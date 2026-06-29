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

try:
    JST = ZoneInfo("Asia/Tokyo")
except Exception:
    # Windows 等で tzdata 未インストール時のフォールバック (UTC+9 固定)
    from datetime import timezone, timedelta
    JST = timezone(timedelta(hours=9))

POLL_INTERVAL_SEC = 30
SLOT_WINDOW_MINUTES = 15
_thread: Optional[threading.Thread] = None
_showing_lock = threading.Lock()
_showing = False


def _normalize_time(raw: str) -> Optional[str]:
    """'9:5' → '09:05'。不正なら None。"""
    s = (raw or "").strip()
    if not s or ":" not in s:
        return None
    parts = s.split(":", 1)
    try:
        h, m = int(parts[0]), int(parts[1])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    except ValueError:
        pass
    return None


def _parse_times(cfg: dict) -> list[str]:
    raw = cfg.get("task_remind_times")
    if isinstance(raw, list) and raw:
        out = []
        for t in raw:
            norm = _normalize_time(str(t))
            if norm:
                out.append(norm)
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


def _personal_api_url(cfg: dict, owner: int, suffix: str) -> str:
    """board_system_url ベースで personal API の URL を組み立てる。"""
    base = _api_base(cfg)
    return f"{base}/api/personal/{owner}/{suffix}"


LIST_SUMMARY_MESSAGE = "本日のタスクの進捗はいかがですか？"


def fetch_pending(cfg: dict, slot: str) -> tuple[list[dict], str]:
    """pending API を呼び、(items, summary) を返す。失敗時は ([], '')。"""
    if requests is None:
        return [], ""
    base = _api_base(cfg)
    owner = _owner_id(cfg)
    if not base or owner is None:
        return [], ""
    url = _personal_api_url(cfg, owner, "task_reminders/pending")
    try:
        from security import validate_http_url
        ok, err = validate_http_url(url, cfg, purpose="task_remind")
        if not ok:
            log_warn(f"[task_remind] URL 拒否: {err}")
            return [], ""
    except Exception as e:
        log_warn(f"[task_remind] URL 検証エラー: {e}")
        return [], ""
    try:
        r = requests.get(url, params={"slot": slot}, timeout=10)
        if r.status_code != 200:
            log_warn(f"[task_remind] pending HTTP {r.status_code}: {r.text[:200]}")
            return [], ""
        data = r.json()
        summary = (data.get("summary") or LIST_SUMMARY_MESSAGE).strip()
        return list(data.get("items") or []), summary
    except Exception as e:
        log_warn(f"[task_remind] pending 取得失敗: {e}")
        return [], ""


def _slots_shown_record(cfg: dict) -> dict:
    rec = cfg.get("task_remind_slots_shown")
    if not isinstance(rec, dict):
        return {"date": "", "slots": []}
    return {"date": str(rec.get("date") or ""), "slots": list(rec.get("slots") or [])}


def slot_already_shown_today(cfg: dict, slot: str) -> bool:
    """このスロットは今日すでにリマインド表示済みか（クライアント側ガード）。"""
    today = datetime.now(JST).strftime("%Y-%m-%d")
    rec = _slots_shown_record(cfg)
    return rec.get("date") == today and slot in rec.get("slots", [])


def mark_slot_shown_today(cfg: dict, slot: str) -> None:
    """スロット表示済みを config に記録（翌日・別スロットはリセット）。"""
    from config_loader import save_config
    today = datetime.now(JST).strftime("%Y-%m-%d")
    rec = _slots_shown_record(cfg)
    slots = list(rec.get("slots") or []) if rec.get("date") == today else []
    if slot not in slots:
        slots.append(slot)
    cfg["task_remind_slots_shown"] = {"date": today, "slots": slots}
    save_config(cfg)


def post_shown_slot(cfg: dict, slot: str) -> bool:
    """Today 全タスクをこのスロットで表示済みにする（サーバ側一括登録）。"""
    base = _api_base(cfg)
    owner = _owner_id(cfg)
    if not base or owner is None or requests is None:
        return False
    url = _personal_api_url(cfg, owner, "task_reminders/shown_slot")
    try:
        r = requests.post(url, json={"slot": slot}, timeout=15)
        return r.status_code == 200
    except Exception as e:
        log_warn(f"[task_remind] shown_slot POST 失敗: {e}")
        return False


def post_shown(cfg: dict, item: dict, slot: str) -> bool:
    base = _api_base(cfg)
    owner = _owner_id(cfg)
    if not base or owner is None or requests is None:
        return False
    url = _personal_api_url(cfg, owner, "task_reminders/shown")
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
    url = _personal_api_url(cfg, owner, "task_reminders/ack")
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
    on_remind: Callable[[list, str, str], None],
    tk_master=None,
) -> bool:
    """ポーリングスレッドを開始。on_remind(items, slot) はバックグラウンドから呼ばれる。"""
    global _thread
    if _thread is not None and _thread.is_alive():
        return False

    def _dispatch(items: list, slot: str, summary: str) -> None:
        if tk_master is not None:
            try:
                tk_master.after(0, lambda its=items, s=slot, sm=summary: on_remind(its, s, sm))
                return
            except Exception:
                pass
        on_remind(items, slot, summary)

    def loop():
        global _showing
        last_diag = ""
        while True:
            try:
                from config_loader import is_feature_enabled, load_config
                from network_readiness import is_network_ready, unreachable_backoff_sec
                cfg = load_config()
                if not is_network_ready(cfg):
                    time.sleep(unreachable_backoff_sec(cfg))
                    continue
                if not is_feature_enabled("task_remind", cfg):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                if _owner_id(cfg) is None:
                    diag = "board_system_personal_id 未設定 (パーソナルログインが必要)"
                    if diag != last_diag:
                        log_warn(f"[task_remind] {diag}")
                        last_diag = diag
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                if _is_paused_today(cfg):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                if not are_notifications_ok(cfg):
                    diag = "notifications_enabled=OFF (🔕)"
                    if diag != last_diag:
                        log_info(f"[task_remind] スキップ: {diag}")
                        last_diag = diag
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                slot = active_slot_now(cfg)
                if not slot:
                    last_diag = ""
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                if slot_already_shown_today(cfg, slot):
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                with _showing_lock:
                    if _showing:
                        time.sleep(POLL_INTERVAL_SEC)
                        continue
                items, summary = fetch_pending(cfg, slot)
                if not items:
                    diag = f"slot={slot} pending=0 (Today レーンに未通知タスクがあるか確認)"
                    if diag != last_diag:
                        log_info(f"[task_remind] {diag}")
                        last_diag = diag
                    time.sleep(POLL_INTERVAL_SEC)
                    continue
                with _showing_lock:
                    _showing = True
                last_diag = ""
                titles = ", ".join((it.get("title") or "?")[:24] for it in items[:3])
                if len(items) > 3:
                    titles += f" ほか{len(items) - 3}件"
                log_info(f"[task_remind] リマインド一覧表示 ({len(items)}件) slot={slot}: {titles}")
                _dispatch(items, slot, summary)
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
