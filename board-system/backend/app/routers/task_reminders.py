# -*- coding: utf-8 -*-
"""
Personal Today タスクのリマインド API（デスクトップアプリ用）。

- GET  pending: 指定スロットで未表示の Today 付箋（calendar 由来除外）
- POST shown:  表示済みとして記録（同日同スロット再送防止）
- POST ack:    continue / done（done は lane=DONE に更新）
"""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import BoardPlacement, BoardType, Lane, StickyNote, TaskReminderLog, User

router = APIRouter(prefix="/api/personal", tags=["task_reminders"])
logger = logging.getLogger(__name__)

PLACEMENT_SOURCE_CALENDAR = "calendar"
MAX_TITLE_LEN = 40


def _jst_today() -> str:
    tz_name = getattr(settings, "calendar_timezone", None) or "Asia/Tokyo"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Tokyo")
    return datetime.now(tz).strftime("%Y-%m-%d")


def _short_title(content: str) -> str:
    text = (content or "").strip().replace("\n", " ")
    if len(text) <= MAX_TITLE_LEN:
        return text or "（無題）"
    return text[: MAX_TITLE_LEN - 1] + "…"


def _remind_message(title: str) -> str:
    return f"「{title}」、進みましたか？"


class PendingItem(BaseModel):
    placement_id: int
    note_id: int
    title: str
    message: str


class PendingResponse(BaseModel):
    owner_id: int
    slot: str
    remind_date: str
    items: list[PendingItem]


class ShownBody(BaseModel):
    placement_id: int
    note_id: int
    slot: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class AckBody(BaseModel):
    placement_id: int
    note_id: int
    slot: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    action: str = Field(..., pattern=r"^(continue|done)$")


async def _ensure_user(user_id: int, db: AsyncSession) -> None:
    r = await db.execute(select(User).where(User.id == user_id))
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")


async def _today_placements(user_id: int, db: AsyncSession) -> list[tuple[BoardPlacement, StickyNote]]:
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == user_id,
            BoardPlacement.lane == Lane.TODAY,
        )
        .order_by(BoardPlacement.sort_order, BoardPlacement.id)
    )
    rows = result.all()
    out = []
    for p, n in rows:
        src = getattr(p, "placement_source", None)
        if src == PLACEMENT_SOURCE_CALENDAR:
            continue
        out.append((p, n))
    return out


async def _logged_note_ids(
    user_id: int, remind_date: str, slot: str, db: AsyncSession
) -> set[int]:
    r = await db.execute(
        select(TaskReminderLog.note_id).where(
            TaskReminderLog.user_id == user_id,
            TaskReminderLog.remind_date == remind_date,
            TaskReminderLog.slot == slot,
        )
    )
    return {row[0] for row in r.all()}


@router.get("/{user_id}/task_reminders/pending", response_model=PendingResponse)
async def get_pending_task_reminders(
    user_id: int,
    slot: str = Query(..., pattern=r"^\d{2}:\d{2}$", description="リマインドスロット (例 13:00)"),
    max_items: int = Query(2, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """指定スロットでまだ表示していない Today タスクを返す。"""
    await _ensure_user(user_id, db)
    remind_date = _jst_today()
    logged = await _logged_note_ids(user_id, remind_date, slot, db)
    placements = await _today_placements(user_id, db)
    items: list[PendingItem] = []
    for p, n in placements:
        if p.note_id in logged:
            continue
        title = _short_title(n.content)
        items.append(
            PendingItem(
                placement_id=p.id,
                note_id=p.note_id,
                title=title,
                message=_remind_message(title),
            )
        )
        if len(items) >= max_items:
            break
    return PendingResponse(
        owner_id=user_id,
        slot=slot,
        remind_date=remind_date,
        items=items,
    )


@router.post("/{user_id}/task_reminders/shown")
async def mark_task_reminder_shown(
    user_id: int,
    body: ShownBody,
    db: AsyncSession = Depends(get_db),
):
    """デスクトップがリマインド UI を表示したとき呼ぶ（同日同スロットの再送防止）。"""
    await _ensure_user(user_id, db)
    remind_date = _jst_today()
    r = await db.execute(
        select(TaskReminderLog).where(
            TaskReminderLog.user_id == user_id,
            TaskReminderLog.note_id == body.note_id,
            TaskReminderLog.remind_date == remind_date,
            TaskReminderLog.slot == body.slot,
        )
    )
    if r.scalar_one_or_none() is not None:
        return {"ok": True, "already": True}
    r_pl = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.id == body.placement_id,
            BoardPlacement.owner_id == user_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.lane == Lane.TODAY,
        )
    )
    if r_pl.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Placement not found or not in TODAY")
    row = TaskReminderLog(
        user_id=user_id,
        note_id=body.note_id,
        placement_id=body.placement_id,
        remind_date=remind_date,
        slot=body.slot,
        action=None,
    )
    db.add(row)
    await db.flush()
    return {"ok": True, "already": False}


@router.post("/{user_id}/task_reminders/ack")
async def ack_task_reminder(
    user_id: int,
    body: AckBody,
    db: AsyncSession = Depends(get_db),
):
    """継続 / 完了 の応答。done のとき Personal を DONE に移動（Task 完了連動は board_placements と同じ）。"""
    await _ensure_user(user_id, db)
    remind_date = _jst_today()
    r = await db.execute(
        select(TaskReminderLog).where(
            TaskReminderLog.user_id == user_id,
            TaskReminderLog.note_id == body.note_id,
            TaskReminderLog.remind_date == remind_date,
            TaskReminderLog.slot == body.slot,
        )
    )
    log_row = r.scalar_one_or_none()
    if log_row is None:
        log_row = TaskReminderLog(
            user_id=user_id,
            note_id=body.note_id,
            placement_id=body.placement_id,
            remind_date=remind_date,
            slot=body.slot,
        )
        db.add(log_row)
        await db.flush()

    r_pl = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.id == body.placement_id,
            BoardPlacement.owner_id == user_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
        )
    )
    placement = r_pl.scalar_one_or_none()
    if placement is None:
        raise HTTPException(status_code=404, detail="Placement not found")

    log_row.action = body.action
    log_row.acked_at = datetime.utcnow()

    if body.action == "done" and placement.lane != Lane.DONE:
        prev_lane = placement.lane
        placement.lane = Lane.DONE
        r_task = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == placement.note_id,
                BoardPlacement.board_type == BoardType.TASK,
                BoardPlacement.owner_id.is_(None),
            )
        )
        task_placement = r_task.scalar_one_or_none()
        if task_placement:
            task_placement.matrix_quadrant = 5
        elif prev_lane == Lane.HELP_REQUEST:
            pass  # HELP_REQUEST から DONE は既存 PATCH と同様 task 連動のみ

    await db.flush()
    return {"ok": True, "action": body.action, "lane": placement.lane.value if placement.lane else None}
