# -*- coding: utf-8 -*-
"""
Self-Healing 同期照合サービス。
board-system (PostgreSQL) と wl-sticky-note (付箋ボード API) の間のデータ差分を照合・修復する。
"""
from __future__ import annotations

import logging
from datetime import date as DateType
from typing import Any

import httpx
from sqlalchemy import select, update as sa_update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import BoardPlacement, BoardType, StickyNote
from app.models.board_placement import Lane
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

    stats: dict[str, Any] = {
        "dry_run": dry_run,
        "remote_total": 0,
        "db_total": 0,
        "created_in_db": 0,
        "archived_in_remote": 0,
        "updated_in_db": 0,
        "errors": [],
    }

    close_client = False
    if client is None:
        client = httpx.AsyncClient(
            timeout=15.0, headers={"x-internal-secret": settings.internal_api_secret}
        )
        close_client = True

    try:
        try:
            resp = await client.get(fetch_url)
            if resp.status_code != 200:
                err_msg = (
                    f"HTTP {resp.status_code} from postit board (URL: {fetch_url})"
                )
                logger.error("[Reconciliation] %s", err_msg)
                stats["errors"].append(err_msg)
                return stats
            remote_data = resp.json()
            remote_notes = remote_data.get("notes", [])
            stats["remote_total"] = len(remote_notes)
        except httpx.RequestError as exc:
            err_msg = f"Network error during fetch from postit board: {exc}"
            logger.error("[Reconciliation] %s", err_msg)
            stats["errors"].append(err_msg)
            return stats
        except Exception as e:
            logger.error("[Reconciliation] Failed to parse remote notes: %s", e)
            stats["errors"].append(str(e))
            return stats

        try:
            stmt = select(StickyNote).where(StickyNote.postit_board_id == board_id)
            result = await db.execute(stmt)
            db_notes = list(result.scalars().all())
            stats["db_total"] = len(db_notes)
        except SQLAlchemyError as db_exc:
            err_msg = f"Database read error: {db_exc}"
            logger.error("[Reconciliation] %s", err_msg)
            stats["errors"].append(err_msg)
            return stats

        db_note_map = {n.postit_note_id: n for n in db_notes if n.postit_note_id}

        # 1. リモート付箋をスキャンして DB を補正
        for r_note in remote_notes:
            r_id = str(r_note.get("id") or "").strip()
            if not r_id:
                continue

            r_text = (r_note.get("text") or "").strip()
            r_gray = bool(r_note.get("gray", False))
            r_is_personal = bool(
                r_note.get("is_personal_only") or r_note.get("isPersonalOnly", False)
            )

            # パーソナル専用付箋は全体タスクボードへ公開しない
            if r_is_personal:
                continue

            parsed_due = None
            if r_note.get("dueDate"):
                try:
                    parsed_due = DateType.fromisoformat(str(r_note.get("dueDate"))[:10])
                except (ValueError, TypeError):
                    parsed_due = None

            if r_id not in db_note_map:
                # ゾンビ復活防止: 既にグレー化されている付箋は新規作成しない
                if r_gray:
                    continue

                stats["created_in_db"] += 1
                logger.info(
                    "[Reconciliation][DryRun=%s] Missing in DB -> Create: postit_id=%s (gray=%s)",
                    dry_run,
                    r_id,
                    r_gray,
                )
                if not dry_run:
                    try:
                        new_note = StickyNote(
                            content=r_text or "（テキストなし）",
                            postit_board_id=board_id,
                            postit_note_id=r_id,
                            status=NoteStatus.ACTIVE,
                            due_date=parsed_due,
                            is_personal_only=False,
                        )
                        db.add(new_note)
                        await db.flush()
                        placement = BoardPlacement(
                            note_id=new_note.id,
                            board_type=BoardType.TASK,
                            matrix_quadrant=1,
                            sort_order=0,
                            placement_source="reconciliation",
                        )
                        db.add(placement)
                    except SQLAlchemyError as create_err:
                        logger.error(
                            "[Reconciliation] Failed to create note %s: %s",
                            r_id,
                            create_err,
                        )
                        stats["errors"].append(f"Create error for {r_id}: {create_err}")
            else:
                db_note = db_note_map[r_id]
                if db_note.is_personal_only:
                    continue

                # 本文同期 (Source of Truth: 付箋ボード)
                if r_text and db_note.content != r_text:
                    stats["updated_in_db"] += 1
                    logger.info(
                        "[Reconciliation][DryRun=%s] Text mismatch -> Sync to DB: postit_id=%s",
                        dry_run,
                        r_id,
                    )
                    if not dry_run:
                        db_note.content = r_text

                # 期限日同期
                if parsed_due is not None and db_note.due_date != parsed_due:
                    stats["updated_in_db"] += 1
                    logger.info(
                        "[Reconciliation][DryRun=%s] Due date mismatch -> Sync to DB: postit_id=%s",
                        dry_run,
                        r_id,
                    )
                    if not dry_run:
                        db_note.due_date = parsed_due

                # グレー化同期
                if r_gray and db_note.status == NoteStatus.ACTIVE:
                    logger.info(
                        "[Reconciliation][DryRun=%s] Remote Gray -> DB Status DONE: postit_id=%s",
                        dry_run,
                        r_id,
                    )
                    if not dry_run:
                        db_note.status = NoteStatus.DONE
                        try:
                            r_placement = await db.execute(
                                select(BoardPlacement).where(
                                    BoardPlacement.note_id == db_note.id,
                                    BoardPlacement.board_type == BoardType.TASK,
                                )
                            )
                            task_placement = r_placement.scalar_one_or_none()
                            if task_placement:
                                task_placement.matrix_quadrant = 5

                            await db.execute(
                                sa_update(BoardPlacement)
                                .where(
                                    BoardPlacement.note_id == db_note.id,
                                    BoardPlacement.board_type == BoardType.PERSONAL,
                                )
                                .values(lane=Lane.DONE)
                            )
                        except SQLAlchemyError as status_err:
                            logger.error(
                                "[Reconciliation] Failed to update status for %s: %s",
                                r_id,
                                status_err,
                            )
                            stats["errors"].append(
                                f"Status update error for {r_id}: {status_err}"
                            )

        # 2. DB 側で完了した付箋をリモート側へ逆同期 (グレー化)
        for postit_id, db_note in db_note_map.items():
            if db_note.is_personal_only:
                continue

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
                            patch_resp = await client.patch(
                                patch_url, json={"gray": True}
                            )
                            if patch_resp.status_code >= 400:
                                logger.warning(
                                    "[Reconciliation] Remote patch failed with HTTP %s for %s",
                                    patch_resp.status_code,
                                    postit_id,
                                )
                        except Exception as e:
                            logger.warning(
                                "[Reconciliation] Failed to patch gray remote note %s: %s",
                                postit_id,
                                e,
                            )
                            stats["errors"].append(
                                f"Remote patch error for {postit_id}: {e}"
                            )

        if not dry_run:
            try:
                await db.flush()
            except SQLAlchemyError as flush_err:
                logger.error("[Reconciliation] DB flush failed: %s", flush_err)
                stats["errors"].append(f"Flush error: {flush_err}")

        return stats
    finally:
        if close_client:
            await client.aclose()
