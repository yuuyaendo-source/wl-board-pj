# -*- coding: utf-8 -*-
"""
Logic 3: Daily Reset API。
Personal Board の Today レーン未完了タスクについて「持ち越しますか？」メッセージを返す。
毎朝の Meeting 用: Today を MORNING にコピーする sync_to_morning（cron 等で 10:15 に実行想定）。
"""
from datetime import date, datetime as _dt
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.core.time_utils import utc_now_naive, JST
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.services.due_date_rules import should_move_to_today
from app.services.sync_reconciliation import reconcile_sticky_notes

router = APIRouter(prefix="/daily_reset", tags=["daily_reset"])


async def _clear_morning_board(db: AsyncSession, exclude_news: bool = False) -> None:
    """Meeting ボード（MORNING 型配置）の内容を削除する共通ヘルパー。"""
    if not exclude_news:
        # 完全リセット時は孤立蓄積を防ぐため、ニュース付箋本体 (StickyNote) も合わせて削除
        r_news = await db.execute(
            select(BoardPlacement.note_id).where(
                BoardPlacement.board_type == BoardType.MORNING,
                BoardPlacement.placement_source == "news",
            )
        )
        news_note_ids = [r[0] for r in r_news.all()]
        if news_note_ids:
            await db.execute(delete(StickyNote).where(StickyNote.id.in_(news_note_ids)))

    stmt = delete(BoardPlacement).where(BoardPlacement.board_type == BoardType.MORNING)
    if exclude_news:
        # ニュース付箋配置を保護し、通常付箋の配置のみを削除対象とする
        stmt = stmt.where(
            or_(
                BoardPlacement.placement_source.is_(None),
                BoardPlacement.placement_source != "news",
            )
        )
    await db.execute(stmt)
    await db.flush()


@router.post("/sync_to_morning")
async def sync_to_morning(db: AsyncSession = Depends(get_db)):
    """
    全ユーザーの Personal Today を MORNING にコピーする（ニュース付箋以外の既存 MORNING 配置を削除）。
    毎朝 10:15 にスケジューラから直列パイプライン経由で呼ばれる。
    """
    # 既存の MORNING 配置を削除（ニュース付箋は除外して保護）
    await _clear_morning_board(db, exclude_news=True)

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
    Meeting ボード（MORNING）の内容を全削除する。手動リセットボタン用。
    """
    await _clear_morning_board(db, exclude_news=False)
    return {"ok": True}


async def apply_due_date_rules(db: AsyncSession) -> dict:
    """
    期限（due_date）の設定されたパーソナル配置に対して、期限までの日数に応じて Today または INBOX に自動移動する。
    - DONE および HELP_REQUEST（応援要請）レーンの配置は除外。
    - is_manually_moved_to_today == True の配置はスキップ（手動移動が優先）。
    - 日本時間（JST）を基準として判定する。
    戻り値: {"today_count": int, "inbox_count": int} 各レーンへ移動した件数。
    """
    today_jst = _dt.now(JST).date()

    # DONE および HELP_REQUEST 以外の PERSONAL 配置で、期限が設定されているものを取得
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.lane.notin_([Lane.DONE, Lane.HELP_REQUEST]),
            StickyNote.due_date.isnot(None),
        )
    )
    rows = result.all()

    today_count = 0
    inbox_count = 0
    for p, n in rows:
        if p.is_manually_moved_to_today:
            continue

        target_lane = (
            Lane.TODAY if should_move_to_today(n.due_date, today_jst) else Lane.INBOX
        )

        if p.lane != target_lane:
            p.lane = target_lane
            if target_lane == Lane.TODAY:
                today_count += 1
            else:
                inbox_count += 1

    await db.flush()
    return {"today_count": today_count, "inbox_count": inbox_count}


def _rotate_placement_items(
    items: list[tuple[BoardPlacement, StickyNote]],
    today_jst: date,
    threshold: int,
    rotate_count: int,
) -> int:
    """
    非除外タスク（期限10日以内を除く）を抽出し、先頭 rotate_count 件を末尾に回して
    sort_order を連番で再採番する共通ヘルパー関数。
    """
    rotatable_indices: list[int] = []
    rotatable_items: list[tuple[BoardPlacement, StickyNote]] = []

    for idx, (p, n) in enumerate(items):
        if n.due_date is not None and (n.due_date - today_jst).days <= 10:
            continue
        rotatable_indices.append(idx)
        rotatable_items.append((p, n))

    if len(rotatable_items) >= threshold:
        rotated_slice = rotatable_items[:rotate_count]
        remaining_slice = rotatable_items[rotate_count:]
        new_rotatable = remaining_slice + rotated_slice

        new_ordered = list(items)
        for orig_idx, item in zip(rotatable_indices, new_rotatable):
            new_ordered[orig_idx] = item

        for idx, (p, _) in enumerate(new_ordered):
            p.sort_order = idx
        return rotate_count

    return 0


async def rotate_stale_tasks(db: AsyncSession, force: bool = False) -> dict:
    """
    タスクレーンに長期間滞留しているタスクを1日おき（2日に1回）に循環させる。
    - 期限が今日から10日以内のタスク（優先度高）は元のインデックス位置をキープ（除外）。
    - Task Board: 完了以外の各列で、対象タスクが11件以上ある場合、先頭10件を末尾へ移動。
    - Personal Board: 各ユーザーの INBOX で、対象タスクが4件以上ある場合、先頭3件を末尾へ移動。
    - 元の並び順位置を保持したまま循環対象のみをスライドさせ、sort_order を連番で再採番（正規化）。
    """
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
        .order_by(
            BoardPlacement.matrix_quadrant, BoardPlacement.sort_order, BoardPlacement.id
        )
    )
    task_rows = task_res.all()

    task_by_q: dict[int, list[tuple[BoardPlacement, StickyNote]]] = {}
    for p, n in task_rows:
        q = p.matrix_quadrant or 1
        task_by_q.setdefault(q, []).append((p, n))

    for q, items in task_by_q.items():
        task_rotated_count += _rotate_placement_items(
            items, today_jst, threshold=11, rotate_count=10
        )

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

    personal_by_owner: dict[int, list[tuple[BoardPlacement, StickyNote]]] = {}
    for p, n in personal_rows:
        if p.owner_id is not None:
            personal_by_owner.setdefault(p.owner_id, []).append((p, n))

    for owner_id, items in personal_by_owner.items():
        personal_rotated_count += _rotate_placement_items(
            items, today_jst, threshold=4, rotate_count=3
        )

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


@router.post("/reconcile")
async def trigger_reconciliation(
    request: Request,
    dry_run: bool = Query(
        True, description="True の場合はログ出力のみを行い書き込みを行わない"
    ),
    db: AsyncSession = Depends(get_db),
):
    """手動で付箋データと DB の差分照合・Self-Healing バッチを実行する。"""
    client = getattr(request.app.state, "http_client", None)
    res = await reconcile_sticky_notes(db, client=client, dry_run=dry_run)
    return {"ok": True, "result": res}


@router.post("/run_8am")
async def run_8am(request: Request, db: AsyncSession = Depends(get_db)):
    """
    毎日 8:00 に実行する処理: (1) Meeting ボードをリセット (2) 期限タスクの自動移動
    (3) 停滞タスクの自動ローテーション (4) 付箋データと DB の差分照合 (5) 全 Google 連携ユーザーの今日の予定を取得し、今日の予定欄に保存＆要約を P 付箋として Today レーンに配置。
    cron で 8:00 にこのエンドポイントを 1 回呼ぶ。
    """
    from app.config import settings
    from app.models import OAuthPkceState, UserGoogleToken
    from app.routers.auth_google import _refresh_user_calendar_and_today
    import logging

    log = logging.getLogger(__name__)

    # 期限切れの OAuth PKCE state をクリーンアップ
    await db.execute(
        delete(OAuthPkceState).where(OAuthPkceState.expires_at < utc_now_naive())
    )

    # 8:00 のリセットは前日のニュースも含め完全クリア（StickyNote 本体も削除）
    await _clear_morning_board(db, exclude_news=False)

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

    # 付箋データと DB の差分照合・自動補正バッチ
    client = getattr(request.app.state, "http_client", None)
    reconcile_result = await reconcile_sticky_notes(
        db, client=client, dry_run=settings.reconciliation_dry_run
    )
    log.info(
        "run_8am: 差分照合実行結果 (dry_run=%s): %s",
        settings.reconciliation_dry_run,
        reconcile_result,
    )

    # 前半のバッチ更新を確定コミット
    await db.commit()

    if (
        not settings.google_calendar_client_id
        or not settings.google_calendar_client_secret
    ):
        log.info("run_8am: Google Calendar 未設定のためカレンダー取得をスキップ")
        return {
            "ok": True,
            "refreshed": [],
            "failed": [],
            "due_date_moved": due_date_result,
            "task_rotation": rotation_result,
            "reconciliation": reconcile_result,
        }

    result = await db.execute(select(UserGoogleToken.user_id).distinct())
    user_ids = [r[0] for r in result.all()]
    refreshed = []
    failed = []
    for uid in user_ids:
        try:
            # ③ 各ユーザー単位でセーブポイント（begin_nested）を作成し、1人の失敗がセッション全体を破綻させないように隔離
            async with db.begin_nested():
                await _refresh_user_calendar_and_today(uid, db)
                refreshed.append(uid)
            await db.commit()
        except Exception as e:
            log.warning("run_8am user_id=%s: %s", uid, e)
            failed.append(uid)

    return {
        "ok": True,
        "refreshed": refreshed,
        "failed": failed,
        "due_date_moved": due_date_result,
        "task_rotation": rotation_result,
        "reconciliation": reconcile_result,
    }
