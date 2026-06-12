# -*- coding: utf-8 -*-
"""リン子ブレストからの Google カレンダー登録（確認フロー・A案: チャットで修正）。"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from app.ai.client import generate_json
from app.services.calendar_proposal_store import (
    CalendarProposal,
    create_proposal,
    delete_proposal,
    get_proposal,
    update_draft,
)

logger = logging.getLogger(__name__)

_CONFIRM_RE = re.compile(
    r"^(はい|ええ|うん|ok|okay|お願い|お願いします|入れて|登録|登録して|それで|いいよ|いいです|大丈夫).*$",
    re.IGNORECASE,
)
_CANCEL_RE = re.compile(
    r"^(いいえ|いえ|やめ|やめて|キャンセル|不要|結構|やっぱ|違う).*$",
    re.IGNORECASE,
)


def _tz() -> ZoneInfo:
    try:
        from app.config import settings

        name = getattr(settings, "calendar_timezone", None) or "Asia/Tokyo"
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("Asia/Tokyo")


def _now_ctx() -> str:
    return datetime.now(_tz()).strftime("%Y-%m-%d %H:%M (%A) Asia/Tokyo")


def interpret_pending_message(text: str) -> str:
    """pending 中のユーザ発話を confirm / cancel / revise に分類。"""
    t = (text or "").strip()
    if not t:
        return "revise"
    if _CANCEL_RE.match(t):
        return "cancel"
    if _CONFIRM_RE.match(t):
        return "confirm"
    return "revise"


def _format_spoken_summary(draft: dict[str, Any]) -> str:
    summary = (draft.get("summary") or "予定").strip()
    start = (draft.get("start") or "").strip()
    end = (draft.get("end") or "").strip()
    try:
        st = datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(_tz())
        en = datetime.fromisoformat(end.replace("Z", "+00:00")).astimezone(_tz())
        date_part = st.strftime("%m月%d日")
        time_part = f"{st.strftime('%H:%M')}〜{en.strftime('%H:%M')}"
        return f"{date_part}{time_part}、「{summary}」でカレンダーに入れますか？"
    except Exception:
        return f"「{summary}」をカレンダーに入れますか？"


def proposal_payload(p: CalendarProposal) -> dict[str, Any]:
    return {
        "type": "action_proposal",
        "action": "calendar_create",
        "proposal_id": p.proposal_id,
        "draft": p.draft,
        "spoken": _format_spoken_summary(p.draft),
    }


def extract_calendar_from_conversation(messages: list[dict[str, str]]) -> dict[str, Any] | None:
    """会話からカレンダー登録意図を抽出。JSON を返す。"""
    convo = []
    for m in messages[-8:]:
        role = m.get("role") or "user"
        content = (m.get("content") or "").strip()
        if content:
            convo.append(f"{role}: {content}")
    if not convo:
        return None
    prompt = f"""あなたは社内アシスタントの意図抽出器です。会話から Google カレンダーへの「新規予定登録」意図があるか判定し、JSON のみを返してください。

現在日時: {_now_ctx()}

会話:
{chr(10).join(convo)}

出力 JSON スキーマ:
{{
  "intent": "calendar_create" | "other",
  "ready": true | false,
  "missing": ["start", "summary", ...],
  "clarify": "情報が足りないときの短い質問（リン子口調・1文）",
  "draft": {{
    "summary": "予定タイトル",
    "start": "ISO8601 with offset e.g. 2026-06-02T14:00:00+09:00",
    "end": "ISO8601 with offset",
    "description": ""
  }}
}}

ルール:
- 予定登録の依頼でなければ intent=other
- 日時かタイトルが曖昧なら ready=false と missing/clarify を埋める
- 終了時刻が無ければ開始から30分後を end にする
- タイムゾーンは +09:00 (Asia/Tokyo)
"""
    data = generate_json(prompt)
    if not isinstance(data, dict):
        return None
    return data


def revise_draft(proposal: CalendarProposal, user_text: str) -> dict[str, Any] | None:
    prompt = f"""カレンダー登録案をユーザーの修正指示で更新し、JSON のみ返してください。

現在日時: {_now_ctx()}

現在の案:
{json.dumps(proposal.draft, ensure_ascii=False)}

修正指示:
{user_text}

出力:
{{
  "ready": true,
  "draft": {{
    "summary": "...",
    "start": "ISO8601+09:00",
    "end": "ISO8601+09:00",
    "description": ""
  }},
  "spoken": "修正後の確認をリン子口調で1文"
}}
"""
    data = generate_json(prompt)
    if not isinstance(data, dict) or not data.get("ready"):
        return None
    draft = data.get("draft")
    if not isinstance(draft, dict):
        return None
    return {"draft": draft, "spoken": (data.get("spoken") or "").strip() or _format_spoken_summary(draft)}


async def create_google_event(user_id: int, draft: dict[str, Any], db) -> tuple[bool, str, dict[str, Any]]:
    """Google Calendar にイベントを作成。戻り値: ok, message, extra"""
    from sqlalchemy import select

    from app.models import UserGoogleToken
    from app.routers.auth_google import GOOGLE_SCOPE, _sync_user_calendar_events_cache

    result = await db.execute(select(UserGoogleToken).where(UserGoogleToken.user_id == user_id))
    row = result.scalar_one_or_none()
    if not row:
        return False, "Google カレンダーがまだ連携されていません。パーソナルボードから連携してください。", {}

    summary = (draft.get("summary") or "予定").strip()
    start = (draft.get("start") or "").strip()
    end = (draft.get("end") or "").strip()
    if not start or not end:
        return False, "日時が不正です。もう一度教えてください。", {}

    def _insert():
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from app.config import settings

        creds = Credentials(
            token=row.access_token,
            refresh_token=row.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_calendar_client_id,
            client_secret=settings.google_calendar_client_secret,
            scopes=GOOGLE_SCOPE,
        )
        if row.token_expiry and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        service = build("calendar", "v3", credentials=creds)
        body = {
            "summary": summary,
            "description": (draft.get("description") or "").strip(),
            "start": {"dateTime": start, "timeZone": "Asia/Tokyo"},
            "end": {"dateTime": end, "timeZone": "Asia/Tokyo"},
        }
        return service.events().insert(calendarId="primary", body=body).execute()

    import asyncio

    try:
        event = await asyncio.to_thread(_insert)
    except Exception as e:
        err = str(e)
        logger.warning("[brainstorm_calendar] insert failed user_id=%s: %s", user_id, err[:200])
        if "insufficient" in err.lower() or "scope" in err.lower() or "403" in err:
            return (
                False,
                "カレンダーの書き込み権限がありません。Google 連携をやり直してください（書き込み許可が必要です）。",
                {},
            )
        return False, "カレンダーへの登録に失敗しました。もう一度お試しください。", {}

    try:
        await _sync_user_calendar_events_cache(user_id, db)
    except Exception:
        pass
    return True, f"入れました。「{summary}」です。", {"event_id": event.get("id"), "html_link": event.get("htmlLink")}


def handle_new_calendar_intent(user_id: int, messages: list[dict[str, str]]) -> dict[str, Any]:
    """新規依頼。提案作成 or 質問文を返す。"""
    extracted = extract_calendar_from_conversation(messages)
    if not extracted or extracted.get("intent") != "calendar_create":
        return {"mode": "chat"}
    if not extracted.get("ready"):
        clarify = (extracted.get("clarify") or "日時を教えてもらえますか？").strip()
        missing = extracted.get("missing") or []
        if missing and "start" in missing and not clarify:
            clarify = "何日の、何時からですか？"
        return {"mode": "clarify", "spoken": clarify}
    draft = extracted.get("draft")
    if not isinstance(draft, dict) or not draft.get("start") or not draft.get("end"):
        return {"mode": "clarify", "spoken": "日時をもう少し教えてもらえますか？"}
    p = create_proposal(user_id, draft)
    return {"mode": "proposal", "proposal": p, "spoken": _format_spoken_summary(p.draft)}


def handle_pending(user_id: int, proposal_id: str, user_text: str) -> dict[str, Any]:
    p = get_proposal(proposal_id, user_id)
    if p is None:
        return {"mode": "expired", "spoken": "確認の期限が切れました。もう一度予定を教えてください。"}
    kind = interpret_pending_message(user_text)
    if kind == "cancel":
        delete_proposal(proposal_id, user_id)
        return {"mode": "cancelled", "spoken": "わかりました。登録はしません。"}
    if kind == "confirm":
        return {"mode": "confirm", "proposal": p}
    revised = revise_draft(p, user_text)
    if not revised:
        return {"mode": "clarify", "spoken": "すみません、修正内容が分かりませんでした。もう一度教えてください。"}
    updated = update_draft(proposal_id, user_id, revised["draft"])
    if updated is None:
        return {"mode": "expired", "spoken": "確認の期限が切れました。もう一度予定を教えてください。"}
    return {"mode": "proposal", "proposal": updated, "spoken": revised.get("spoken") or _format_spoken_summary(updated.draft)}
