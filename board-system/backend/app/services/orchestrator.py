# -*- coding: utf-8 -*-
"""
AIによる自動振り分けオーケストレーター。
新規付箋の内容を Triage → Matrix Scoring し、Task ボードの適切な列へ配置、担当者があれば Personal にも配布する。
Board System でタスクになった付箋（postit 連携なし）は付箋ボードにも反映する。
"""
import asyncio
import json
import logging
import time
import urllib.request

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import run_matrix_scoring, run_triage
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane

logger = logging.getLogger("uvicorn")

# アイゼンハワー象限(1-4) → Taskボード列(1=アイデア, 2=短期, 3=長期, 4=重要)
# matrix.py: 1=緊急かつ重要, 2=重要だが非緊急, 3=緊急だが非重要, 4=どちらでもない
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


def _sync_database_url() -> str:
    """非同期用 URL を同期用に変換（別接続で担当者検索するため）。"""
    from app.config import settings

    url = settings.database_url
    if "postgresql+asyncpg" in url:
        return url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
    if "sqlite+aiosqlite" in url:
        return url.replace("sqlite+aiosqlite", "sqlite", 1)
    return url


def _resolve_assignee_to_user_id_sync(assignee_name: str) -> int | None:
    """担当者名から users.id を取得。完全一致を優先し、なければ部分一致。同期専用エンジンで実行。"""
    from sqlalchemy import create_engine, select as sync_select
    from sqlalchemy.orm import Session

    raw = (assignee_name or "").strip()
    normalized = _normalize_assignee_name(raw) if raw else ""
    if not raw and not normalized:
        return None

    url = _sync_database_url()
    engine = create_engine(url)
    with Session(engine) as session:
        # 完全一致を優先（姓のみ or フルネーム）
        for candidate in (normalized, raw):
            if not candidate:
                continue
            row = session.execute(
                sync_select(User.id).where(User.name == candidate).limit(1)
            ).first()
            if row:
                return row[0]
        # 部分一致（User.name に candidate が含まれる）
        for candidate in (normalized, raw):
            if not candidate:
                continue
            row = session.execute(
                sync_select(User.id).where(User.name.contains(candidate)).limit(1)
            ).first()
            if row:
                return row[0]
    return None


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
    content_preview = (content[:300] + "…") if len(content) > 300 else (content or "(空)")
    logger.info("[Rinko AI] Note %s 内容: %s", note_id, content_preview)

    # --- 1. Triage ---
    try:
        triage_result = await asyncio.to_thread(run_triage, content)
    except Exception as e:
        logger.warning("[Rinko AI] Triage failed: %s", e)
        triage_result = None

    if not triage_result:
        logger.warning(
            "[Rinko AI] Triage 未実行（APIキー未設定または失敗）。振り分け結果: アイデア列に配置。"
            " OLLAMA_URL を .env に設定するとタスク判定・列の自動振り分けが有効になります。"
        )
        await _place_on_task_board(db, note_id, 50.0, 50.0, 1)
        await db.flush()
        logger.info("[Rinko AI] Note %s 振り分け完了: アイデア列（Triage 未実行のためデフォルト）", note_id)
        if not note.postit_note_id:
            from app.config import settings
            ok = await asyncio.to_thread(
                _sync_note_to_postit_sync,
                note.id,
                note.content or "",
                settings.postit_board_id,
                settings.postit_board_url,
            )
            if ok:
                note.postit_board_id = settings.postit_board_id
                note.postit_note_id = f"bs-{note.id}"
                await db.flush()
                logger.info("[Rinko AI] Note %s を付箋ボードに反映しました", note.id)
        return

    # タスクでないと判定されても全件 Task ボードに載せる（曖昧な内容で取りこぼしを防ぐ）
    if not triage_result.get("is_task"):
        reason = triage_result.get("reason") or ""
        logger.info(
            "[Rinko AI] Note %s タスクでないと判定 → アイデア列に配置｜%s",
            note_id,
            reason,
        )
        await _place_on_task_board(db, note_id, 50.0, 50.0, 1)  # 1=アイデア
        await db.flush()
        # 担当者名があれば Personal 配布を試みる（下記 4 と共通のためここで続行）

    triage_reason = triage_result.get("reason") or ""
    if triage_reason and triage_result.get("is_task"):
        logger.info("[Rinko AI] Note %s Triage 理由: %s", note_id, triage_reason)

    # --- 2. Matrix Scoring（タスクと判定されたときのみ） ---
    urgency, importance, column = 50.0, 50.0, 1
    column_name = "アイデア"
    if triage_result.get("is_task"):
        try:
            matrix_result = await asyncio.to_thread(run_matrix_scoring, content)
        except Exception as e:
            logger.warning("[Rinko AI] Matrix scoring failed: %s", e)
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
            "[Rinko AI] Note %s 採点: U=%s, I=%s → 列「%s」｜%s",
            note_id,
            urgency,
            importance,
            column_name,
            matrix_reason,
        )
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

    # Board System でタスクになった付箋（付箋ボード連携なし）を付箋ボードに反映
    if not note.postit_note_id:
        from app.config import settings

        ok = await asyncio.to_thread(
            _sync_note_to_postit_sync,
            note.id,
            note.content or "",
            settings.postit_board_id,
            settings.postit_board_url,
        )
        if ok:
            note.postit_board_id = settings.postit_board_id
            note.postit_note_id = f"bs-{note.id}"
            await db.flush()
            logger.info("[Rinko AI] Note %s を付箋ボードに反映しました", note.id)


def _sync_note_to_postit_sync(note_id: int, content: str, board_id: str, base_url: str) -> bool:
    """Board System の付箋を付箋ボードに追加する（同期）。成功時 True。"""
    postit_note_id = f"bs-{note_id}"
    payload = {
        "boardId": board_id,
        "note": {
            "id": postit_note_id,
            "text": content or "",
            "x": 0,
            "y": 0,
            "color": "#ffeb3b",
            "pinned": False,
            "author": "",
            "createdAt": int(time.time() * 1000),
        },
    }
    url = f"{base_url.rstrip('/')}/api/sticky_notes"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if 200 <= resp.status < 300:
                return True
    except Exception as e:
        logger.warning("[Rinko AI] sync_note_to_postit failed: %s", e)
    return False


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
