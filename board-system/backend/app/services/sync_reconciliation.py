# -*- coding: utf-8 -*-
"""
Self-Healing 同期照合サービス。
board-system (PostgreSQL) と wl-sticky-note (付箋ボード API) の間のデータ差分を照合・修復する。
"""
import logging
from typing import Any
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import BoardPlacement, BoardType, StickyNote
from app.models.sticky_note import NoteStatus

logger = logging.getLogger(__name__)


async def reconcile_sticky_notes(
    db: AsyncSession,
    client: httpx.AsyncClient | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    wl-sticky-note と board-system のデータ整合性をチェック・補正する。

    Source of Truth 規則:
    - 本文・存在有無 (物理存在): wl-sticky-note を優先
    - ステータス・期限日: board-system (PostgreSQL) を優先
    """
    postit_url = settings.postit_board_url.rstrip("/")
    board_id = settings.postit_board_id
    fetch_url = f"{postit_url}/api/boards/{board_id}/notes"

    stats = {
        "dry_run": dry_run,
        "remote_total": 0,
        "db_total": 0,
        "created_in_db": 0,
        "archived_in_remote": 0,
        "errors": [],
    }

    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        close_client = True

    try:
        try:
            resp = await client.get(fetch_url)
            if resp.status_code != 200:
                stats["errors"].append(f"HTTP {resp.status_code} from postit board")
                return stats
            remote_data = resp.json()
            remote_notes = remote_data.get("notes", [])
            stats["remote_total"] = len(remote_notes)
        except Exception as e:
            logger.error("[Reconciliation] Failed to fetch remote notes: %s", e)
            stats["errors"].append(str(e))
            return stats

        stmt = select(StickyNote).where(StickyNote.postit_board_id == board_id)
        result = await db.execute(stmt)
        db_notes = list(result.scalars().all())
        stats["db_total"] = len(db_notes)

        db_note_map = {n.postit_note_id: n for n in db_notes if n.postit_note_id}

        for r_note in remote_notes:
            r_id = str(r_note.get("id"))
            r_text = r_note.get("text", "")
            r_gray = r_note.get("gray", False)

            if r_id not in db_note_map:
                stats["created_in_db"] += 1
                logger.info(
                    "[Reconciliation][DryRun=%s] Missing in DB -> Create: postit_id=%s (gray=%s)",
                    dry_run,
                    r_id,
                    r_gray,
                )
                if not dry_run:
                    status = NoteStatus.DONE if r_gray else NoteStatus.ACTIVE
                    matrix_q = 5 if r_gray else 1
                    new_note = StickyNote(
                        content=r_text or "（テキストなし）",
                        postit_board_id=board_id,
                        postit_note_id=r_id,
                        status=status,
                    )
                    db.add(new_note)
                    await db.flush()
                    placement = BoardPlacement(
                        note_id=new_note.id,
                        board_type=BoardType.TASK,
                        matrix_quadrant=matrix_q,
                        sort_order=0,
                        placement_source="reconciliation",
                    )
                    db.add(placement)
            else:
                db_note = db_note_map[r_id]
                if r_gray and db_note.status == NoteStatus.ACTIVE:
                    logger.info(
                        "[Reconciliation][DryRun=%s] Remote Gray -> DB Status DONE: postit_id=%s",
                        dry_run,
                        r_id,
                    )
                    if not dry_run:
                        db_note.status = NoteStatus.DONE
                        r_placement = await db.execute(
                            select(BoardPlacement).where(
                                BoardPlacement.note_id == db_note.id,
                                BoardPlacement.board_type == BoardType.TASK,
                            )
                        )
                        task_placement = r_placement.scalar_one_or_none()
                        if task_placement:
                            task_placement.matrix_quadrant = 5

        for postit_id, db_note in db_note_map.items():
            if db_note.status in (NoteStatus.DONE, NoteStatus.ARCHIVED):
                r_match = next(
                    (rn for rn in remote_notes if str(rn.get("id")) == postit_id), None
                )
                if r_match and not r_match.get("gray"):
                    stats["archived_in_remote"] += 1
                    logger.info(
                        "[Reconciliation][DryRun=%s] DB Completed/Archived -> Remote Gray: postit_id=%s",
                        dry_run,
                        postit_id,
                    )
                    if not dry_run:
                        patch_url = (
                            f"{postit_url}/api/boards/{board_id}/notes/{postit_id}"
                        )
                        try:
                            await client.patch(patch_url, json={"gray": True})
                        except Exception as e:
                            logger.warning(
                                "[Reconciliation] Failed to patch gray remote note %s: %s",
                                postit_id,
                                e,
                            )

        if not dry_run:
            await db.commit()

        return stats
    finally:
        if close_client:
            await client.aclose()
