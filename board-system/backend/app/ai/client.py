# -*- coding: utf-8 -*-
"""
ローカル LLM（Ollama）呼び出し。OpenAI 互換 API（/v1/chat/completions）を使用。
OLLAMA_URL 未設定時は None を返す。

OLLAMA_MODEL 未設定時は /api/tags（modified_at 新しい順）→ 失敗時 /v1/models でモデル名を自動解決し、短時間キャッシュする。

※ Gemini は使用しない（ローカル LLM 利用のためコメントアウト）。
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from typing import Any

import requests

from app.config import settings

logger = logging.getLogger(__name__)
_session: requests.Session | None = None
_cache_lock = threading.Lock()
# v1 ベース URL（正規化済み） -> (model_id, expires_at_unix)
_model_cache: dict[str, tuple[str, float]] = {}


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def _split_root_and_v1(ollama_url: str) -> tuple[str, str]:
    """http://host:11434[/v1] -> (root, v1_base)。"""
    u = ollama_url.strip().rstrip("/")
    if u.endswith("/v1"):
        root = u[:-3].rstrip("/")
        v1 = u
    else:
        root = u
        v1 = f"{root}/v1"
    return root, v1


def _cache_key_v1(v1_base: str) -> str:
    return v1_base.rstrip("/")


def invalidate_resolved_model_cache(v1_base: str | None = None) -> None:
    """指定 v1 ベースのキャッシュを捨てる。None なら全消し。"""
    with _cache_lock:
        if v1_base is None:
            _model_cache.clear()
        else:
            _model_cache.pop(_cache_key_v1(v1_base), None)


def _pick_model_from_tags(payload: dict[str, Any]) -> str | None:
    models = payload.get("models") or []
    if not models:
        return None

    def sort_key(m: dict[str, Any]) -> tuple[str, str]:
        return (str(m.get("modified_at") or ""), str(m.get("name") or ""))

    sorted_m = sorted(models, key=sort_key, reverse=True)
    name = sorted_m[0].get("name")
    return str(name).strip() if name else None


def _pick_model_from_openai_models(payload: dict[str, Any]) -> str | None:
    data = payload.get("data") or []
    if not data:
        return None
    mid = data[0].get("id")
    return str(mid).strip() if mid else None


def _discover_model_id(root: str, v1_base: str, sess: requests.Session) -> str | None:
    """Ollama 上で利用可能なモデル名を1つ選ぶ。"""
    try:
        r = sess.get(f"{root}/api/tags", timeout=20)
        if r.ok:
            picked = _pick_model_from_tags(r.json())
            if picked:
                return picked
    except requests.RequestException as e:
        logger.debug("[Rinko AI] /api/tags 取得スキップ: %s", str(e)[:120])
    except (TypeError, ValueError, KeyError) as e:
        logger.debug("[Rinko AI] /api/tags 解析スキップ: %s", e)

    try:
        r = sess.get(f"{v1_base}/models", timeout=20)
        if r.ok:
            picked = _pick_model_from_openai_models(r.json())
            if picked:
                return picked
    except requests.RequestException as e:
        logger.debug("[Rinko AI] /v1/models 取得スキップ: %s", str(e)[:120])
    except (TypeError, ValueError, KeyError) as e:
        logger.debug("[Rinko AI] /v1/models 解析スキップ: %s", e)

    return None


def resolve_ollama_model_for_request(v1_base: str, *, force_refresh: bool = False) -> str | None:
    """
    chat/completions 用の model 文字列を返す。
    settings.ollama_model があればそれを優先。なければキャッシュまたは Ollama へ問い合わせ。
    """
    override = settings.ollama_model
    if override:
        return override

    root, v1_norm = _split_root_and_v1(settings.ollama_url or v1_base)
    key = _cache_key_v1(v1_norm)
    ttl = max(30, int(settings.ollama_model_auto_cache_ttl_seconds))
    now = time.monotonic()

    if not force_refresh:
        with _cache_lock:
            hit = _model_cache.get(key)
            if hit is not None:
                mid, exp = hit
                if now < exp:
                    return mid

    sess = _get_session()
    discovered = _discover_model_id(root, v1_norm, sess)
    if not discovered:
        logger.warning(
            "[Rinko AI] Ollama から利用可能モデルを取得できませんでした（%s の /api/tags と /v1/models を確認）",
            root,
        )
        return None

    with _cache_lock:
        _model_cache[key] = (discovered, now + ttl)
    logger.info("[Rinko AI] モデル自動解決: %s (endpoint=%s)", discovered, key)
    return discovered


def _post_chat_completions(v1_base: str, model: str, prompt: str, timeout: int) -> requests.Response:
    url = f"{v1_base.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    sess = _get_session()
    return sess.post(url, json=payload, timeout=timeout)


def generate_text(prompt: str) -> str | None:
    """
    プロンプトを送り、応答のテキスト（Markdown 等）をそのまま返す。
    OLLAMA_URL 未設定時は None。JSON 抽出は行わない。
    """
    if not settings.ollama_url:
        return None
    _, v1_base = _split_root_and_v1(settings.ollama_url)

    for attempt in range(2):
        model = resolve_ollama_model_for_request(v1_base, force_refresh=(attempt > 0))
        if not model:
            return None
        try:
            r = _post_chat_completions(v1_base, model, prompt, timeout=120)
            if r.status_code == 404:
                invalidate_resolved_model_cache(v1_base)
                if attempt == 0:
                    logger.warning(
                        "[Rinko AI] chat/completions が 404 — モデル解決を破棄して再試行します (model=%s)",
                        model,
                    )
                    continue
            r.raise_for_status()
            data = r.json()
            choices = data.get("choices") or []
            if not choices:
                return None
            content = (choices[0].get("message") or {}).get("content")
            if content is None:
                return None
            return str(content).strip() or None
        except requests.RequestException as e:
            logger.warning("[Rinko AI] Ollama API 呼び出しに失敗しました: %s — %s", type(e).__name__, str(e)[:300])
            return None
        except Exception as e:
            logger.warning("[Rinko AI] Ollama 呼び出しエラー: %s — %s", type(e).__name__, str(e)[:300])
            return None
    return None


def generate_json(prompt: str) -> dict | list | None:
    """
    プロンプトを送り、応答から JSON を1つ抽出して dict または list で返す。
    失敗時・OLLAMA_URL 未設定時は None。
    OLLAMA_URL は OpenAI 互換のベース（例: http://host:11434/v1）。末尾の /v1 が無い場合は自動で付与。
    404 の場合はモデル不一致の可能性 — 自動解決キャッシュを捨てて再試行する。
    """
    if not settings.ollama_url:
        return None
    _, v1_base = _split_root_and_v1(settings.ollama_url)

    for attempt in range(2):
        model = resolve_ollama_model_for_request(v1_base, force_refresh=(attempt > 0))
        if not model:
            return None
        try:
            r = _post_chat_completions(v1_base, model, prompt, timeout=60)
            if r.status_code == 404:
                invalidate_resolved_model_cache(v1_base)
                if attempt == 0:
                    logger.warning(
                        "[Rinko AI] Ollama API 404 — モデル解決を破棄して再試行します (model=%s)",
                        model,
                    )
                    continue
                logger.warning(
                    "[Rinko AI] Ollama API 404 — URL または OLLAMA_MODEL（固定時）を確認してください。"
                    " 自動解決時は ollama の /api/tags を確認してください。",
                )
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
            msg = str(e)[:300]
            if "404" not in msg:
                logger.warning("[Rinko AI] Ollama API 呼び出しに失敗しました: %s — %s", type(e).__name__, msg)
            return None
        except json.JSONDecodeError as e:
            logger.warning("[Rinko AI] Ollama 応答の JSON 解析に失敗しました: %s", str(e)[:200])
            return None
        except Exception as e:
            logger.warning("[Rinko AI] Ollama 呼び出しエラー: %s — %s", type(e).__name__, str(e)[:300])
            return None
    return None
