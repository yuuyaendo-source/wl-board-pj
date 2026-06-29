# -*- coding: utf-8 -*-
"""社内ネットワーク（CATO/VPN）到達確認。

Windows GUI アプリから ping.exe を subprocess するとコマンドプロンプトが
点滅するため、HTTP プローブのみを使う。
"""
from __future__ import annotations

import time
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

_PROBE_CACHE: Optional[tuple[float, bool]] = None
_PROBE_CACHE_TTL_SEC = 10
_UNREACHABLE_BACKOFF_SEC = 30


def resolve_probe_url(cfg: dict) -> Optional[str]:
    """ネットワーク到達確認に使う URL。未設定なら None（チェックしない）。"""
    if not isinstance(cfg, dict):
        return None
    explicit = (cfg.get("update_network_check_url") or "").strip()
    if explicit:
        return explicit
    update_json = (cfg.get("update_check_url") or "").strip()
    if update_json:
        return update_json
    bs = (cfg.get("board_system_url") or "").strip().rstrip("/")
    if bs:
        return f"{bs}/health" if not bs.endswith("/health") else bs
    linko = (cfg.get("linko_server_url") or "").strip().rstrip("/")
    if linko:
        return f"{linko}/api/v2/health"
    return None


def is_network_ready(cfg: dict | None = None, *, timeout: int = 5, use_cache: bool = True) -> bool:
    """プローブ URL へ HTTP GET できれば True。URL 未設定時は True（従来どおり動作）。"""
    global _PROBE_CACHE
    if cfg is None:
        from config_loader import load_config
        cfg = load_config()
    probe = resolve_probe_url(cfg)
    if not probe:
        return True
    if requests is None:
        return True
    now = time.monotonic()
    if use_cache and _PROBE_CACHE is not None:
        cached_at, cached_ok = _PROBE_CACHE
        if now - cached_at < _PROBE_CACHE_TTL_SEC:
            return cached_ok
    ok = _probe_http(probe, cfg, timeout)
    _PROBE_CACHE = (now, ok)
    return ok


def wait_for_network_ready(
    cfg: dict | None = None,
    interval_sec: int = 5,
    max_wait_sec: int = 180,
) -> bool:
    """プローブ URL が応答するまで待つ。タイムアウト時 False。"""
    if cfg is None:
        from config_loader import load_config
        cfg = load_config()
    probe = resolve_probe_url(cfg)
    if not probe:
        return True
    deadline = time.monotonic() + max(0, int(max_wait_sec))
    interval = max(1, int(interval_sec))
    while time.monotonic() < deadline:
        if is_network_ready(cfg, use_cache=False):
            _log(f"ネットワーク確立: {probe} へ到達確認")
            return True
        time.sleep(interval)
    _log(f"ネットワーク待機タイムアウト: {probe} へ {max_wait_sec}秒以内に到達不可")
    return False


def unreachable_backoff_sec(cfg: dict | None = None) -> int:
    """到達不可時にポーリングスレッドが sleep する秒数。"""
    if cfg is None:
        from config_loader import load_config
        cfg = load_config()
    raw = cfg.get("network_unreachable_backoff_sec")
    try:
        n = int(raw)
        return max(5, min(300, n))
    except (TypeError, ValueError):
        return _UNREACHABLE_BACKOFF_SEC


def _probe_http(url: str, cfg: dict, timeout: int) -> bool:
    if requests is None:
        return True
    try:
        from security import validate_http_url
        ok, _ = validate_http_url(url, cfg, purpose="network_probe")
        if not ok:
            return False
    except Exception:
        return False
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False


def _log(msg: str) -> None:
    try:
        from app_log import log_info
        log_info(msg)
    except Exception:
        pass
