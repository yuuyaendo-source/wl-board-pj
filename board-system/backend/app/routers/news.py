# -*- coding: utf-8 -*-
"""
朝会ニュース: 取得（RSS→Ollama要約→MORNING付箋）とクリア（placement_source=news のみ削除）。
"""
import asyncio
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote
from app.models.board_placement import Lane
from app.models.sticky_note import NoteStatus
from app.services.news_fetcher import fetch_and_summarize_news

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])

PLACEMENT_SOURCE_NEWS = "news"


@router.post("/fetch")
async def fetch_news(db: AsyncSession = Depends(get_db)):
    """
    RSS を取得し Ollama で要約して、Meeting（MORNING）ボードに付箋として追加する。
    OLLAMA_URL 未設定時はスキップ。テスト・手動用および 10:15 スケジューラから呼ぶ。
    """
    from app.config import settings

    if not settings.ollama_url:
        return {"ok": True, "skipped": True, "reason": "OLLAMA_URL 未設定", "created": 0}

    def _run() -> str | None:
        return fetch_and_summarize_news()

    try:
        markdown = await asyncio.to_thread(_run)
    except Exception as e:
        logger.error("ニュース取得・要約エラー: %s", e)
        return {"ok": False, "error": str(e)[:200], "created": 0}

    if not markdown:
        return {"ok": True, "skipped": True, "reason": "要約結果が空", "created": 0}

    # 既存の MORNING の最大 sort_order を取得（ニュースを末尾に）
    r = await db.execute(
        select(BoardPlacement.sort_order)
        .where(BoardPlacement.board_type == BoardType.MORNING)
        .order_by(BoardPlacement.sort_order.desc())
        .limit(1)
    )
    next_order = 0
    row = r.scalar_one_or_none()
    if row is not None:
        next_order = row + 1

    note = StickyNote(
        content=markdown,
        author_id=None,
        status=NoteStatus.ACTIVE,
    )
    db.add(note)
    await db.flush()

    placement = BoardPlacement(
        note_id=note.id,
        board_type=BoardType.MORNING,
        owner_id=None,
        lane=Lane.TODAY,
        sort_order=next_order,
        placement_source=PLACEMENT_SOURCE_NEWS,
    )
    db.add(placement)
    await db.commit()
    logger.info("ニュース付箋を MORNING に追加しました note_id=%s", note.id)
    return {"ok": True, "created": 1, "note_id": note.id}


@router.post("/clear")
async def clear_news(db: AsyncSession = Depends(get_db)):
    """
    ニュース付箋のみ削除（MORNING の placement_source=news の配置と対応する付箋を削除）。
    毎日 10:00 のスケジューラおよび手動「クリア」ボタン用。
    """
    result = await db.execute(
        select(BoardPlacement.note_id).where(
            BoardPlacement.board_type == BoardType.MORNING,
            BoardPlacement.placement_source == PLACEMENT_SOURCE_NEWS,
        )
    )
    note_ids = [r[0] for r in result.all()]
    if not note_ids:
        await db.commit()
        return {"ok": True, "deleted": 0}

    await db.execute(
        delete(BoardPlacement).where(
            BoardPlacement.board_type == BoardType.MORNING,
            BoardPlacement.placement_source == PLACEMENT_SOURCE_NEWS,
        )
    )
    await db.execute(delete(StickyNote).where(StickyNote.id.in_(note_ids)))
    await db.commit()
    logger.info("ニュース付箋を削除しました note_ids=%s", note_ids)
    return {"ok": True, "deleted": len(note_ids)}
