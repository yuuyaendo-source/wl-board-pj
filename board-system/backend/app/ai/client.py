# -*- coding: utf-8 -*-
"""
ローカル LLM（Ollama）呼び出し。OpenAI 互換 API（/v1/chat/completions）を使用。
OLLAMA_URL 未設定時は None を返す。

※ Gemini は使用しない（ローカル LLM 利用のためコメントアウト）。
"""
import json
import logging
import re

import requests

from app.config import settings

logger = logging.getLogger(__name__)
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def generate_json(prompt: str) -> dict | None:
    """
    プロンプトを送り、応答から JSON を1つ抽出して dict で返す。
    失敗時・OLLAMA_URL 未設定時は None。
    """
    if not settings.ollama_url:
        return None
    url = f"{settings.ollama_url.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.ollama_model,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        sess = _get_session()
        r = sess.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            logger.warning("[Rinko AI] Ollama 応答に choices がありません")
            return None
        content = (choices[0].get("message") or {}).get("content")
        if not content or not (text := str(content).strip()):
            logger.warning("[Rinko AI] Ollama 応答が空でした")
            return None
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if m:
                text = m.group(1).strip()
        return json.loads(text)
    except requests.RequestException as e:
        logger.warning("[Rinko AI] Ollama API 呼び出しに失敗しました: %s — %s", type(e).__name__, str(e)[:300])
        return None
    except json.JSONDecodeError as e:
        logger.warning("[Rinko AI] Ollama 応答の JSON 解析に失敗しました: %s", str(e)[:200])
        return None
    except Exception as e:
        logger.warning("[Rinko AI] Ollama 呼び出しエラー: %s — %s", type(e).__name__, str(e)[:300])
        return None
