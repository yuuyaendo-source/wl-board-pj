# -*- coding: utf-8 -*-
"""
AIによる自動振り分けオーケストレーター。
新規付箋の内容を Triage → Matrix Scoring し、Task ボードの適切な列へ配置、担当者があれば Personal にも配布する。
Board System でタスクになった付箋（postit 連携なし）は付箋ボードにも反映する。
MOCK_AI=true の場合は外部 LLM 呼び出しを行わずに確定スコアで配置する。
"""
import asyncio
import logging
import os
import time
from types import SimpleNamespace

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import run_matrix_scoring, run_triage
from app.db import async_session_maker
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.services.llm_settings import get_resolved_ollama_async

logger = logging.getLogger("uvicorn")


async def process_new_note_ai_background(app, note_id: int) -> None:
    """HTTP response 後に専用 DB セッションで AI 振り分けを実行する。"""
    request = SimpleNamespace(app=app)
    async with async_session_maker() as db:
        try:
            await process_new_note_ai(request, note_id, db)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("[Linko AI] Background processing failed for note %s", note_id)

# アイゼンハワー象限(1-4) → Taskボード列(1=アイデア, 2=短期, 3=長期, 4=重要)
EISENHOWER_TO_COLUMN = {1: 4, 2: 3, 3: 2, 4: 1}


def _normalize_assignee_name(name: str) -> str:
    """敬称を除去してマッチしやすくする。"""
    if not name or not name.strip():
        return ""
    s = name.strip()
    for suffix in ("さん", "君", "様", "先生", "ちゃん"):
        if s.endswith(suffix):
            s = s[: -len(suffix)].strip()
            break
    return s


async def _resolve_assignee_user_async(
    assignee_name: str, db: AsyncSession
) -> User | None:
    """担当者名から User オブジェクトを非同期取得。完全一致を優先し、なければ部分一致。"""
    raw = (assignee_name or "").strip()
    normalized = _normalize_assignee_name(raw) if raw else ""
    if not raw and not normalized:
        return None

    # 完全一致を優先
    for candidate in (normalized, raw):
        if not candidate:
            continue
        result = await db.execute(select(User).where(User.name == candidate).limit(1))
        user = result.scalar_one_or_none()
        if user:
            return user

    # 部分一致
    for candidate in (normalized, raw):
        if not candidate:
            continue
        result = await db.execute(
            select(User).where(User.name.contains(candidate)).limit(1)
        )
        user = result.scalar_one_or_none()
        if user:
            return user

    return None


async def process_new_note_ai(request: Request, note_id: int, db: AsyncSession) -> None:
    """
    新規付箋に対する AI 振り分け（バックグラウンド的処理）。
    """
    logger.info("[Linko AI] Processing Note ID: %s...", note_id)

    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        logger.error("[Linko AI] Note %s not found.", note_id)
        return

    content = note.content or ""
    content_preview = (
        (content[:300] + "…") if len(content) > 300 else (content or "(空)")
    )
    logger.info("[Linko AI] Note %s 内容: %s", note_id, content_preview)

    # E2E テスト環境用 モック判定 (MOCK_AI=true)
    if os.environ.get("MOCK_AI", "").lower() in ("true", "1"):
        logger.info("[Linko AI] MOCK_AI 提案適用 Note ID: %s", note_id)
        await _place_on_task_board(db, note_id, 80.0, 80.0, 4)  # 重要列へマッピング
        await db.flush()
        if not note.postit_note_id:
            from app.config import settings

            ok = await _sync_note_to_postit_async(
                request,
                note.id,
                note.content or "",
                settings.postit_board_id,
            )
            if ok:
                note.postit_board_id = settings.postit_board_id
                note.postit_note_id = f"bs-{note.id}"
                await db.flush()
        return

    ollama_url, model_ov = await get_resolved_ollama_async(db)

    # --- 1. Triage ---
    try:
        triage_result = await asyncio.to_thread(
            run_triage, content, ollama_url, model_ov
        )
    except Exception as e:
        logger.warning("[Linko AI] Triage failed: %s", e)
        triage_result = None

    if not triage_result:
        logger.warning(
            "[Linko AI] Triage 未実行（APIキー未設定または失敗）。振り分け結果: アイデア列に配置。"
        )
        await _place_on_task_board(db, note_id, 50.0, 50.0, 1)
        await db.flush()
        logger.info(
            "[Linko AI] Note %s 振り分け完了: アイデア列（Triage 未実行のためデフォルト）",
            note_id,
        )
        if not note.postit_note_id:
            from app.config import settings

            ok = await _sync_note_to_postit_async(
                request,
                note.id,
                note.content or "",
                settings.postit_board_id,
            )
            if ok:
                note.postit_board_id = settings.postit_board_id
                note.postit_note_id = f"bs-{note.id}"
                await db.flush()
                logger.info("[Linko AI] Note %s を付箋ボードに反映しました", note.id)
        return

    if not triage_result.get("is_task"):
        reason = triage_result.get("reason") or ""
        logger.info(
            "[Linko AI] Note %s タスクでないと判定 → アイデア列に配置｜%s",
            note_id,
            reason,
        )
        await _place_on_task_board(db, note_id, 50.0, 50.0, 1)
        await db.flush()

    triage_reason = triage_result.get("reason") or ""
    if triage_reason and triage_result.get("is_task"):
        logger.info("[Linko AI] Note %s Triage 理由: %s", note_id, triage_reason)

    # --- 2. Matrix Scoring ---
    urgency, importance, column = 50.0, 50.0, 1
    column_name = "アイデア"
    if triage_result.get("is_task"):
        try:
            matrix_result = await asyncio.to_thread(
                run_matrix_scoring, content, ollama_url, model_ov
            )
        except Exception as e:
            logger.warning("[Linko AI] Matrix scoring failed: %s", e)
            matrix_result = None
        if matrix_result:
            urgency = float(matrix_result.get("urgency", 50))
            importance = float(matrix_result.get("importance", 50))
            quadrant_eisenhower = matrix_result.get("matrix_quadrant", 4)
            column = EISENHOWER_TO_COLUMN.get(quadrant_eisenhower, 1)
        COLUMN_NAMES = {1: "アイデア", 2: "短期タスク", 3: "長期タスク", 4: "重要"}
        column_name = COLUMN_NAMES.get(column, "アイデア")
        matrix_reason = (matrix_result or {}).get("reason") or ""
        logger.info(
            "[Linko AI] Note %s 採点: U=%s, I=%s → 列「%s」｜%s",
            note_id,
            urgency,
            importance,
            column_name,
            matrix_reason,
        )
        await _place_on_task_board(db, note_id, urgency, importance, column)
        await db.flush()
        logger.info(
            "[Linko AI] Note %s 振り分け完了: Task の「%s」列に配置",
            note_id,
            column_name,
        )

    # --- 3. Personal へ配布 ---
    assignee_name = triage_result.get("assignee_name")
    if assignee_name and isinstance(assignee_name, str):
        assignee_name = assignee_name.strip()
    if assignee_name:
        try:
            user = await _resolve_assignee_user_async(assignee_name, db)
        except Exception as e:
            logger.warning("[Linko AI] Assignee resolve failed: %s", e)
            user = None

        if user:
            logger.info("[Linko AI] Assigning to user: %s", user.name)
            personal = BoardPlacement(
                note_id=note_id,
                board_type=BoardType.PERSONAL,
                owner_id=user.id,
                lane=Lane.INBOX,
                sort_order=0,
            )
            db.add(personal)
            await db.flush()
            logger.info(
                "[Linko AI] Note %s 振り分け完了: Task + Personal（%s）に配布",
                note_id,
                user.name,
            )
        else:
            logger.warning("[Linko AI] Assignee '%s' not found in DB.", assignee_name)
    else:
        logger.info("[Linko AI] Note %s 振り分け完了（担当者なし）", note_id)

    if not note.postit_note_id:
        from app.config import settings

        ok = await _sync_note_to_postit_async(
            request,
            note.id,
            note.content or "",
            settings.postit_board_id,
        )
        if ok:
            note.postit_board_id = settings.postit_board_id
            note.postit_note_id = f"bs-{note.id}"
            await db.flush()
            logger.info("[Linko AI] Note %s を付箋ボードに反映しました", note.id)


async def _sync_note_to_postit_async(
    request: Request, note_id: int, content: str, board_id: str
) -> bool:
    """Board System の付箋が付箋ボードに追加された際、中央付近（x:2000, y:2000）に配置する"""
    from app.config import settings

    postit_note_id = f"bs-{note_id}"
    payload = {
        "boardId": board_id,
        "note": {
            "id": postit_note_id,
            "text": content or "",
            "x": 2000.0,
            "y": 2000.0,
            "color": "#ffeb3b",
            "pinned": False,
            "author": "",
            "createdAt": int(time.time() * 1000),
        },
    }
    url = f"{settings.postit_board_url.rstrip('/')}/api/sticky_notes"
    try:
        client = request.app.state.http_client
        resp = await client.post(url, json=payload, timeout=5.0)
        return 200 <= resp.status_code < 300
    except Exception as e:
        logger.warning("[Linko AI] sync_note_to_postit failed: %s", e)
        return False


async def _place_on_task_board(
    db: AsyncSession, note_id: int, x: float, y: float, column: int
) -> None:
    result = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.TASK,
            BoardPlacement.owner_id.is_(None),
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        placement = BoardPlacement(
            note_id=note_id,
            board_type=BoardType.TASK,
            owner_id=None,
            position_x=x,
            position_y=y,
            matrix_quadrant=column,
            sort_order=0,
        )
        db.add(placement)
    else:
        existing.position_x = x
        existing.position_y = y
        existing.matrix_quadrant = column
