# -*- coding: utf-8 -*-
"""Google カレンダー予定のリマインド（Board System API ポーリング）。

features.calendar_notify=True かつ board_system_personal_id 設定時のみ。
Google 未連携時は API が空を返し、クライアントは何もしない。
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from app_log import log_info, log_warn
except Exception:
    def log_info(msg: str) -> None:
        print(msg, flush=True)

    def log_warn(msg: str) -> None:
        print(msg, flush=True)

POLL_INTERVAL_SEC = 60
DEFAULT_MINUTES_BEFORE = 15


def calendar_remind_minutes(cfg: dict) -> int:
    from config_loader import normalize_calendar_remind_minutes

    return normalize_calendar_remind_minutes(
        cfg.get("calendar_remind_minutes_before") or DEFAULT_MINUTES_BEFORE
    )
_thread: Optional[threading.Thread] = None
_busy_lock = threading.Lock()
_busy = False


def _api_base(cfg: dict) -> str:
    from config_loader import get_effective_board_system_url
    return (get_effective_board_system_url(cfg) or "").rstrip("/")


def _owner_id(cfg: dict) -> Optional[int]:
    pid = (cfg.get("board_system_personal_id") or "").strip()
    if not pid:
        return None
    try:
        return int(pid)
    except ValueError:
        return None


def fetch_pending(cfg: dict, minutes_before: int = DEFAULT_MINUTES_BEFORE) -> list[dict]:
    if requests is None:
        return []
    base = _api_base(cfg)
    owner = _owner_id(cfg)
    if not base or owner is None:
        return []
    url = f"{base}/api/personal/{owner}/calendar_reminders/pending"
    try:
        from security import validate_http_url
        ok, err = validate_http_url(url, cfg, purpose="calendar_remind")
        if not ok:
            log_warn(f"[calendar_notify] URL 拒否: {err}")
            return []
    except Exception as e:
        log_warn(f"[calendar_notify] URL 検証エラー: {e}")
        return []
    try:
        r = requests.get(url, params={"minutes_before": minutes_before}, timeout=15)
        if r.status_code != 200:
            log_warn(f"[calendar_notify] pending HTTP {r.status_code}: {r.text[:200]}")
            return []
        return list((r.json() or {}).get("items") or [])
    except Exception as e:
        log_warn(f"[calendar_notify] pending 取得失敗: {e}")
        return []


def post_shown(cfg: dict, item: dict, minutes_before: int = DEFAULT_MINUTES_BEFORE) -> bool:
    base = _api_base(cfg)
    owner = _owner_id(cfg)
    if not base or owner is None or requests is None:
        return False
    url = f"{base}/api/personal/{owner}/calendar_reminders/shown"
    try:
        r = requests.post(
            url,
            params={"minutes_before": minutes_before},
            json={
                "event_id": item["event_id"],
                "event_start": item.get("start") or "",
            },
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        log_warn(f"[calendar_notify] shown POST 失敗: {e}")
        return False


def start_calendar_notify_poll(
    on_remind: Callable[[list[dict]], None],
    tk_master=None,
) -> bool:
    global _thread
    if _thread is not None and _thread.is_alive():
        return False

    def _dispatch(items: list[dict]) -> None:
        if tk_master is not None:
            try:
                tk_master.after(0, lambda its=items: on_remind(its))
                return
            except Exception:
                pass
        on_remind(items)

    def loop():
        global _busy
        while True:
            try:
                from config_loader import is_feature_enabled, load_config
                from task_remind_client import are_notifications_ok
                cfg = load_config()
                if not is_feature_enabled("calendar_notify", cfg):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                if _owner_id(cfg) is None:
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                if not are_notifications_ok(cfg):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                with _busy_lock:
                    if _busy:
                        time.sleep(POLL_INTERVAL_SEC)
                        continue
                minutes = calendar_remind_minutes(cfg)
                items = fetch_pending(cfg, minutes_before=minutes)
                if not items:
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                with _busy_lock:
                    _busy = True
                log_info(
                    f"[calendar_notify] リマインド ({len(items)}件): "
                    + ", ".join((it.get("title") or "?")[:20] for it in items[:3])
                )
                _dispatch(items)
            except Exception as e:
                log_warn(f"[calendar_notify] poll エラー: {e}")
            time.sleep(POLL_INTERVAL_SEC)

    _thread = threading.Thread(target=loop, daemon=True, name="calendar_notify_poll")
    _thread.start()
    return True


def notify_delivery_done() -> None:
    global _busy
    with _busy_lock:
        _busy = False
