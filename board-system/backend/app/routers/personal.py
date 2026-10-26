# -*- coding: utf-8 -*-
"""
パーソナル summary / today API。
linko-system が GET /api/personal/{person_id}/summary でサマリを取得し、
POST /api/personal/{person_id}/today でカレンダーキーワード由来の Today を送る。
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.personal_summary import PersonalSummaryCache
from app.models.user import User
from app.core.time_utils import utc_now_naive

router = APIRouter(prefix="/api/personal", tags=["personal"])


class TodayItem(BaseModel):
    label: str
    summary: str = ""
    start: str = ""
    end: str = ""


class PostTodayBody(BaseModel):
    items: list[TodayItem] = []


class EventItem(BaseModel):
    summary: str = ""
    start: str = ""
    end: str = ""


class PostEventsBody(BaseModel):
    events: list[EventItem] = []


async def _resolve_cache_row(
    person_id: str, db: AsyncSession
) -> tuple[PersonalSummaryCache | None, str]:
    """修正⑥: person_id（user_id、または email 等）から PersonalSummaryCache を柔軟に解決。"""
    pid_clean = person_id.strip()
    result = await db.execute(
        select(PersonalSummaryCache).where(PersonalSummaryCache.person_id == pid_clean)
    )
    row = result.scalar_one_or_none()
    if row:
        return row, pid_clean

    if "@" in pid_clean:
        user_res = await db.execute(
            select(User.id).where(func.lower(User.email) == pid_clean.lower())
        )
        uid = user_res.scalar_one_or_none()
        if uid is not None:
            uid_str = str(uid)
            result = await db.execute(
                select(PersonalSummaryCache).where(
                    PersonalSummaryCache.person_id == uid_str
                )
            )
            return result.scalar_one_or_none(), uid_str
    elif pid_clean.isdigit():
        user_res = await db.execute(select(User.email).where(User.id == int(pid_clean)))
        email = user_res.scalar_one_or_none()
        if email:
            result = await db.execute(
                select(PersonalSummaryCache).where(
                    PersonalSummaryCache.person_id == email.strip().lower()
                )
            )
            found = result.scalar_one_or_none()
            if found:
                return found, email.strip().lower()

    return None, pid_clean


@router.get("/{person_id}/summary")
async def get_personal_summary(
    person_id: str,
    db: AsyncSession = Depends(get_db),
):
    row, _ = await _resolve_cache_row(person_id, db)
    if row is None:
        return {"events": [], "today": []}
    try:
        events = json.loads(row.events) if row.events else []
    except (TypeError, ValueError):
        events = []
    try:
        today = json.loads(row.today) if row.today else []
    except (TypeError, ValueError):
        today = []
    return {"events": events, "today": today}


@router.post("/{person_id}/today")
async def post_personal_today(
    person_id: str,
    body: PostTodayBody,
    db: AsyncSession = Depends(get_db),
):
    if not person_id.strip():
        raise HTTPException(status_code=400, detail="person_id is required")
    today_json = json.dumps([item.model_dump() for item in body.items])

    row, effective_pid = await _resolve_cache_row(person_id, db)
    if row is None:
        row = PersonalSummaryCache(
            person_id=effective_pid, events="[]", today=today_json
        )
        db.add(row)
    else:
        row.today = today_json
        row.updated_at = utc_now_naive()
    await db.flush()
    return {"ok": True}


@router.post("/{person_id}/events")
async def post_personal_events(
    person_id: str,
    body: PostEventsBody,
    db: AsyncSession = Depends(get_db),
):
    if not person_id.strip():
        raise HTTPException(status_code=400, detail="person_id is required")
    events_json = json.dumps([e.model_dump() for e in body.events])

    row, effective_pid = await _resolve_cache_row(person_id, db)
    if row is None:
        row = PersonalSummaryCache(
            person_id=effective_pid, events=events_json, today="[]"
        )
        db.add(row)
    else:
        row.events = events_json
        row.updated_at = utc_now_naive()
    await db.flush()
    return {"ok": True}
