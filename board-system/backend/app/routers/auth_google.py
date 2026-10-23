# -*- coding: utf-8 -*-
"""
Google カレンダー OAuth と今日の予定取得。
/auth/google?user_id= で Google へリダイレクト、/auth/google/callback でトークン保存。
PKCE: 認可開始時に自前で code_verifier を生成して DB に保存し、コールバックで取得して fetch_token に渡す。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import secrets
import urllib.parse
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidKey, InvalidSignature, InvalidTag
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.time_utils import get_timezone, now_jst, utc_now_naive
from app.db import get_db
from app.models import (
    BoardPlacement,
    BoardType,
    Lane,
    OAuthPkceState,
    PersonalSummaryCache,
    StickyNote,
    User,
    UserGoogleToken,
)
from app.models.sticky_note import NoteStatus
from app.services.calendar_placement import (
    CALENDAR_PLACEMENT_SOURCES,
    events_fingerprint,
    placement_source_for_event,
    should_skip_calendar_sticky,
)

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

GOOGLE_SCOPE = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]
PKCE_TTL_SECONDS = 600
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

# 復号失敗と断定できる例外クラス群
DECRYPTION_ERRORS = (ValueError, InvalidKey, InvalidTag, InvalidSignature)


def _pkce_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _exchange_token_with_pkce(code: str, redirect_uri: str, code_verifier: str) -> dict:
    import requests

    resp = requests.post(
        GOOGLE_TOKEN_URI,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.google_calendar_client_id,
            "client_secret": settings.google_calendar_client_secret,
            "code_verifier": code_verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    expiry = None
    if data.get("expires_in"):
        expiry = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
        expiry = expiry.replace(tzinfo=None)
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expiry": expiry,
    }


@router.get("/auth/google")
async def auth_google_start(
    user_id: int = Query(..., description="ユーザーID"),
    db: AsyncSession = Depends(get_db),
):
    if (
        not settings.google_calendar_client_id
        or not settings.google_calendar_client_secret
    ):
        raise HTTPException(status_code=503, detail="Google Calendar is not configured")
    redirect_uri = settings.google_calendar_redirect_uri
    if not redirect_uri:
        raise HTTPException(
            status_code=503, detail="google_calendar_redirect_uri is not set"
        )
    try:
        user = await db.execute(select(User.id).where(User.id == user_id))
        if user.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="User not found")

        code_verifier = secrets.token_urlsafe(32)
        code_challenge = _pkce_code_challenge(code_verifier)
        state_token = secrets.token_urlsafe(32)
        params = {
            "client_id": settings.google_calendar_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPE),
            "state": state_token,
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        authorization_url = GOOGLE_AUTH_URI + "?" + urllib.parse.urlencode(params)
        expires_at = utc_now_naive() + timedelta(seconds=PKCE_TTL_SECONDS)
        await db.execute(
            delete(OAuthPkceState).where(
                or_(
                    OAuthPkceState.user_id == user_id,
                    OAuthPkceState.expires_at < utc_now_naive(),
                )
            )
        )
        db.add(
            OAuthPkceState(
                state=state_token,
                user_id=user_id,
                code_verifier=code_verifier,
                expires_at=expires_at,
            )
        )
        await db.flush()
        logger.info("PKCE state saved for user_id=%s", user_id)
        return RedirectResponse(url=authorization_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/google/callback")
async def auth_google_callback(
    state: str = Query(..., description="OAuth CSRF state"),
    code: str | None = Query(None, description="OAuth 認可コード"),
    error: str | None = Query(
        None, description="OAuth エラー (アクセス拒否/キャンセル等)"
    ),
    db: AsyncSession = Depends(get_db),
):
    if not state:
        raise HTTPException(status_code=400, detail="state is required")
    redirect_uri = settings.google_calendar_redirect_uri
    if not redirect_uri:
        raise HTTPException(
            status_code=503, detail="google_calendar_redirect_uri is not set"
        )

    result = await db.execute(
        select(OAuthPkceState).where(
            OAuthPkceState.state == state,
            OAuthPkceState.expires_at > utc_now_naive(),
        )
    )
    row = result.scalar_one_or_none()
    code_verifier = row.code_verifier if row else None
    user_id = row.user_id if row else None
    if row:
        logger.info("PKCE state found for user_id=%s, deleting", user_id)
        await db.delete(row)
        await db.flush()
    else:
        logger.warning("PKCE state not found (expired or not saved)")

    if not code_verifier or user_id is None:
        raise HTTPException(
            status_code=400,
            detail="OAuth session expired or invalid. Please click 'Google カレンダーと連携' again from the personal board.",
        )

    base = (settings.oauth_success_redirect_base or "/boards").strip().rstrip("/")

    # Google 認証画面でユーザーがキャンセルまたは拒否した場合、パーソナルボードへ安全に戻す
    if error or not code:
        err_param = "cancelled" if error == "access_denied" else "error"
        path = f"{base}/personal/{user_id}?google_auth={err_param}".lstrip("/")
        logger.info(
            "OAuth cancelled or error for user_id=%s (error=%s), redirecting to %s",
            user_id,
            error,
            path,
        )
        return RedirectResponse(url=f"/{path}", status_code=302)

    try:
        data = await asyncio.to_thread(
            _exchange_token_with_pkce, code, redirect_uri, code_verifier
        )
    except Exception as e:
        logger.warning("token exchange failed for user_id=%s: %s", user_id, e)
        path = f"{base}/personal/{user_id}?google_auth=error".lstrip("/")
        return RedirectResponse(url=f"/{path}", status_code=302)

    result = await db.execute(
        select(UserGoogleToken).where(UserGoogleToken.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    expiry = data["expiry"]
    if row:
        row.access_token = data["access_token"]
        if data["refresh_token"]:
            row.refresh_token = data["refresh_token"]
        row.token_expiry = expiry
        row.updated_at = utc_now_naive()
    else:
        token = UserGoogleToken(
            user_id=user_id,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_expiry=expiry,
        )
        db.add(token)
    await db.flush()

    path = f"{base}/personal/{user_id}?google_auth=success".lstrip("/")
    try:
        await _refresh_user_calendar_and_today(user_id, db)
    except Exception as e:
        logger.warning("OAuth コールバック後のカレンダー取得に失敗: %s", e)
    return RedirectResponse(url=f"/{path}", status_code=302)


async def _fetch_today_events_for_user(
    user_id: int, db: AsyncSession
) -> list[dict] | None:
    try:
        result = await db.execute(
            select(UserGoogleToken).where(UserGoogleToken.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return []
    except (OperationalError, DBAPIError, SQLAlchemyError) as db_err:
        logger.error("[OAuth] DBクエリ一時エラー (User: %s): %s", user_id, db_err)
        return None

    try:
        # StringEncryptedType のプロパティ参照時に AES 復号が実行される
        raw_access_token = row.access_token
        raw_refresh_token = row.refresh_token
        token_expiry = row.token_expiry
    except DECRYPTION_ERRORS as decrypt_err:
        # 暗号キーの変更や不正パディングなど、データ破損・復号不能が確定した場合のみレコードを削除
        logger.warning(
            "[OAuth] トークン復号失敗 (暗号不整合)。レコードを安全に破棄します (User: %s): %s",
            user_id,
            decrypt_err,
        )
        try:
            await db.execute(
                delete(UserGoogleToken).where(UserGoogleToken.user_id == user_id)
            )
            await db.flush()
        except SQLAlchemyError as del_err:
            logger.error(
                "[OAuth] 破損トークン削除処理失敗 (User: %s): %s", user_id, del_err
            )
            await db.rollback()
        return None
    except Exception as unexpected_err:
        # DB セッションの内部エラーやその他の一時的例外ではトークンを削除せず中断
        logger.error(
            "[OAuth] トークン読み出し中に予期しない例外が発生しました (User: %s): %s",
            user_id,
            unexpected_err,
        )
        return None

    def _fetch():
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        tz = get_timezone(settings.calendar_timezone)
        now_local = datetime.now(tz)
        start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        time_min = start.isoformat()
        time_max = end.isoformat()

        creds = Credentials(
            token=raw_access_token,
            refresh_token=raw_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_calendar_client_id,
            client_secret=settings.google_calendar_client_secret,
            scopes=GOOGLE_SCOPE,
            expiry=token_expiry,
        )
        refreshed = False
        if creds.refresh_token and (creds.expired or not creds.valid):
            creds.refresh(Request())
            refreshed = True
        service = build("calendar", "v3", credentials=creds)
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        out = []
        for e in events:
            start_info = e.get("start", {}) or {}
            end_info = e.get("end", {}) or {}
            start_str = start_info.get("dateTime") or start_info.get("date") or ""
            end_str = end_info.get("dateTime") or end_info.get("date") or ""
            out.append(
                {
                    "id": e.get("id", ""),
                    "summary": e.get("summary", ""),
                    "start": start_str,
                    "end": end_str,
                    "eventType": e.get("eventType") or "default",
                }
            )
        if refreshed:
            return out, creds.token, creds.expiry
        return out, None, None

    try:
        events, new_token, new_expiry = await asyncio.to_thread(_fetch)
        if new_token is not None:
            result = await db.execute(
                select(UserGoogleToken).where(UserGoogleToken.user_id == user_id)
            )
            refresh_row = result.scalar_one_or_none()
            if refresh_row:
                refresh_row.access_token = new_token
                if new_expiry:
                    refresh_row.token_expiry = (
                        new_expiry.replace(tzinfo=None)
                        if getattr(new_expiry, "tzinfo", None)
                        else new_expiry
                    )
                refresh_row.updated_at = utc_now_naive()
                await db.flush()
        return events
    except Exception as e:
        logger.error(
            "[OAuth] Google Calendar API 取得失敗 (user_id=%s): %s", user_id, e
        )
        return None


async def _sync_user_calendar_events_cache(
    user_id: int, db: AsyncSession, events: list[dict] | None = None
) -> int:
    if events is None:
        events = await _fetch_today_events_for_user(user_id, db)
        if events is None:
            return 0
    person_id = str(user_id)
    events_json = json.dumps(events)
    result = await db.execute(
        select(PersonalSummaryCache).where(PersonalSummaryCache.person_id == person_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = PersonalSummaryCache(person_id=person_id, events=events_json, today="[]")
        db.add(row)
    else:
        row.events = events_json
        row.updated_at = utc_now_naive()
    await db.flush()
    return len(events)


async def _refresh_user_calendar_and_today(
    user_id: int, db: AsyncSession, events: list[dict] | None = None
) -> int:
    if events is None:
        events = await _fetch_today_events_for_user(user_id, db)
        if events is None:
            return 0
    person_id = str(user_id)
    events_json = json.dumps(events)
    today_items = []
    if events:
        try:
            from app.ai import run_today_short_summaries
            from app.services.llm_settings import get_resolved_ollama_async

            ollama_url, model_ov = await get_resolved_ollama_async(db)
            today_items = await asyncio.to_thread(
                run_today_short_summaries, events, ollama_url, model_ov
            )
        except Exception as e:
            logger.warning("Today 短縮文生成に失敗 user_id=%s: %s", user_id, e)
    if events and not today_items:
        today_items = [
            {
                "label": ((e.get("summary") or "")[:50] or "(無題)"),
                "summary": e.get("summary", ""),
                "start": e.get("start", ""),
                "end": e.get("end", ""),
            }
            for e in events
        ]
    today_json = json.dumps(today_items)
    result = await db.execute(
        select(PersonalSummaryCache).where(PersonalSummaryCache.person_id == person_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = PersonalSummaryCache(
            person_id=person_id,
            events=events_json,
            today=today_json,
        )
        db.add(row)
    else:
        row.events = events_json
        row.today = today_json
        row.updated_at = utc_now_naive()
    await db.flush()

    today_date = now_jst().date()

    # 当該ユーザーのパーソナルにあるすべてのカレンダー由来付箋を取得（due_date の NULL や過去日・別レーンも網羅）
    r_cal = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == user_id,
            BoardPlacement.placement_source.in_(CALENDAR_PLACEMENT_SOURCES),
        )
    )
    existing_pairs = r_cal.all()

    target_events = []
    for i, item in enumerate(today_items):
        if i >= len(events):
            break
        ev = events[i]
        if should_skip_calendar_sticky(ev):
            continue
        label = (item.get("label") or item.get("summary") or "").strip() or "(無題)"
        summary = (ev.get("summary") or "").strip()
        ev_id = str(ev.get("id") or "").strip()
        target_events.append(
            {
                "ev": ev,
                "event_id": ev_id,
                "label": label,
                "summary": summary,
                "source": placement_source_for_event(ev),
            }
        )

    matched_placement_ids = set()
    matched_event_indices = set()

    # 1. イベントIDによるマッチング
    for t_idx, target in enumerate(target_events):
        if not target["event_id"]:
            continue
        ev_key = target["event_id"][:64]
        for p, n in existing_pairs:
            if p.id in matched_placement_ids:
                continue
            if n.postit_note_id and n.postit_note_id == ev_key:
                matched_placement_ids.add(p.id)
                matched_event_indices.add(t_idx)
                if n.due_date != today_date:
                    n.due_date = today_date
                if p.lane == Lane.TODAY:
                    if n.content != target["label"]:
                        n.content = target["label"]
                    if p.placement_source != target["source"]:
                        p.placement_source = target["source"]
                break

    # 2. タイトル（ラベルまたはサマリ）によるマッチング
    for t_idx, target in enumerate(target_events):
        if t_idx in matched_event_indices:
            continue
        target_label = target["label"]
        target_summary = target["summary"]
        for p, n in existing_pairs:
            if p.id in matched_placement_ids:
                continue
            note_content = (n.content or "").strip()
            if note_content in (target_label, target_summary):
                matched_placement_ids.add(p.id)
                matched_event_indices.add(t_idx)
                if target["event_id"] and not n.postit_note_id:
                    n.postit_note_id = target["event_id"][:64]
                if n.due_date != today_date:
                    n.due_date = today_date
                if p.lane == Lane.TODAY:
                    if n.content != target_label:
                        n.content = target_label
                    if p.placement_source != target["source"]:
                        p.placement_source = target["source"]
                break

    # 3. 今日の予定にマッチしなかったカレンダー付箋を削除（レーン・日付に関わらず確実に削除）
    for p, n in existing_pairs:
        if p.id not in matched_placement_ids:
            nid = p.note_id
            await db.delete(p)
            await db.flush()
            r_other = await db.execute(
                select(BoardPlacement.id).where(BoardPlacement.note_id == nid).limit(1)
            )
            if r_other.scalar_one_or_none() is None:
                r_note = await db.execute(
                    select(StickyNote).where(StickyNote.id == nid)
                )
                note_row = r_note.scalar_one_or_none()
                if note_row:
                    await db.delete(note_row)

    r_sort = await db.execute(
        select(func.coalesce(func.max(BoardPlacement.sort_order), -1)).where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == user_id,
            BoardPlacement.lane == Lane.TODAY,
        )
    )
    next_sort = (r_sort.scalar() or 0) + 1

    # 4. 新規予定の付箋作成
    for t_idx, target in enumerate(target_events):
        if t_idx in matched_event_indices:
            continue

        note = StickyNote(
            content=target["label"],
            author_id=None,
            status=NoteStatus.ACTIVE,
            postit_board_id=None,
            postit_note_id=target["event_id"][:64] if target["event_id"] else None,
            due_date=today_date,
            is_personal_only=True,
        )
        db.add(note)
        await db.flush()
        placement = BoardPlacement(
            note_id=note.id,
            board_type=BoardType.PERSONAL,
            owner_id=user_id,
            lane=Lane.TODAY,
            sort_order=next_sort,
            placement_source=target["source"],
        )
        db.add(placement)
        next_sort += 1

    await db.flush()
    return len(events)


@router.get("/api/personal/{user_id}/calendar/events/live")
async def get_live_calendar_events(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")
    r_tok = await db.execute(
        select(UserGoogleToken).where(UserGoogleToken.user_id == user_id)
    )
    if r_tok.scalar_one_or_none() is None:
        return {"events": [], "synced": False, "stickies_updated": False}
    person_id = str(user_id)
    cached_events: list[dict] = []
    r_cache = await db.execute(
        select(PersonalSummaryCache).where(PersonalSummaryCache.person_id == person_id)
    )
    cache_row = r_cache.scalar_one_or_none()
    if cache_row and cache_row.events:
        try:
            cached_events = json.loads(cache_row.events)
        except (TypeError, ValueError):
            cached_events = []

    events = await _fetch_today_events_for_user(user_id, db)
    if events is None:
        return {"events": cached_events, "synced": False, "stickies_updated": False}

    # DB内の現在のカレンダー付箋数を取得して、予定数との乖離も検知
    r_has_cal = await db.execute(
        select(func.count(BoardPlacement.id)).where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == user_id,
            BoardPlacement.placement_source.in_(CALENDAR_PLACEMENT_SOURCES),
        )
    )
    current_cal_count = r_has_cal.scalar() or 0
    valid_events_count = len(
        [e for e in (events or []) if not should_skip_calendar_sticky(e)]
    )
    fingerprint_diff = events_fingerprint(cached_events) != events_fingerprint(events)

    # フィンガープリント変更、またはDB付箋数とカレンダー予定数に不一致がある場合は必ず同期・削除を実施
    stickies_updated = fingerprint_diff or (current_cal_count != valid_events_count)
    if stickies_updated:
        await _refresh_user_calendar_and_today(user_id, db, events=events)
    else:
        await _sync_user_calendar_events_cache(user_id, db, events)
    return {"events": events, "synced": True, "stickies_updated": stickies_updated}


@router.post("/api/personal/calendar_sync_all")
async def calendar_sync_all_events(db: AsyncSession = Depends(get_db)):
    if (
        not settings.google_calendar_client_id
        or not settings.google_calendar_client_secret
    ):
        return {"ok": True, "synced": [], "failed": [], "skipped": True}
    result = await db.execute(select(UserGoogleToken.user_id).distinct())
    user_ids = [r[0] for r in result.all()]
    synced = []
    failed = []

    for uid in user_ids:
        try:
            async with db.begin_nested():
                person_id = str(uid)
                r_cache = await db.execute(
                    select(PersonalSummaryCache).where(
                        PersonalSummaryCache.person_id == person_id
                    )
                )
                cache_row = r_cache.scalar_one_or_none()
                cached_events: list[dict] = []
                if cache_row and cache_row.events:
                    try:
                        cached_events = json.loads(cache_row.events)
                    except Exception:
                        cached_events = []

                events = await _fetch_today_events_for_user(uid, db)
                if events is not None:
                    r_has_cal = await db.execute(
                        select(func.count(BoardPlacement.id)).where(
                            BoardPlacement.board_type == BoardType.PERSONAL,
                            BoardPlacement.owner_id == uid,
                            BoardPlacement.placement_source.in_(
                                CALENDAR_PLACEMENT_SOURCES
                            ),
                        )
                    )
                    current_cal_count = r_has_cal.scalar() or 0
                    valid_events_count = len(
                        [
                            e
                            for e in (events or [])
                            if not should_skip_calendar_sticky(e)
                        ]
                    )
                    fingerprint_diff = events_fingerprint(
                        cached_events
                    ) != events_fingerprint(events)

                    if fingerprint_diff or (current_cal_count != valid_events_count):
                        await _refresh_user_calendar_and_today(uid, db, events=events)
                    else:
                        await _sync_user_calendar_events_cache(uid, db, events=events)
                    synced.append(uid)
            await db.commit()
        except Exception as e:
            logger.warning("calendar_sync_all user_id=%s failed: %s", uid, e)
            failed.append(uid)

    return {"ok": True, "synced": synced, "failed": failed}


@router.post("/api/personal/{user_id}/calendar/refresh")
async def refresh_personal_calendar(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    if (
        not settings.google_calendar_client_id
        or not settings.google_calendar_client_secret
    ):
        raise HTTPException(status_code=503, detail="Google Calendar is not configured")
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")
    count = await _refresh_user_calendar_and_today(user_id, db)
    return {"ok": True, "events_count": count}
