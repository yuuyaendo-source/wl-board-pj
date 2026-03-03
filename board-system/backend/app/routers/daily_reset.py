# -*- coding: utf-8 -*-
"""
Logic 3: Daily Reset API。
Personal Board の Today レーン未完了タスクについて「持ち越しますか？」メッセージを返す。
毎朝の Meeting 用: Today を MORNING にコピーする sync_to_morning（cron 等で 10:15 に実行想定）。
"""
import asyncio

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.ai import run_daily_reset_messages

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


@router.post("/run_8am")
async def run_8am(db: AsyncSession = Depends(get_db)):
    """
    毎日 8:00 に実行する処理: (1) Meeting ボードをリセット (2) 全 Google 連携ユーザーの今日の予定を取得し、
    今日の予定欄に保存＆要約を P 付箋として Today レーンに配置。
    cron で 8:00 にこのエンドポイントを 1 回呼ぶ。
    """
    from app.config import settings
    from app.models import UserGoogleToken
    from app.routers.auth_google import _refresh_user_calendar_and_today
    import logging
    log = logging.getLogger(__name__)

    await db.execute(delete(BoardPlacement).where(BoardPlacement.board_type == BoardType.MORNING))
    await db.flush()

    if not settings.google_calendar_client_id or not settings.google_calendar_client_secret:
        log.info("run_8am: Google Calendar 未設定のためカレンダー取得をスキップ")
        return {"ok": True, "refreshed": [], "failed": []}

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
    return {"ok": True, "refreshed": refreshed, "failed": failed}
