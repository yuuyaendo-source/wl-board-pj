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
    GEMINI_API_KEY 未設定時は簡易メッセージを返す。
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
