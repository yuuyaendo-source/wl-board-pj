# -*- coding: utf-8 -*-
"""
Google カレンダー OAuth と今日の予定取得。
/auth/google?user_id= で Google へリダイレクト、/auth/google/callback でトークン保存。
PKCE: 認可開始時に自前で code_verifier を生成して DB に保存し、コールバックで取得して fetch_token に渡す。
"""
import asyncio
import hashlib
import json
import logging
import secrets
import urllib.parse
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from app.config import settings
from app.db import get_db
from app.models import OAuthPkceState, PersonalSummaryCache, User, UserGoogleToken

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

GOOGLE_SCOPE = ["https://www.googleapis.com/auth/calendar.readonly"]
PKCE_TTL_SECONDS = 600
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


def _pkce_code_challenge(verifier: str) -> str:
    """PKCE: code_verifier から S256 の code_challenge を計算。"""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _exchange_token_with_pkce(code: str, redirect_uri: str, code_verifier: str) -> dict:
    """トークンエンドポイントに code_verifier を付けて POST（自前実装で確実に送る）。"""
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
        # PostgreSQL TIMESTAMP WITHOUT TIME ZONE 用に naive UTC に変換
        expiry = expiry.replace(tzinfo=None)
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expiry": expiry,
    }


def _set_code_verifier_on_flow(flow, code_verifier: str) -> None:
    """Flow の内部クライアントに code_verifier を設定（authorization_url で code_challenge に使われる）。"""
    try:
        session = getattr(flow, "oauth2session", None)
        if session is not None:
            client = getattr(session, "_client", None) or getattr(session, "client", None)
            if client is not None:
                setattr(client, "code_verifier", code_verifier)
    except Exception:
        pass


def _google_flow(redirect_uri: str, code_verifier: str | None = None):
    """Google OAuth Flow を生成（同期）。code_verifier を渡すと PKCE で使用。"""
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_calendar_client_id,
                "client_secret": settings.google_calendar_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=GOOGLE_SCOPE,
        redirect_uri=redirect_uri,
    )
    if code_verifier:
        _set_code_verifier_on_flow(flow, code_verifier)
    return flow


@router.get("/auth/google")
async def auth_google_start(
    user_id: int = Query(..., description="ユーザーID"),
    db: AsyncSession = Depends(get_db),
):
    """Google OAuth 開始。user_id を state に載せて Google へリダイレクト。PKCE の code_verifier を DB に保存。"""
    if not settings.google_calendar_client_id or not settings.google_calendar_client_secret:
        raise HTTPException(status_code=503, detail="Google Calendar is not configured")
    redirect_uri = settings.google_calendar_redirect_uri
    if not redirect_uri:
        raise HTTPException(status_code=503, detail="google_calendar_redirect_uri is not set")
    try:
        # PKCE: code_verifier を生成し、認可URLを自前で組み立て（ライブラリ任せだと code_challenge が一致しないため）
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = _pkce_code_challenge(code_verifier)
        params = {
            "client_id": settings.google_calendar_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPE),
            "state": str(user_id),
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        authorization_url = GOOGLE_AUTH_URI + "?" + urllib.parse.urlencode(params)
        expires_at = datetime.utcnow() + timedelta(seconds=PKCE_TTL_SECONDS)
        await db.execute(delete(OAuthPkceState).where(OAuthPkceState.state == str(user_id)))
        db.add(OAuthPkceState(state=str(user_id), code_verifier=code_verifier, expires_at=expires_at))
        await db.flush()
        logger.info("PKCE state saved for state=%s (user_id=%s)", user_id, user_id)
        return RedirectResponse(url=authorization_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/google/callback")
async def auth_google_callback(
    code: str = Query(..., description="OAuth 認可コード"),
    state: str = Query(..., description="user_id"),
    db: AsyncSession = Depends(get_db),
):
    """Google OAuth コールバック。トークンを保存し /personal/{user_id} へリダイレクト。"""
    if not code or not state:
        raise HTTPException(status_code=400, detail="code and state are required")
    try:
        user_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid state")
    redirect_uri = settings.google_calendar_redirect_uri
    if not redirect_uri:
        raise HTTPException(status_code=503, detail="google_calendar_redirect_uri is not set")

    result = await db.execute(
        select(OAuthPkceState).where(
            OAuthPkceState.state == state,
            OAuthPkceState.expires_at > datetime.utcnow(),
        )
    )
    row = result.scalar_one_or_none()
    code_verifier = row.code_verifier if row else None
    if row:
        logger.info("PKCE state found for state=%s, deleting", state)
        await db.delete(row)
        await db.flush()
    else:
        logger.warning("PKCE state not found for state=%s (expired or not saved)", state)

    if not code_verifier:
        raise HTTPException(
            status_code=400,
            detail="OAuth session expired or invalid. Please click 'Google カレンダーと連携' again from the personal board.",
        )

    try:
        data = await asyncio.to_thread(_exchange_token_with_pkce, code, redirect_uri, code_verifier)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"token exchange failed: {e}")

    # upsert user_google_tokens
    result = await db.execute(select(UserGoogleToken).where(UserGoogleToken.user_id == user_id))
    row = result.scalar_one_or_none()
    expiry = data["expiry"]
    if row:
        row.access_token = data["access_token"]
        if data["refresh_token"]:
            row.refresh_token = data["refresh_token"]
        row.token_expiry = expiry
        row.updated_at = datetime.utcnow()
    else:
        token = UserGoogleToken(
            user_id=user_id,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_expiry=expiry,
        )
        db.add(token)
    await db.flush()

    # フロントのパーソナルボードへ。ベースURLは設定から取れないので相対パス
    return RedirectResponse(url=f"/personal/{user_id}", status_code=302)


async def _fetch_today_events_for_user(user_id: int, db: AsyncSession) -> list[dict]:
    """指定ユーザーの Google トークンで今日の予定を取得。"""
    result = await db.execute(select(UserGoogleToken).where(UserGoogleToken.user_id == user_id))
    row = result.scalar_one_or_none()
    if not row:
        return []

    def _fetch():
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request

        creds = Credentials(
            token=row.access_token,
            refresh_token=row.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_calendar_client_id,
            client_secret=settings.google_calendar_client_secret,
            scopes=GOOGLE_SCOPE,
        )
        refreshed = False
        if row.token_expiry and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            refreshed = True
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])
        out = []
        for e in events:
            start_info = e.get("start", {}) or {}
            end_info = e.get("end", {}) or {}
            start_str = start_info.get("dateTime") or start_info.get("date") or ""
            end_str = end_info.get("dateTime") or end_info.get("date") or ""
            out.append({
                "summary": e.get("summary", ""),
                "start": start_str,
                "end": end_str,
            })
        if refreshed:
            return out, creds.token, creds.expiry
        return out, None, None

    try:
        ret = await asyncio.to_thread(_fetch)
        if len(ret) == 3:
            events, new_token, new_expiry = ret
            if new_token is not None:
                row.access_token = new_token
                if new_expiry:
                    # PostgreSQL TIMESTAMP WITHOUT TIME ZONE 用に naive に変換
                    row.token_expiry = new_expiry.replace(tzinfo=None) if getattr(new_expiry, "tzinfo", None) else new_expiry
                row.updated_at = datetime.utcnow()
                await db.flush()
        else:
            events = ret[0]
        return events
    except Exception:
        return []


@router.post("/api/personal/{user_id}/calendar/refresh")
async def refresh_personal_calendar(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """指定ユーザーの Google カレンダーから今日の予定を取得し、PersonalSummaryCache.events に保存。"""
    if not settings.google_calendar_client_id or not settings.google_calendar_client_secret:
        raise HTTPException(status_code=503, detail="Google Calendar is not configured")
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")
    events = await _fetch_today_events_for_user(user_id, db)
    if not events:
        return {"ok": True, "events_count": 0}
    person_id = str(user_id)
    events_json = json.dumps(events)
    result = await db.execute(select(PersonalSummaryCache).where(PersonalSummaryCache.person_id == person_id))
    row = result.scalar_one_or_none()
    if row is None:
        stmt = sqlite_upsert(PersonalSummaryCache).values(
            person_id=person_id,
            events=events_json,
            today="[]",
        )
        await db.execute(stmt)
    else:
        stmt = sqlite_upsert(PersonalSummaryCache).values(
            person_id=person_id,
            events=events_json,
            today=row.today or "[]",
        ).on_conflict_do_update(
            index_elements=["person_id"],
            set_={"events": events_json, "updated_at": datetime.utcnow()},
        )
        await db.execute(stmt)
    await db.flush()
    return {"ok": True, "events_count": len(events)}
