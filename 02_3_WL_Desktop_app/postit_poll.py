# -*- coding: utf-8 -*-
"""
付箋ボードの新付箋をポーリングし、変化時にコールバックする。
"""
import threading
import time
import requests

POLL_TIMEOUT_SEC = 5


def _postit_summary_url(postit_board_url, board_id):
    """GET /api/boards/:id/summary のURL。"""
    base = (postit_board_url or "").rstrip("/")
    return f"{base}/api/boards/{board_id}/summary"


def _postit_board_open_url(postit_board_url, board_id):
    """付箋ボードの該当ボードを開くURL。"""
    base = (postit_board_url or "").rstrip("/")
    return f"{base}/board/{board_id}"


def fetch_summary(postit_board_url, board_id):
    """付箋ボードのサマリーを取得。失敗時は None。"""
    url = _postit_summary_url(postit_board_url, board_id)
    try:
        r = requests.get(url, timeout=POLL_TIMEOUT_SEC)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def start_postit_poll(config_getter, on_new_notes):
    """
    付箋ボードをポーリングするスレッドを開始する（daemon）。
    config_getter: 現在の設定 dict を返す関数（例: lambda: _config）
    on_new_notes: 新付箋検知時に呼ぶ関数 (summary_dict, board_open_url) => None
    """
    def poll_loop():
        last_notes_count = None
        last_note_at = None
        first_poll = True
        while True:
            raw = config_getter().get("postit_poll_interval_sec")
            interval = int(raw) if raw is not None else 60
            if interval <= 0:
                time.sleep(60)
                continue
            interval = max(10, interval)  # 最低10秒で過負荷を防ぐ
            # 初回は即ポーリングして現状を把握し、2回目以降は interval ごとにポーリング
            if not first_poll:
                time.sleep(interval)
            first_poll = False
            cfg = config_getter()
            url = cfg.get("postit_board_url")
            board_id = (cfg.get("postit_board_id") or "").strip()
            if not url or not board_id:
                continue
            summary = fetch_summary(url, board_id)
            if not summary:
                continue
            notes_count = summary.get("notesCount", 0)
            note_at = summary.get("lastNoteAt", 0)
            if last_notes_count is not None and (notes_count > last_notes_count or note_at > (last_note_at or 0)):
                board_open_url = _postit_board_open_url(url, board_id)
                try:
                    on_new_notes(summary, board_open_url)
                except Exception:
                    pass
            last_notes_count = notes_count
            last_note_at = note_at if note_at else last_note_at

    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()
