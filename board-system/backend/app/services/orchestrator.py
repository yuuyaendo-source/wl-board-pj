# -*- coding: utf-8 -*-
"""
AIによる自動振り分けオーケストレーター。
新規付箋の内容を Triage → Matrix Scoring し、Task ボードの適切な列へ配置、担当者があれば Personal にも配布する。
改善指示書12を参考に現状の非同期構成に合わせて実装。
"""
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import run_matrix_scoring, run_triage
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane

logger = logging.getLogger("uvicorn")

# アイゼンハワー象限(1-4) → Taskボード列(1=アイデア, 2=短期, 3=長期, 4=重要)
# matrix.py: 1=緊急かつ重要, 2=重要だが非緊急, 3=緊急だが非重要, 4=どちらでもない
EISENHOWER_TO_COLUMN = {1: 4, 2: 3, 3: 2, 4: 1}


def _resolve_assignee_to_user_id_sync(assignee_name: str) -> int | None:
    """担当者名から users.id を取得（部分一致）。同期。"""
    from sqlalchemy import create_engine, select as sync_select
    from sqlalchemy.orm import Session

    from app.config import settings

    url = settings.database_url.replace("sqlite+aiosqlite", "sqlite")
    engine = create_engine(url)
    with Session(engine) as session:
        row = session.execute(
            sync_select(User.id).where(User.name.contains(assignee_name)).limit(1)
        ).first()
        return row[0] if row else None


async def process_new_note_ai(note_id: int, db: AsyncSession) -> None:
    """
    新規付箋に対する AI 振り分け（バックグラウンド的処理）。
    1. Triage でタスク判定
    2. タスクなら Matrix Scoring で緊急度・重要度を採点
    3. Task ボードの適切な列（1=アイデア, 2=短期, 3=長期, 4=重要）に配置
    4. 担当者名があれば Personal Inbox に配布
    例外時はログのみで握りつぶし、呼び出し元の 500 を防ぐ。
    """
    logger.info("[Rinko AI] Processing Note ID: %s...", note_id)

    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        logger.error("[Rinko AI] Note %s not found.", note_id)
        return

    content = note.content or ""

    # --- 1. Triage ---
    try:
        triage_result = await asyncio.to_thread(run_triage, content)
    except Exception as e:
        logger.warning("[Rinko AI] Triage failed: %s", e)
        triage_result = None

    if not triage_result:
        logger.warning(
            "[Rinko AI] Triage 未実行（APIキー未設定または失敗）。振り分け結果: アイデア列に配置。"
            " GEMINI_API_KEY を .env に設定するとタスク判定・列の自動振り分けが有効になります。"
        )
        await _place_on_task_board(db, note_id, 50.0, 50.0, 1)
        await db.flush()
        logger.info("[Rinko AI] Note %s 振り分け完了: アイデア列（Triage 未実行のためデフォルト）", note_id)
        return

    if not triage_result.get("is_task"):
        reason = triage_result.get("reason") or ""
        logger.info(
            "[Rinko AI] Note %s 振り分け完了: タスクでないと判定 → Main のみ（Task には出さない）｜%s",
            note_id,
            reason,
        )
        return

    triage_reason = triage_result.get("reason") or ""
    if triage_reason:
        logger.info("[Rinko AI] Note %s Triage 理由: %s", note_id, triage_reason)

    # --- 2. Matrix Scoring ---
    try:
        matrix_result = await asyncio.to_thread(run_matrix_scoring, content)
    except Exception as e:
        logger.warning("[Rinko AI] Matrix scoring failed: %s", e)
        matrix_result = None

    urgency = 50.0
    importance = 50.0
    quadrant_eisenhower = 4  # デフォルト: どちらでもない → アイデア列

    if matrix_result:
        urgency = float(matrix_result.get("urgency", 50))
        importance = float(matrix_result.get("importance", 50))
        quadrant_eisenhower = matrix_result.get("matrix_quadrant", 4)

    column = EISENHOWER_TO_COLUMN.get(quadrant_eisenhower, 1)
    COLUMN_NAMES = {1: "アイデア", 2: "短期タスク", 3: "長期タスク", 4: "重要"}
    column_name = COLUMN_NAMES.get(column, "アイデア")
    matrix_reason = (matrix_result or {}).get("reason") or ""
    logger.info(
        "[Rinko AI] Note %s 採点: U=%s, I=%s → 列「%s」｜%s",
        note_id,
        urgency,
        importance,
        column_name,
        matrix_reason,
    )

    # --- 3. Task ボードへ配置 ---
    await _place_on_task_board(db, note_id, urgency, importance, column)
    await db.flush()
    logger.info("[Rinko AI] Note %s 振り分け完了: Task の「%s」列に配置", note_id, column_name)

    # --- 4. Personal へ配布（担当者あり） ---
    assignee_name = triage_result.get("assignee_name")
    if assignee_name and isinstance(assignee_name, str):
        assignee_name = assignee_name.strip()
    if assignee_name:
        try:
            owner_id = await asyncio.to_thread(
                _resolve_assignee_to_user_id_sync, assignee_name
            )
        except Exception as e:
            logger.warning("[Rinko AI] Assignee resolve failed: %s", e)
            owner_id = None
        if owner_id is not None:
            result_user = await db.execute(select(User).where(User.id == owner_id))
            user = result_user.scalar_one_or_none()
            if user:
                logger.info("[Rinko AI] Assigning to user: %s", user.name)
                personal = BoardPlacement(
                    note_id=note_id,
                    board_type=BoardType.PERSONAL,
                    owner_id=owner_id,
                    lane=Lane.INBOX,
                    sort_order=0,
                )
                db.add(personal)
                await db.flush()
                logger.info("[Rinko AI] Note %s 振り分け完了: Task + Personal（%s）に配布", note_id, user.name)
        else:
            logger.warning("[Rinko AI] Assignee '%s' not found in DB.", assignee_name)
    else:
        logger.info("[Rinko AI] Note %s 振り分け完了（担当者なし）", note_id)


async def _place_on_task_board(
    db: AsyncSession, note_id: int, x: float, y: float, column: int
) -> None:
    """Task ボードへの配置（既存があれば更新）。column は 1=アイデア, 2=短期, 3=長期, 4=重要。"""
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
