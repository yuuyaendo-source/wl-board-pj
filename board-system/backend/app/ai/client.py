# -*- coding: utf-8 -*-
"""
Gemini 呼び出し。API キー未設定時は None を返す。
"""
import json
import re

from app.config import settings

_model = None


def _get_model():
    global _model
    if not settings.gemini_api_key:
        return None
    if _model is None:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel(settings.gemini_model)
    return _model


def generate_json(prompt: str) -> dict | None:
    """
    プロンプトを送り、応答から JSON を1つ抽出して dict で返す。
    失敗時・API キー未設定時は None。
    """
    model = _get_model()
    if not model:
        return None
    try:
        response = model.generate_content(prompt)
        if not response or not response.text:
            return None
        text = response.text.strip()
        # コードブロック除去
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if m:
                text = m.group(1).strip()
        return json.loads(text)
    except Exception:
        return None
