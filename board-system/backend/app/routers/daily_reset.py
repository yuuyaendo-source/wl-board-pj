# -*- coding: utf-8 -*-
"""
Logic 3: Daily Reset API。
Personal Board の Today レーン未完了タスクについて「持ち越しますか？」メッセージを返す。
毎朝の Meeting 用: Today を MORNING にコピーする sync_to_morning（cron 等で 10:15 に実行想定）。
"""
import asyncio
from datetime import date
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.ai import run_daily_reset_messages

JST = ZoneInfo("Asia/Tokyo")
router = APIRouter(prefix="/daily_reset", tags=["daily_reset"])


@router.get("/messages")
async def get_daily_reset_messages(
    owner_id: int = Query(..., description="Personal の所有者"),
    db: AsyncSession = Depends(get_db),
):
    """
    指定ユーザーの Personal Board の Today レーンにある付箋について、
    「昨日の『〇〇』は持ち越しますか？」形式の問いかけを LLM で生成して返す。
    OLLAMA_URL 未設定時は簡易メッセージを返す。
    """
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == owner_id,
            BoardPlacement.lane == Lane.TODAY,
        )
        .order_by(BoardPlacement.sort_order, BoardPlacement.id)
    )
    rows = result.all()
    items = [{"note_id": p.note_id, "content": n.content} for p, n in rows]
    messages = await asyncio.to_thread(run_daily_reset_messages, items)
    return {"owner_id": owner_id, "messages": messages}


@router.post("/sync_to_morning")
async def sync_to_morning(db: AsyncSession = Depends(get_db)):
    """
    全ユーザーの Personal Today を MORNING にコピーする（既存の MORNING は削除）。
    毎朝 10:15 に cron や systemd タイマーで呼ぶ想定。テスト時は手動で呼べる。
    """
    # 既存の MORNING 配置を全削除
    await db.execute(delete(BoardPlacement).where(BoardPlacement.board_type == BoardType.MORNING))
    await db.flush()

    # 全ユーザー取得
    users_result = await db.execute(select(User).order_by(User.id))
    users = list(users_result.scalars().all())
    created = 0

    for user in users:
        result = await db.execute(
            select(BoardPlacement, StickyNote)
            .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
            .where(
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.owner_id == user.id,
                BoardPlacement.lane == Lane.TODAY,
            )
            .order_by(BoardPlacement.sort_order, BoardPlacement.id)
        )
        rows = result.all()
        for sort_order, (p, _) in enumerate(rows):
            placement = BoardPlacement(
                note_id=p.note_id,
                board_type=BoardType.MORNING,
                owner_id=user.id,
                lane=Lane.TODAY,
                sort_order=sort_order,
            )
            db.add(placement)
            created += 1

    await db.flush()
    return {"ok": True, "created": created}


@router.post("/reset_meeting")
async def reset_meeting(db: AsyncSession = Depends(get_db)):
    """
    Meeting ボード（MORNING）の内容を全削除する。
    毎日 8:00 の cron 用および手動リセットボタン用。
    """
    result = await db.execute(delete(BoardPlacement).where(BoardPlacement.board_type == BoardType.MORNING))
    await db.flush()
    return {"ok": True}


async def apply_due_date_rules(db: AsyncSession) -> dict:
    """
    期限（due_date）の設定されたパーソナル配置に対して、期限までの日数に応じて Today または INBOX に自動移動する。
    - DONE レーンの配置は除外（完了済みタスクは自動移動しない）。
    - is_manually_moved_to_today == True の配置はスキップ（手動移動が優先）。
    - 日本時間（JST）を基準として判定する。
    戻り値: {"today_count": int, "inbox_count": int} 各レーンへ移動した件数。
    """
    today_jst = date.today()  # サーバーが JST の場合はこれで OK
    # Dockerで TZ=Asia/Tokyo が設定されている前提。さらに確実にする場合は datetime.now(JST).date() を使う。
    from datetime import datetime as _dt
    today_jst = _dt.now(JST).date()

    # DONE 以外の PERSONAL 配置で、期限が設定されているものを取得
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.lane != Lane.DONE,
            StickyNote.due_date.isnot(None),
        )
    )
    rows = result.all()

    today_count = 0
    inbox_count = 0
    for p, n in rows:
        # 手動移動フラグが立っている場合は自動移動をスキップ
        if p.is_manually_moved_to_today:
            continue

        days = (n.due_date - today_jst).days
        target_lane: Lane

        if days < 0:
            # 期限切れ: 毎日 Today
            target_lane = Lane.TODAY
        elif days < 30:
            # 短期ルール: 1ヶ月未満
            if days in (0, 1, 2, 3, 4, 5, 10, 20):
                target_lane = Lane.TODAY
            else:
                target_lane = Lane.INBOX
        else:
            # 長期ルール: 1ヶ月以上
            if days % 30 == 0:
                target_lane = Lane.TODAY
            else:
                target_lane = Lane.INBOX

        if p.lane != target_lane:
            p.lane = target_lane
            if target_lane == Lane.TODAY:
                today_count += 1
            else:
                inbox_count += 1

    await db.flush()
    return {"today_count": today_count, "inbox_count": inbox_count}


async def rotate_stale_tasks(db: AsyncSession, force: bool = False) -> dict:
    """
    タスクレーンに長期間滞留しているタスクを1日おき（2日に1回）に循環させる。
    - 期限が今日から10日以内のタスク（優先度高）は先頭位置をキープ（除外）。
    - Task Board: 完了以外の各列で、対象タスクが11件以上ある場合、先頭10件を末尾へ移動。
    - Personal Board: 各ユーザーの INBOX で、対象タスクが4件以上ある場合、先頭3件を末尾へ移動。
    - リスト全体の sort_order を 0 から連番で再採番（正規化）。
    """
    from datetime import datetime as _dt
    today_jst = _dt.now(JST).date()

    if not force and today_jst.toordinal() % 2 != 0:
        return {"skipped": True, "reason": "Not a rotation day (runs every 2 days)"}

    task_rotated_count = 0
    personal_rotated_count = 0

    # 1. Task Board のローテーション（完了 quadrant=5 以外）
    task_res = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.board_type == BoardType.TASK,
            BoardPlacement.matrix_quadrant.isnot(None),
            BoardPlacement.matrix_quadrant != 5,
        )
        .order_by(BoardPlacement.matrix_quadrant, BoardPlacement.sort_order, BoardPlacement.id)
    )
    task_rows = task_res.all()

    # 象限（列）ごとにグループ化
    task_by_q: dict[int, list[tuple[BoardPlacement, StickyNote]]] = {}
    for p, n in task_rows:
        q = p.matrix_quadrant or 1
        task_by_q.setdefault(q, []).append((p, n))

    for q, items in task_by_q.items():
        keep_top: list[tuple[BoardPlacement, StickyNote]] = []
        rotatable: list[tuple[BoardPlacement, StickyNote]] = []

        for p, n in items:
            if n.due_date is not None and (n.due_date - today_jst).days <= 10:
                keep_top.append((p, n))
            else:
                rotatable.append((p, n))

        # 11件以上ある場合のみ先頭10件を末尾へ
        if len(rotatable) >= 11:
            rotate_count = 10
            rotated_slice = rotatable[:rotate_count]
            remaining_slice = rotatable[rotate_count:]
            new_ordered = keep_top + remaining_slice + rotated_slice
            for idx, (p, _) in enumerate(new_ordered):
                p.sort_order = idx
            task_rotated_count += rotate_count

    # 2. Personal Board のローテーション（各ユーザーの INBOX レーン）
    personal_res = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.lane == Lane.INBOX,
        )
        .order_by(BoardPlacement.owner_id, BoardPlacement.sort_order, BoardPlacement.id)
    )
    personal_rows = personal_res.all()

    # ユーザーごとにグループ化
    personal_by_owner: dict[int, list[tuple[BoardPlacement, StickyNote]]] = {}
    for p, n in personal_rows:
        if p.owner_id is not None:
            personal_by_owner.setdefault(p.owner_id, []).append((p, n))

    for owner_id, items in personal_by_owner.items():
        keep_top: list[tuple[BoardPlacement, StickyNote]] = []
        rotatable: list[tuple[BoardPlacement, StickyNote]] = []

        for p, n in items:
            if n.due_date is not None and (n.due_date - today_jst).days <= 10:
                keep_top.append((p, n))
            else:
                rotatable.append((p, n))

        # 4件以上ある場合のみ先頭3件を末尾へ
        if len(rotatable) >= 4:
            rotate_count = 3
            rotated_slice = rotatable[:rotate_count]
            remaining_slice = rotatable[rotate_count:]
            new_ordered = keep_top + remaining_slice + rotated_slice
            for idx, (p, _) in enumerate(new_ordered):
                p.sort_order = idx
            personal_rotated_count += rotate_count

    await db.flush()
    return {
        "skipped": False,
        "task_rotated_count": task_rotated_count,
        "personal_rotated_count": personal_rotated_count,
    }


@router.post("/rotate_tasks")
async def manual_rotate_tasks(
    force: bool = Query(True, description="2日に1回の判定を無視して強制実行するか"),
    db: AsyncSession = Depends(get_db),
):
    """タスクローテーション（停滞タスクの自動並び替え）を手動実行するエンドポイント。"""
    result = await rotate_stale_tasks(db, force=force)
    return {"ok": True, "result": result}


@router.post("/run_8am")
async def run_8am(db: AsyncSession = Depends(get_db)):
    """
    毎日 8:00 に実行する処理: (1) Meeting ボードをリセット (2) 期限タスクの自動移動
    (3) 停滞タスクの自動ローテーション (4) 全 Google 連携ユーザーの今日の予定を取得し、今日の予定欄に保存＆要約を P 付箋として Today レーンに配置。
    cron で 8:00 にこのエンドポイントを 1 回呼ぶ。
    """
    from app.config import settings
    from app.models import UserGoogleToken
    from app.routers.auth_google import _refresh_user_calendar_and_today
    import logging
    log = logging.getLogger(__name__)

    await db.execute(delete(BoardPlacement).where(BoardPlacement.board_type == BoardType.MORNING))
    await db.flush()

    # 期限タスクの自動移動
    due_date_result = await apply_due_date_rules(db)
    log.info(
        "run_8am: 期限タスク自動移動 today=%s inbox=%s",
        due_date_result["today_count"],
        due_date_result["inbox_count"],
    )

    # 停滞タスクの自動ローテーション（期限間近のタスクが Today に移動した後に実行）
    rotation_result = await rotate_stale_tasks(db)
    log.info("run_8am: タスクローテーション実行結果: %s", rotation_result)

    if not settings.google_calendar_client_id or not settings.google_calendar_client_secret:
        log.info("run_8am: Google Calendar 未設定のためカレンダー取得をスキップ")
        return {
            "ok": True,
            "refreshed": [],
            "failed": [],
            "due_date_moved": due_date_result,
            "task_rotation": rotation_result,
        }

    result = await db.execute(select(UserGoogleToken.user_id).distinct())
    user_ids = [r[0] for r in result.all()]
    refreshed = []
    failed = []
    for uid in user_ids:
        try:
            await _refresh_user_calendar_and_today(uid, db)
            refreshed.append(uid)
        except Exception as e:
            log.warning("run_8am user_id=%s: %s", uid, e)
            failed.append(uid)
    return {
        "ok": True,
        "refreshed": refreshed,
        "failed": failed,
        "due_date_moved": due_date_result,
        "task_rotation": rotation_result,
    }

