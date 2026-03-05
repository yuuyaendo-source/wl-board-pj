# -*- coding: utf-8 -*-
"""
パーソナル summary / today API。
linko-system が GET /api/personal/{person_id}/summary でサマリを取得し、
POST /api/personal/{person_id}/today でカレンダーキーワード由来の Today を送る。
"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.personal_summary import PersonalSummaryCache

router = APIRouter(prefix="/api/personal", tags=["personal"])


class TodayItem(BaseModel):
    """Today 1件。label 必須、他は任意。"""
    label: str
    summary: str = ""
    start: str = ""
    end: str = ""


class PostTodayBody(BaseModel):
    """POST /api/personal/{person_id}/today の body。"""
    items: list[TodayItem] = []


class EventItem(BaseModel):
    """今日の予定1件。"""
    summary: str = ""
    start: str = ""
    end: str = ""


class PostEventsBody(BaseModel):
    """POST /api/personal/{person_id}/events の body。カレンダー枠に表示する今日の予定を保存。"""
    events: list[EventItem] = []


@router.get("/{person_id}/summary")
async def get_personal_summary(
    person_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    linko-system 用。指定 person_id の events と today を返す。
    キャッシュが無い場合は events=[], today=[] で 200 を返す。
    """
    result = await db.execute(
        select(PersonalSummaryCache).where(PersonalSummaryCache.person_id == person_id)
    )
    row = result.scalar_one_or_none()
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
    """
    linko-system のカレンダーキーワード連携用。Today 項目を上書き保存する。
    """
    if not person_id.strip():
        raise HTTPException(status_code=400, detail="person_id is required")
    today_json = json.dumps([item.model_dump() for item in body.items])

    result = await db.execute(
        select(PersonalSummaryCache).where(PersonalSummaryCache.person_id == person_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = PersonalSummaryCache(person_id=person_id, events="[]", today=today_json)
        db.add(row)
    else:
        row.today = today_json
        row.updated_at = datetime.utcnow()
    await db.flush()
    return {"ok": True}


@router.post("/{person_id}/events")
async def post_personal_events(
    person_id: str,
    body: PostEventsBody,
    db: AsyncSession = Depends(get_db),
):
    """
    今日の予定（events）をキャッシュに保存。カレンダー連携元（Google 取得結果等）が呼ぶ。
    today は変更せず、events のみ更新する。
    """
    if not person_id.strip():
        raise HTTPException(status_code=400, detail="person_id is required")
    events_json = json.dumps([e.model_dump() for e in body.events])

    result = await db.execute(
        select(PersonalSummaryCache).where(PersonalSummaryCache.person_id == person_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = PersonalSummaryCache(person_id=person_id, events=events_json, today="[]")
        db.add(row)
    else:
        row.events = events_json
        row.updated_at = datetime.utcnow()
    await db.flush()
    return {"ok": True}
