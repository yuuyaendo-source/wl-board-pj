# -*- coding: utf-8 -*-
"""
Gemini 呼び出し（google-genai SDK）。API キー未設定時は None を返す。
"""
import json
import logging
import re

from app.config import settings

logger = logging.getLogger(__name__)
_client = None


def _get_client():
    global _client
    if not settings.gemini_api_key:
        return None
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=settings.gemini_api_key)
        logger.info("[Rinko AI] Gemini クライアント初期化: model=%s", settings.gemini_model)
    return _client


def generate_json(prompt: str) -> dict | None:
    """
    プロンプトを送り、応答から JSON を1つ抽出して dict で返す。
    失敗時・API キー未設定時は None。
    """
    client = _get_client()
    if not client:
        return None
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        text = getattr(response, "text", None) if response else None
        if not text and getattr(response, "candidates", None):
            cand = response.candidates[0] if response.candidates else None
            if cand and getattr(cand, "content", None) and getattr(cand.content, "parts", None) and cand.content.parts:
                text = getattr(cand.content.parts[0], "text", None)
        if not text or not (text := str(text).strip()):
            logger.warning("[Rinko AI] Gemini 応答が空でした")
            return None
        # コードブロック除去
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if m:
                text = m.group(1).strip()
        return json.loads(text)
    except Exception as e:
        msg = str(e).strip()
        if not msg and getattr(e, "message", None):
            msg = str(e.message).strip()
        if not msg and e.args:
            msg = str(e.args[0]).strip() if e.args else ""
        # APIキー無効は日本語で案内
        if msg and ("API key not valid" in msg or "API_KEY_INVALID" in msg):
            logger.warning(
                "[Rinko AI] GEMINI_API_KEY が無効です。"
                " https://aistudio.google.com/apikey でキーを確認・再発行し、"
                " board-system/backend/.env の GEMINI_API_KEY を更新してからサーバーを再起動してください。"
            )
        else:
            if msg and "AIza" in msg:
                detail = "(APIキー含むため省略)"
            else:
                detail = msg[:400] if msg else repr(e.args)[:300]
            logger.warning("[Rinko AI] Gemini API 呼び出しに失敗しました: %s — %s", type(e).__name__, detail)
        return None
