# -*- coding: utf-8 -*-
"""AIボード等のURLへ接続できるか簡易チェック。"""
import requests

TIMEOUT_SEC = 2


def is_reachable(url: str) -> bool:
    """指定URLに接続できるか（GETで2秒タイムアウト）。"""
    if not url:
        return False
    try:
        from security import validate_http_url
        ok, _ = validate_http_url(url, purpose="health_check")
        if not ok:
            return False
    except Exception:
        return False
    try:
        r = requests.get(url.rstrip("/") + "/", timeout=TIMEOUT_SEC)
        return r.status_code < 500
    except Exception:
        return False
