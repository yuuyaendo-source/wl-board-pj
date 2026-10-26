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
from app.services.llm_settings import (
    get_resolved_ollama_async,
    ollama_configured_async,
)
from app.services.news_fetcher import fetch_and_summarize_news

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])

PLACEMENT_SOURCE_NEWS = "news"


async def _clear_existing_news_internal(db: AsyncSession) -> int:
    """既存のニュース付箋と配置をクリーンアップする内部ヘルパー。"""
    result = await db.execute(
        select(BoardPlacement.note_id).where(
            BoardPlacement.board_type == BoardType.MORNING,
            BoardPlacement.placement_source == PLACEMENT_SOURCE_NEWS,
        )
    )
    note_ids = [r[0] for r in result.all()]
    if not note_ids:
        return 0

    await db.execute(
        delete(BoardPlacement).where(
            BoardPlacement.board_type == BoardType.MORNING,
            BoardPlacement.placement_source == PLACEMENT_SOURCE_NEWS,
        )
    )
    await db.execute(delete(StickyNote).where(StickyNote.id.in_(note_ids)))
    await db.flush()
    return len(note_ids)


@router.post("/fetch")
async def fetch_news(db: AsyncSession = Depends(get_db)):
    """
    RSS を取得し Ollama で要約して、Meeting（MORNING）ボードに付箋として追加する。
    OLLAMA_URL 未設定時はスキップ。10:15 スケジューラから sync_to_morning 完了後に呼ばれる。
    """
    if not await ollama_configured_async(db):
        return {
            "ok": True,
            "skipped": True,
            "reason": "OLLAMA_URL 未設定",
            "created": 0,
        }

    url, model_ov = await get_resolved_ollama_async(db)

    def _run() -> str | None:
        return fetch_and_summarize_news(ollama_url=url, model_override=model_ov)

    try:
        markdown = await asyncio.to_thread(_run)
    except Exception as e:
        logger.error("ニュース取得・要約エラー: %s", e)
        return {"ok": False, "error": str(e)[:200], "created": 0}

    if not markdown:
        return {"ok": True, "skipped": True, "reason": "要約結果が空", "created": 0}

    # 既に今日のニュース付箋が存在する場合は重複を避けるため事前にクリーンアップ
    await _clear_existing_news_internal(db)

    # 既存の MORNING の最大 sort_order を取得（ニュースを末尾に配置）
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
    await db.flush()
    logger.info("ニュース付箋を MORNING に追加しました note_id=%s", note.id)
    return {"ok": True, "created": 1, "note_id": note.id}


@router.post("/clear")
async def clear_news(db: AsyncSession = Depends(get_db)):
    """
    ニュース付箋のみ削除（MORNING の placement_source=news の配置と対応する付箋を削除）。
    毎日 10:00 のスケジューラおよび手動「クリア」ボタン用。
    """
    deleted_count = await _clear_existing_news_internal(db)
    logger.info("ニュース付箋を削除しました deleted=%s", deleted_count)
    return {"ok": True, "deleted": deleted_count}
