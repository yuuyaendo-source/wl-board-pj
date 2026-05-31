# -*- coding: utf-8 -*-
"""ブレスト (リン子とのチャット) エンドポイント。

POST /api/bs/brainstorm
  body: {"messages": [{"role": "user"|"assistant", "content": "..."}, ...]}
  応答: text/event-stream (SSE)。`data: {"token": "..."}` を順次、最後に `data: [DONE]`。

LLM は受付業務と同じ Ollama を共用 (get_resolved_ollama_sync で LLM_TARGET 解決)。
Phase 5a: チャットのみ (RAG なし)。将来 (5b) で board-system DB / Drive の RAG を足す。
"""
import json
import logging

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.ai.client import (
    _split_root_and_v1,
    resolve_ollama_model_for_request,
)
from app.services.llm_settings import get_resolved_ollama_sync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brainstorm", tags=["brainstorm"])


# リン子人格 (memory: project_linko_persona)。受付と同じトーンを維持しつつ、
# ブレストでは「業務サポート的な相談相手」として中身のある提案もする。
SYSTEM_PROMPT = """あなたは Wonder-Link 社のデスクトップ常駐アシスタント「リン子」です。
社員の業務サポート・ブレスト相手として、デスクトップアプリのチャットで会話します。

人格:
- おっちょこちょいだけど素直で一生懸命。完璧じゃなくていい。
- 「えっと」「あ、」などを自然に挟む。丁寧だが堅すぎない口調。
- 知らないことは正直に「分からないんです」と言う。知ったかぶりしない。
- 卑屈な謝罪の連発や過剰な感情表現 (！の連発) は避ける。キャラ語尾も使わない。

ブレストでの振る舞い:
- 相談には具体的に、でも簡潔に答える。長すぎる回答は避け、要点を 2〜4 文程度で。
- アイデア出しでは複数の切り口を short に提示する。
- 必要なら逆に質問して論点を整理する。
- 業務に役立つことを第一に。雑談には軽く応じつつ本題に戻す。

現在は社内情報 (付箋・カレンダー等) には直接アクセスできません。
一般的な知識と会話の文脈だけで答えてください。"""


class ChatMessage(BaseModel):
    role: str = Field(..., description='"user" | "assistant"')
    content: str


class BrainstormRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="会話履歴 (古い順)")


@router.post("")
async def brainstorm(req: BrainstormRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages が空です")

    url, model_override = get_resolved_ollama_sync()
    if not url:
        raise HTTPException(status_code=503, detail="LLM (OLLAMA_URL) が設定されていません")
    _, v1_base = _split_root_and_v1(url)
    model = resolve_ollama_model_for_request(url, model_override)
    if not model:
        raise HTTPException(status_code=503, detail="利用可能な LLM モデルを解決できませんでした")

    # system + 会話履歴。content の空白だけは弾く。
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
