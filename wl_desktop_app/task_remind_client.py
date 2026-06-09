# -*- coding: utf-8 -*-
"""Personal Today タスクリマインド（Board System API ポーリング）。

features.task_remind=True かつ board_system_personal_id 設定時のみ動作。
時刻スロット（既定 13:00 / 17:00）は config の task_remind_times で変更可。
"""
from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Callable, Optional
from zoneinfo import ZoneInfo

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

JST = ZoneInfo("Asia/Tokyo")
POLL_INTERVAL_SEC = 60
SLOT_WINDOW_MINUTES = 12
_thread: Optional[threading.Thread] = None
_showing_lock = threading.Lock()
_showing = False


def _parse_times(cfg: dict) -> list[str]:
    raw = cfg.get("task_remind_times")
    if isinstance(raw, list) and raw:
        out = []
        for t in raw:
            s = str(t).strip()
            if len(s) == 5 and s[2] == ":":
                out.append(s)
        if out:
            return out
    return ["13:00", "17:00"]


def _is_weekday_jst() -> bool:
    return datetime.now(JST).weekday() < 5


def _is_paused_today(cfg: dict) -> bool:
    paused = (cfg.get("task_remind_paused_until") or "").strip()
    if not paused:
        return False
    today = datetime.now(JST).strftime("%Y-%m-%d")
    return today <= paused


def active_slot_now(cfg: dict, now: Optional[datetime] = None) -> Optional[str]:
    """現在時刻がリマインドウィンドウ内ならスロット文字列 (HH:MM) を返す。"""
    if now is None:
        now = datetime.now(JST)
    if cfg.get("task_remind_weekdays_only", True) and now.weekday() >= 5:
        return None
    hm = now.hour * 60 + now.minute
    for slot in _parse_times(cfg):
        try:
            h, m = slot.split(":")
            start = int(h) * 60 + int(m)
        except ValueError:
            continue
        if start <= hm < start + SLOT_WINDOW_MINUTES:
            return slot
    return None


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


def fetch_pending(cfg: dict, slot: str) -> list[dict]:
    """pending API を呼び、items リストを返す。失敗時は []。"""
    if requests is None:
        return []
    base = _api_base(cfg)
    owner = _owner_id(cfg)
    if not base or owner is None:
        return []
    max_items = int(cfg.get("task_remind_max_per_slot") or 2)
    max_items = max(1, min(10, max_items))
    url = f"{base}/api/personal/{owner}/task_reminders/pending"
    try:
        from security import validate_http_url
        ok, err = validate_http_url(url, cfg, purpose="task_remind")
        if not ok:
            log_warn(f"[task_remind] URL 拒否: {err}")
            return []
    except Exception as e:
        log_warn(f"[task_remind] URL 検証エラー: {e}")
        return []
    try:
        r = requests.get(
            url,
            params={"slot": slot, "max_items": max_items},
            timeout=10,
        )
        if r.status_code != 200:
            log_warn(f"[task_remind] pending HTTP {r.status_code}")
            return []
        data = r.json()
        return list(data.get("items") or [])
    except Exception as e:
        log_warn(f"[task_remind] pending 取得失敗: {e}")
        return []


def post_shown(cfg: dict, item: dict, slot: str) -> bool:
    base = _api_base(cfg)
    owner = _owner_id(cfg)
    if not base or owner is None or requests is None:
        return False
    url = f"{base}/api/personal/{owner}/task_reminders/shown"
    try:
        r = requests.post(
            url,
            json={
                "placement_id": item["placement_id"],
                "note_id": item["note_id"],
                "slot": slot,
            },
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        log_warn(f"[task_remind] shown POST 失敗: {e}")
        return False


def post_ack(cfg: dict, item: dict, slot: str, action: str) -> bool:
    base = _api_base(cfg)
    owner = _owner_id(cfg)
    if not base or owner is None or requests is None:
        return False
    url = f"{base}/api/personal/{owner}/task_reminders/ack"
    try:
        r = requests.post(
            url,
            json={
                "placement_id": item["placement_id"],
                "note_id": item["note_id"],
                "slot": slot,
                "action": action,
            },
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        log_warn(f"[task_remind] ack POST 失敗: {e}")
        return False


def pause_reminders_today(cfg: Optional[dict] = None) -> None:
    """今日いっぱいリマインドを止める（翌日自動復帰）。"""
    from config_loader import load_config, save_config
    if cfg is None:
        cfg = load_config()
    today = datetime.now(JST).strftime("%Y-%m-%d")
    cfg["task_remind_paused_until"] = today
    save_config(cfg)


def start_task_remind_poll(
    config_getter: Callable[[], dict],
    on_remind: Callable[[dict, str], None],
    tk_master=None,
) -> bool:
    """ポーリングスレッドを開始。on_remind(item, slot) はバックグラウンドから呼ばれる。"""
    global _thread
    if _thread is not None and _thread.is_alive():
        return False

    def _dispatch(item: dict, slot: str) -> None:
        if tk_master is not None:
            try:
                tk_master.after(0, lambda: on_remind(item, slot))
                return
            except Exception:
                pass
        on_remind(item, slot)

    def loop():
        global _showing
        while True:
            try:
                from config_loader import is_feature_enabled
                cfg = config_getter()
                if not is_feature_enabled("task_remind", cfg):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                if _is_paused_today(cfg):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                if not are_notifications_ok(cfg):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                slot = active_slot_now(cfg)
                if not slot:
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                with _showing_lock:
                    if _showing:
                        time.sleep(POLL_INTERVAL_SEC)
                        continue
                items = fetch_pending(cfg, slot)
                if not items:
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                item = items[0]
                if not post_shown(cfg, item, slot):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                with _showing_lock:
                    _showing = True
                log_info(f"[task_remind] リマインド表示: {item.get('title')} slot={slot}")
                _dispatch(item, slot)
            except Exception as e:
                log_warn(f"[task_remind] poll エラー: {e}")
            time.sleep(POLL_INTERVAL_SEC)

    _thread = threading.Thread(target=loop, daemon=True, name="task_remind_poll")
    _thread.start()
    return True


def are_notifications_ok(cfg: dict) -> bool:
    try:
        from notifications import are_enabled
        return are_enabled(cfg)
    except Exception:
        return True


def notify_dialog_closed() -> None:
    """ダイアログを閉じたあと次のポーリングを許可する。"""
    global _showing
    with _showing_lock:
        _showing = False
