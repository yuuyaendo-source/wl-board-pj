# -*- coding: utf-8 -*-
"""
Google カレンダー予定のリマインド API（デスクトップ用）。

- GET  pending: 開始 N 分前の予定（Google 未連携時は空）
- POST shown:  表示済み記録
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
from app.models import CalendarReminderLog, User, UserGoogleToken

router = APIRouter(prefix="/api/personal", tags=["calendar_reminders"])
logger = logging.getLogger(__name__)

REMIND_KIND_BEFORE_15 = "before_15"
DEFAULT_MINUTES_BEFORE = 15
# ポーリング間隔を考慮した通知ウィンドウ（分）
WINDOW_MARGIN_MIN = 2.0


def _jst_now() -> datetime:
    tz_name = getattr(settings, "calendar_timezone", None) or "Asia/Tokyo"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Tokyo")
    return datetime.now(tz)


def _jst_today() -> str:
    return _jst_now().strftime("%Y-%m-%d")


def _short_title(summary: str) -> str:
    text = (summary or "").strip().replace("\n", " ") or "予定"
    if len(text) <= 40:
        return text
    return text[:39] + "…"


def _parse_event_start(start_str: str, tz: ZoneInfo) -> datetime | None:
    """終日 (date のみ) は None。dateTime 予定のみ。"""
    if not start_str or "T" not in start_str:
        return None
    try:
        # Google は Z または +09:00 付き
        s = start_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        return dt.astimezone(tz)
    except Exception:
        return None


def _voice_text(title: str, minutes_before: int) -> str:
    return f"お疲れ様です。{minutes_before}分後に、{title}が始まります。"


def _toast_message(title: str, minutes_before: int) -> str:
    return f"{minutes_before}分後に「{title}」が始まります"


class CalendarPendingItem(BaseModel):
    event_id: str
    title: str
    start: str
    message: str
    voice_text: str


class CalendarPendingResponse(BaseModel):
    owner_id: int
    remind_date: str
    minutes_before: int
    items: list[CalendarPendingItem]


class CalendarShownBody(BaseModel):
    event_id: str
    event_start: str = ""  # 開始時刻 ISO。予定変更時は別扱いで再リマインド可能にする
    remind_kind: str = Field(default=REMIND_KIND_BEFORE_15, max_length=16)


async def _ensure_user(user_id: int, db: AsyncSession) -> None:
    r = await db.execute(select(User).where(User.id == user_id))
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")


async def _logged_starts_by_event(
    user_id: int, remind_date: str, remind_kind: str, db: AsyncSession
) -> dict[str, str]:
    """event_id → リマインド済みの開始時刻 (event_summary 列に保存)。"""
    r = await db.execute(
        select(CalendarReminderLog.event_id, CalendarReminderLog.event_summary).where(
            CalendarReminderLog.user_id == user_id,
            CalendarReminderLog.remind_date == remind_date,
            CalendarReminderLog.remind_kind == remind_kind,
        )
    )
    return {row[0]: (row[1] or "") for row in r.all()}


@router.get("/{user_id}/calendar_reminders/pending", response_model=CalendarPendingResponse)
async def get_pending_calendar_reminders(
    user_id: int,
    minutes_before: int = Query(DEFAULT_MINUTES_BEFORE, ge=1, le=15),
    db: AsyncSession = Depends(get_db),
):
    """Google 連携済みユーザーの、まもなく開始する予定を返す。未連携は items=[]。"""
    await _ensure_user(user_id, db)
    remind_date = _jst_today()
    remind_kind = REMIND_KIND_BEFORE_15 if minutes_before == 15 else f"before_{minutes_before}"

    r_tok = await db.execute(select(UserGoogleToken).where(UserGoogleToken.user_id == user_id))
    if r_tok.scalar_one_or_none() is None:
        return CalendarPendingResponse(
            owner_id=user_id,
            remind_date=remind_date,
            minutes_before=minutes_before,
            items=[],
        )

    from app.routers.auth_google import _fetch_today_events_for_user, _sync_user_calendar_events_cache

    events = await _fetch_today_events_for_user(user_id, db)
    try:
        await _sync_user_calendar_events_cache(user_id, db, events)
    except Exception as e:
        logger.warning("calendar pending cache sync failed user_id=%s: %s", user_id, e)
    logged = await _logged_starts_by_event(user_id, remind_date, remind_kind, db)

    tz_name = getattr(settings, "calendar_timezone", None) or "Asia/Tokyo"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Tokyo")
    now = _jst_now()

    items: list[CalendarPendingItem] = []
    for e in events:
        event_id = (e.get("id") or "").strip()
        if not event_id:
            continue
        start_str = e.get("start") or ""
        if logged.get(event_id) == start_str:
            continue
        start_dt = _parse_event_start(start_str, tz)
        if start_dt is None:
            continue
        minutes_until = (start_dt - now).total_seconds() / 60.0
        lo = minutes_before - WINDOW_MARGIN_MIN
        hi = minutes_before + WINDOW_MARGIN_MIN
        if not (lo <= minutes_until <= hi):
            continue
        title = _short_title(e.get("summary") or "")
        items.append(
            CalendarPendingItem(
                event_id=event_id,
                title=title,
                start=start_str,
                message=_toast_message(title, minutes_before),
                voice_text=_voice_text(title, minutes_before),
            )
        )

    return CalendarPendingResponse(
        owner_id=user_id,
        remind_date=remind_date,
        minutes_before=minutes_before,
        items=items,
    )


@router.post("/{user_id}/calendar_reminders/shown")
async def mark_calendar_reminder_shown(
    user_id: int,
    body: CalendarShownBody,
    minutes_before: int = Query(DEFAULT_MINUTES_BEFORE, ge=1, le=15),
    db: AsyncSession = Depends(get_db),
):
    """デスクトップがリマインドを表示したとき呼ぶ。"""
    await _ensure_user(user_id, db)
    remind_date = _jst_today()
    remind_kind = REMIND_KIND_BEFORE_15 if minutes_before == 15 else f"before_{minutes_before}"
    event_id = (body.event_id or "").strip()
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    event_start = (body.event_start or "").strip()
    r = await db.execute(
        select(CalendarReminderLog).where(
            CalendarReminderLog.user_id == user_id,
            CalendarReminderLog.event_id == event_id,
            CalendarReminderLog.remind_date == remind_date,
            CalendarReminderLog.remind_kind == remind_kind,
        )
    )
    row = r.scalar_one_or_none()
    if row is not None:
        if (row.event_summary or "") == event_start:
            return {"ok": True, "already": True}
        row.event_summary = event_start
        await db.flush()
        return {"ok": True, "already": False, "updated": True}

    row = CalendarReminderLog(
        user_id=user_id,
        event_id=event_id,
        remind_date=remind_date,
        remind_kind=remind_kind,
        event_summary=event_start or None,
    )
    db.add(row)
    await db.flush()
    return {"ok": True, "already": False}
