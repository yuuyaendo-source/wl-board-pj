# -*- coding: utf-8 -*-
"""設定の読み込み（config.json + 環境変数）。"""
import os
import sys
import json

# exe 化（PyInstaller）時は exe と同じフォルダの config.json を読む
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")


def get_app_base_dir():
    """アプリのベースディレクトリ（exe 時は exe と同じフォルダ）。config.json・toast_icon の基準に使う。"""
    return _BASE_DIR


def _default_user_id():
    """デスクトップアプリ利用者を識別するID（未設定時はWindowsのUSERNAMEなど）。"""
    return os.environ.get("WLINKO_USER_ID") or os.environ.get("USERNAME", "")


def _get_defaults():
    return {
        "ai_board_url": "http://127.0.0.1:5000/",
        "postit_board_url": "http://127.0.0.1:3000/",
        "postit_board_id": "wl",  # トレイクリックで開くデフォルトボード。本番: wl（AI-Board連携先）
        "postit_board_ids": None,  # 新付箋を監視するボードIDのリスト。未設定時は postit_board_id のみ。例: ["wl", "board_2"]
        "user_id": _default_user_id(),
        "display_name": "",  # ミニポートから投稿したときに付箋に表示する名前（起動時に入力）
        "personal_path": "",  # Board System 利用時は未使用。レガシー AI ボード用パス（例: /asakawa）。空でよい。
        "open_personal_on_start": False,
        "avatar_visible": True,
        "sound_enabled": True,
        "toast_duration_sec": 8,
        "postit_poll_interval_sec": 60,  # 付箋ボードの新付箋チェック間隔（0で無効）
        "tray_click_action": "postit",  # トレイアイコンクリックで開く先: "postit" | "personal" | "last_notification"
        "toast_icon_path": "",  # トースト用アイコン（PNG/ICOの絶対パス。空ならデフォルトアイコン）
        "notifications_enabled": True,  # トースト通知の表示（アプリ内でオン/オフ。Windows の設定とは別）
        "mini_port_api_url": "https://wl-ai-board.internal.wonder-link.co.jp/board/wl",  # Rinko Mini-Port 送信先（この URL に POST で送信）
        "mini_port_taskboard_url": "https://wl-ai-board.internal.wonder-link.co.jp/boards/taskboard",  # リン子クリックで開く Task ボード URL
        "update_check_url": "",  # 更新チェック用 JSON の URL。空ならチェックしない。例: https://example.com/wonderlinko/latest.json
        "board_system_url": "",  # Board System のベース URL。設定時はメールログインでパーソナルボードを開ける
        "board_system_personal_id": "",  # メールログインで取得した user id。設定時は「パーソナルを開く」で Board System のパーソナルを開く
    }


DEFAULTS = _get_defaults()


def load_config():
    """config.json を読み、環境変数で上書き可能にする。"""
    cfg = dict(_get_defaults())
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    cfg["ai_board_url"] = os.environ.get("AI_BOARD_URL", cfg["ai_board_url"]).rstrip("/") + "/"
    cfg["postit_board_url"] = os.environ.get("POSTIT_BOARD_URL", cfg["postit_board_url"]).rstrip("/") + "/"
    cfg["mini_port_api_url"] = (os.environ.get("MINI_PORT_API_URL", cfg.get("mini_port_api_url", "https://wl-ai-board.internal.wonder-link.co.jp/board/wl"))).rstrip("/")
    cfg["mini_port_taskboard_url"] = (os.environ.get("MINI_PORT_TASKBOARD_URL", cfg.get("mini_port_taskboard_url", "https://wl-ai-board.internal.wonder-link.co.jp/boards/taskboard"))).strip()
    cfg["board_system_url"] = (os.environ.get("BOARD_SYSTEM_URL", cfg.get("board_system_url", "")) or "").strip().rstrip("/")
    return cfg


def save_config(cfg):
    """config.json に保存（AI_BOARD_URL 等は保存しない）。"""
    defaults = _get_defaults()
    out = {k: v for k, v in cfg.items() if k in defaults and k not in ("ai_board_url", "postit_board_url")}
    out["ai_board_url"] = cfg.get("ai_board_url", defaults["ai_board_url"])
    out["postit_board_url"] = cfg.get("postit_board_url", defaults["postit_board_url"])
    out["user_id"] = cfg.get("user_id", defaults["user_id"])
    out["display_name"] = cfg.get("display_name", defaults.get("display_name", ""))
    out["personal_path"] = cfg.get("personal_path", defaults.get("personal_path", ""))
    out["postit_board_id"] = cfg.get("postit_board_id", defaults.get("postit_board_id", ""))
    if cfg.get("postit_board_ids") is not None:
        out["postit_board_ids"] = cfg.get("postit_board_ids")
    out["postit_poll_interval_sec"] = cfg.get("postit_poll_interval_sec", defaults.get("postit_poll_interval_sec", 60))
    out["tray_click_action"] = cfg.get("tray_click_action", defaults.get("tray_click_action", "postit"))
    out["toast_icon_path"] = cfg.get("toast_icon_path", defaults.get("toast_icon_path", ""))
    out["notifications_enabled"] = cfg.get("notifications_enabled", defaults.get("notifications_enabled", True))
    out["mini_port_api_url"] = cfg.get("mini_port_api_url", defaults.get("mini_port_api_url", "https://wl-ai-board.internal.wonder-link.co.jp/board/wl"))
    out["mini_port_taskboard_url"] = cfg.get("mini_port_taskboard_url", defaults.get("mini_port_taskboard_url", "https://wl-ai-board.internal.wonder-link.co.jp/boards/taskboard"))
    out["update_check_url"] = cfg.get("update_check_url", defaults.get("update_check_url", ""))
    out["board_system_url"] = cfg.get("board_system_url", defaults.get("board_system_url", ""))
    out["board_system_personal_id"] = cfg.get("board_system_personal_id", defaults.get("board_system_personal_id", ""))
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def get_board_system_frontend_base(cfg=None):
    """Board System のフロントエンドベースURL。board_system_url が API ベース（/api/bs 付き）ならそれを除く。"""
    if cfg is None:
        cfg = load_config()
    base = (cfg.get("board_system_url") or "").strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/api/bs"):
        return base[:-len("/api/bs")].rstrip("/")
    return base


def get_board_system_personal_url(cfg=None):
    """各自の Board System パーソナルボードのURL。未設定時は None。"""
    if cfg is None:
        cfg = load_config()
    frontend = get_board_system_frontend_base(cfg)
    pid = (cfg.get("board_system_personal_id") or "").strip()
    if not frontend or not pid:
        return None
    return f"{frontend}/boards/personal/{pid}"


def get_effective_board_system_url(cfg=None):
    """Board System の API ベース URL。board_system_url が未設定のとき、mini_port_taskboard_url から推定する。"""
    if cfg is None:
        cfg = load_config()
    url = (cfg.get("board_system_url") or "").strip().rstrip("/")
    if url:
        return url
    task = (cfg.get("mini_port_taskboard_url") or "").strip()
    if not task:
        return ""
    import re
    base = re.sub(r"/boards/.*$", "", task).rstrip("/")
    return f"{base}/api/bs" if base else ""
