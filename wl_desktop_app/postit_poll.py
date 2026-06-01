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
        from security import validate_http_url
        ok, _ = validate_http_url(url, purpose="postit_poll")
        if not ok:
            return None
    except Exception:
        return None
    try:
        r = requests.get(url, timeout=POLL_TIMEOUT_SEC)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def fetch_summary_with_error(postit_board_url, board_id):
    """
    付箋ボードのサマリーを取得。戻り値は (summary_dict or None, error_message or None)。
    接続テスト用。失敗時は理由を返す。
    """
    url = _postit_summary_url(postit_board_url, board_id)
    try:
        from security import validate_http_url
        ok, err = validate_http_url(url, purpose="postit_poll")
        if not ok:
            return None, err or "URL が許可されていません"
    except Exception as e:
        return None, str(e)
    try:
        r = requests.get(url, timeout=POLL_TIMEOUT_SEC)
        if r.status_code == 200:
            return r.json(), None
        if r.status_code == 404:
            return None, "ボードが見つかりません(404)。board_id を確認してください。"
        return None, f"HTTP {r.status_code}"
    except requests.exceptions.Timeout:
        return None, "タイムアウト。URL・ネットワークを確認してください。"
    except requests.exceptions.ConnectionError as e:
        return None, "接続できません。wl-sticky-note.local に到達できるか確認してください。"
    except Exception as e:
        return None, str(e) or "不明なエラー"


def _get_poll_board_ids(cfg):
    """
    監視するボードIDのリストを返す。
    postit_board_ids が非空リストならそれを使い、否则は postit_board_id のみのリスト。
    """
    ids = cfg.get("postit_board_ids")
    if ids and isinstance(ids, list):
        return [str(bid).strip() for bid in ids if str(bid).strip()]
    single = (cfg.get("postit_board_id") or "").strip()
    return [single] if single else []


def start_postit_poll(config_getter, on_new_notes):
    """
    付箋ボードをポーリングするスレッドを開始する（daemon）。
    複数ボードIDを監視し、いずれかに新付箋があれば on_new_notes を呼ぶ。
    config_getter: 現在の設定 dict を返す関数（例: lambda: _config）
    on_new_notes: 新付箋検知時に呼ぶ関数 (summary_dict, board_open_url) => None
    """
    def poll_loop():
        # ボードIDごとに前回の notesCount / lastNoteAt を保持
        last_per_board = {}
        first_poll = True
        while True:
            raw = config_getter().get("postit_poll_interval_sec")
            interval = int(raw) if raw is not None else 60
            if interval <= 0:
                time.sleep(60)
                continue
            interval = max(10, interval)  # 最低10秒で過負荷を防ぐ
            if not first_poll:
                time.sleep(interval)
            first_poll = False
            cfg = config_getter()
            url = (cfg.get("postit_board_url") or "").strip().rstrip("/")
            board_ids = _get_poll_board_ids(cfg)
            if not url or not board_ids:
                continue
            for board_id in board_ids:
                summary = fetch_summary(url, board_id)
                if not summary:
                    continue
                notes_count = summary.get("notesCount", 0)
                note_at = summary.get("lastNoteAt", 0)
                prev = last_per_board.get(board_id, (None, None))
                last_count, last_at = prev
                if last_count is not None and (notes_count > last_count or note_at > (last_at or 0)):
                    board_open_url = _postit_board_open_url(url, board_id)
                    try:
                        on_new_notes(summary, board_open_url)
                    except Exception:
                        pass
                last_per_board[board_id] = (notes_count, note_at if note_at else last_at)

    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()
