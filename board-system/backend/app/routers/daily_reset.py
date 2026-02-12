# -*- coding: utf-8 -*-
"""
Logic 3: Daily Reset API。
Personal Board の Today レーン未完了タスクについて「持ち越しますか？」メッセージを返す。
"""
import asyncio

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote
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
