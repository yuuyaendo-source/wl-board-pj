# -*- coding: utf-8 -*-
"""AIボード等のURLへ接続できるか簡易チェック。"""
import requests

TIMEOUT_SEC = 2


def is_reachable(url: str) -> bool:
    """指定URLに接続できるか（GETで2秒タイムアウト）。"""
    if not url:
        return False
    try:
        r = requests.get(url.rstrip("/") + "/", timeout=TIMEOUT_SEC)
        return r.status_code < 500
    except Exception:
        return False
