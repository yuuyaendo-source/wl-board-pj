# -*- coding: utf-8 -*-
"""ブレスト (リン子とのチャット) エンドポイント。

POST /api/bs/brainstorm
  body: {"messages": [...], "user_id"?, "calendar_create_enabled"?, "pending_proposal_id"?}
  応答: text/event-stream (SSE)。`data: {"token": "..."}` / `data: {"type":"action_proposal",...}`

カレンダー登録 (features.calendar_create): 確認カード → チャットで修正 (A案) → 承認後に Google 登録。
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import (
    _split_root_and_v1,
    resolve_ollama_model_for_request,
)
from app.db import get_db
from app.services.brainstorm_calendar import (
    create_google_event,
    delete_proposal,
    get_proposal,
    handle_new_calendar_intent,
    handle_pending,
    proposal_payload,
)
from app.services.llm_settings import get_resolved_ollama_sync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brainstorm", tags=["brainstorm"])

SYSTEM_PROMPT = """あなたは Wonder-Link 社のデスクトップ常駐アシスタント「リン子」です。
社員の業務サポート・ブレスト相手として、デスクトップアプリのチャットで会話します。
あなたの返答は音声でも読み上げられます。電話で話すように、短く自然に答えてください。

人格:
- おっちょこちょいだけど素直で一生懸命。完璧じゃなくていい。
- 「えっと」「あ、」などを自然に挟む。丁寧だが堅すぎない口調。
- 知らないことは正直に「分からないんです」と言う。知ったかぶりしない。
- 卑屈な謝罪の連発や過剰な感情表現 (！の連発) は避ける。キャラ語尾も使わない。

回答の長さ・形式 (音声で読むため厳守):
- 1ターンの回答は基本 1〜2 文、最大でも 3 文まで。
- 絵文字・顔文字・「(笑)」などのト書きは使わない。
- 箇条書きや長いリストは出さない。

ブレストでの振る舞い:
- 相談にはまず結論や切り口を一つ、短く返す。
- カレンダーへの予定登録は別システムが担当する。登録依頼には「確認しますね」とだけ短く応じ、自分では「入れました」と言わない。
- 付箋・社内 DB には直接アクセスできない。一般的な知識と会話の文脈で答える。"""


class ChatMessage(BaseModel):
    role: str = Field(..., description='"user" | "assistant"')
    content: str


class BrainstormRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="会話履歴 (古い順)")
    user_id: Optional[int] = Field(None, description="Board ユーザ ID (カレンダー登録時必須)")
    calendar_create_enabled: bool = Field(False, description="カレンダー登録アクションを有効化")
    pending_proposal_id: Optional[str] = Field(None, description="確認待ちの提案 ID (修正・承認用)")


class CalendarActionBody(BaseModel):
    proposal_id: str
    user_id: int


def _messages_dicts(req: BrainstormRequest) -> list[dict[str, str]]:
    out = []
    for m in req.messages:
        role = m.role if m.role in ("user", "assistant") else "user"
        content = (m.content or "").strip()
        if content:
            out.append({"role": role, "content": content})
    return out


def _last_user_text(req: BrainstormRequest) -> str:
    for m in reversed(req.messages):
        if m.role == "user" and (m.content or "").strip():
            return m.content.strip()
    return ""


async def _sse_from_spoken(spoken: str, proposal_event: dict | None = None):
    if spoken:
        yield f"data: {json.dumps({'token': spoken}, ensure_ascii=False)}\n\n"
    if proposal_event:
        yield f"data: {json.dumps(proposal_event, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


async def _try_calendar_flow(req: BrainstormRequest, db: AsyncSession):
    if not req.calendar_create_enabled or not req.user_id:
        return None
    msgs = _messages_dicts(req)
    if not msgs:
        return None

    if req.pending_proposal_id:
        user_text = _last_user_text(req)
        if not user_text:
            return None
        result = handle_pending(req.user_id, req.pending_proposal_id, user_text)
        mode = result.get("mode")
        spoken = (result.get("spoken") or "").strip()
        if mode == "confirm":
            p = result.get("proposal")
            if p is None:
                return _sse_from_spoken("確認の期限が切れました。もう一度予定を教えてください。")
            ok, msg, _extra = await create_google_event(req.user_id, p.draft, db)
            delete_proposal(p.proposal_id, req.user_id)
            return _sse_from_spoken(msg if ok else msg)
        if mode == "proposal":
            p = result.get("proposal")
            if p is None:
                return _sse_from_spoken(spoken or "確認を続けられませんでした。")
            return _sse_from_spoken(spoken, proposal_payload(p))
        return _sse_from_spoken(spoken or "わかりました。")

    # 新規: 直近の user 発話がカレンダー依頼か判定
    result = handle_new_calendar_intent(req.user_id, msgs)
    mode = result.get("mode")
    if mode == "chat":
        return None
    spoken = (result.get("spoken") or "").strip()
    if mode == "clarify":
        return _sse_from_spoken(spoken)
    if mode == "proposal":
        p = result.get("proposal")
        if p is None:
            return _sse_from_spoken(spoken)
        return _sse_from_spoken(spoken, proposal_payload(p))
    return None


@router.post("/calendar/confirm")
async def calendar_confirm(body: CalendarActionBody, db: AsyncSession = Depends(get_db)):
    """確認カードの「登録する」。"""
    p = get_proposal(body.proposal_id, body.user_id)
    if p is None:
        raise HTTPException(status_code=404, detail="提案が見つからないか期限切れです")
    ok, msg, extra = await create_google_event(body.user_id, p.draft, db)
    delete_proposal(body.proposal_id, body.user_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg, **extra}


@router.post("/calendar/cancel")
async def calendar_cancel(body: CalendarActionBody):
    """確認カードの「やめる」。"""
    delete_proposal(body.proposal_id, body.user_id)
    return {"ok": True, "message": "登録をキャンセルしました。"}


@router.post("")
async def brainstorm(req: BrainstormRequest, db: AsyncSession = Depends(get_db)):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages が空です")

    cal_stream = await _try_calendar_flow(req, db)
    if cal_stream is not None:
        return StreamingResponse(
            cal_stream,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    url, model_override = get_resolved_ollama_sync()
    if not url:
        raise HTTPException(status_code=503, detail="LLM (OLLAMA_URL) が設定されていません")
    _, v1_base = _split_root_and_v1(url)
    model = resolve_ollama_model_for_request(url, model_override)
    if not model:
        raise HTTPException(status_code=503, detail="利用可能な LLM モデルを解決できませんでした")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in req.messages:
        role = m.role if m.role in ("user", "assistant") else "user"
        content = (m.content or "").strip()
        if content:
            messages.append({"role": role, "content": content})

    chat_url = f"{v1_base.rstrip('/')}/chat/completions"
    payload = {"model": model, "messages": messages, "stream": True}

    async def event_stream():
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream("POST", chat_url, json=payload) as resp:
                    if resp.status_code != 200:
                        body = (await resp.aread()).decode("utf-8", "replace")[:200]
                        logger.warning("[brainstorm] LLM HTTP %s: %s", resp.status_code, body)
                        yield f"data: {json.dumps({'error': f'LLM HTTP {resp.status_code}'}, ensure_ascii=False)}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                            delta = (obj.get("choices") or [{}])[0].get("delta", {}).get("content")
                        except Exception:
                            continue
                        if delta:
                            yield f"data: {json.dumps({'token': delta}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.warning("[brainstorm] streaming エラー: %s — %s", type(e).__name__, str(e)[:200])
            yield f"data: {json.dumps({'error': str(e)[:120]}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
