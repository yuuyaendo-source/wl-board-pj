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

CALENDAR_REMIND_MINUTES_MIN = 1
CALENDAR_REMIND_MINUTES_MAX = 15
CALENDAR_REMIND_MINUTES_DEFAULT = 15


def normalize_calendar_remind_minutes(value) -> int:
    """カレンダーリマインドの「何分前」を 1〜15 に正規化する。"""
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = CALENDAR_REMIND_MINUTES_DEFAULT
    return max(CALENDAR_REMIND_MINUTES_MIN, min(CALENDAR_REMIND_MINUTES_MAX, n))


def get_app_base_dir():
    """アプリのベースディレクトリ（exe 時は exe と同じフォルダ）。config.json・toast_icon の基準に使う。"""
    return _BASE_DIR


def _default_user_id():
    """デスクトップアプリ利用者を識別するID（未設定時はWindowsのUSERNAMEなど）。"""
    return os.environ.get("WLINKO_USER_ID") or os.environ.get("USERNAME", "")


def _get_defaults():
    # 注意: msi に config.json はバンドルしない設計 (v3.1.4 以降)。
    # 新規インストール時はこれらの defaults でそのまま動作する必要があるので、
    # **本番想定の URL** を defaults として持つ。開発時は環境変数か個別 config.json で override。
    return {
        "ai_board_url": "https://wl-ai-board.internal.wonder-link.com/",
        "postit_board_url": "https://wl-ai-board.internal.wonder-link.com/",
        "postit_board_id": "wl",  # トレイクリックで開くデフォルトボード。本番: wl（AI-Board連携先）
        "postit_board_ids": None,  # 新付箋を監視するボードIDのリスト。未設定時は postit_board_id のみ。例: ["wl", "board_2"]
        "user_id": _default_user_id(),
        "display_name": "",  # ミニポートから投稿したときに付箋に表示する名前（起動時に入力）
        "personal_path": "",  # Board System 利用時は未使用。レガシー AI ボード用パス（例: /asakawa）。空でよい。
        "open_personal_on_start": False,
        # 旧 tray menu「アバターを表示」「音声ON」が読んでいた設定。v3.1.7 で UI 削除済 (dead)。
        # 既存ユーザ config.json にあれば残るが、コードは参照しない。
        "toast_duration_sec": 8,
        "postit_poll_interval_sec": 60,  # 付箋ボードの新付箋チェック間隔（0で無効）
        "tray_click_action": "postit",  # トレイアイコンクリックで開く先: "postit" | "personal" | "last_notification"
        "toast_icon_path": "",  # トースト用アイコン（PNG/ICOの絶対パス。空ならデフォルトアイコン）
        "notifications_enabled": True,  # 通知表示の総合スイッチ（トースト・吹き出し・来客通知・口パク。Windows OS 設定とは別）
        "mini_port_api_url": "https://wl-ai-board.internal.wonder-link.com/board/wl",  # Rinko Mini-Port 送信先（この URL に POST で送信）
        "mini_port_taskboard_url": "https://wl-ai-board.internal.wonder-link.com/boards/taskboard",  # リン子クリックで開く Task ボード URL
        "update_check_url": "https://wl-ai-board.internal.wonder-link.com/api/bs/desktop-app/latest.json",  # 更新チェック用 JSON の URL
        "update_network_check_host": "172.16.1.4",  # 起動時更新チェック前に Ping でネットワーク確立を待つ先。空なら待たない
        "update_network_check_interval_sec": 5,
        "update_network_check_max_wait_sec": 180,
        "board_system_url": "https://wl-ai-board.internal.wonder-link.com/api/bs",  # Board System のベース URL
        "board_system_personal_id": "",  # メールログインで取得した user id。設定時は「パーソナルを開く」で Board System のパーソナルを開く
        # linko-system (AI-Board) の Socket.IO サーバ URL。features.visitor_notify=True のときに接続して来客通知を受ける
        "linko_server_url": "https://linko-board.internal.wonder-link.com",
        # linko-system 管理 API 用（管理者 PC の config.json のみ。MSI 同梱しない）
        "linko_admin_token": "",
        # 機能フラグ。v2 で追加。基本 OFF でユーザーが任意で ON にする (詳細は docs/v2_拡張計画.md)。
        # taskbar_mode: ミニポートではなく通常 window としてタスクバーにも出す
        # linko_avatar: ミニポートにリン子の 2D アバター (表情切替) を表示
        # visitor_notify: 受付の来客通知 (visitor_arrived イベントを受信) をトーストで出す
        # visitor_notify_sound: visitor_notify が ON のとき、合わせて音声を再生する (opt-in)
        # brainstorm: チャット/音声でリン子と業務サポート的なブレストをする
        # brainstorm_voice: ブレスト応答をリン子の声 (GPT-SoVITS) で読み上げる (既定 ON)
        "features": {
            "taskbar_mode": False,
            "linko_avatar": False,
            "visitor_notify": False,
            "visitor_notify_sound": False,
            "brainstorm": False,
            "brainstorm_voice": True,
            "task_remind": False,
            "calendar_notify": False,
            "calendar_create": False,
            "remind_voice": False,
            "face_registry_manage": False,
            "face_registry_self": False,
        },
        # タスクリマインド（features.task_remind=ON 時）。Today レーンのみ。
        "task_remind_times": ["13:00", "17:00"],
        "task_remind_weekdays_only": True,
        "task_remind_slots_shown": {"date": "", "slots": []},  # 当日表示済みスロット（自動更新）
        "task_remind_paused_until": "",  # YYYY-MM-DD。当日までリマインド停止（空=停止なし）
        "calendar_remind_minutes_before": 15,  # カレンダー予定の何分前に通知するか
        # 外向き URL の許可ホスト (security.py)。未設定時は社内サフィックス + localhost のみ。
        "security": {
            "allowed_host_suffixes": [".internal.wonder-link.com"],
            "allowed_hosts": ["localhost", "127.0.0.1"],
            "allow_private_ips": False,
        },
    }


DEFAULTS = _get_defaults()


def load_config():
    """config.json を読み、環境変数で上書き可能にする。"""
    cfg = dict(_get_defaults())
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # features は辞書なので update でネスト構造が落ちないようにマージ
            if isinstance(loaded.get("features"), dict):
                merged_features = dict(cfg.get("features") or {})
                merged_features.update(loaded["features"])
                loaded["features"] = merged_features
            cfg.update(loaded)
        except Exception:
            pass
    cfg["ai_board_url"] = os.environ.get("AI_BOARD_URL", cfg["ai_board_url"]).rstrip("/") + "/"
    cfg["postit_board_url"] = os.environ.get("POSTIT_BOARD_URL", cfg["postit_board_url"]).rstrip("/") + "/"
    cfg["mini_port_api_url"] = (os.environ.get("MINI_PORT_API_URL", cfg.get("mini_port_api_url", "https://wl-ai-board.internal.wonder-link.com/board/wl"))).rstrip("/")
    cfg["mini_port_taskboard_url"] = (os.environ.get("MINI_PORT_TASKBOARD_URL", cfg.get("mini_port_taskboard_url", "https://wl-ai-board.internal.wonder-link.com/boards/taskboard"))).strip()
    cfg["board_system_url"] = (os.environ.get("BOARD_SYSTEM_URL", cfg.get("board_system_url", "")) or "").strip().rstrip("/")
    cfg["linko_server_url"] = (os.environ.get("LINKO_SERVER_URL", cfg.get("linko_server_url", "")) or "").strip().rstrip("/")
    cfg["linko_admin_token"] = (os.environ.get("LINKO_ADMIN_TOKEN", cfg.get("linko_admin_token", "")) or "").strip()
    try:
        from security import sanitize_config_urls
        sanitize_config_urls(cfg, _get_defaults())
    except Exception as e:
        print(f"[security] config URL sanitize skipped: {e}", flush=True)
    cfg["calendar_remind_minutes_before"] = normalize_calendar_remind_minutes(
        cfg.get("calendar_remind_minutes_before")
    )
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
    out["mini_port_api_url"] = cfg.get("mini_port_api_url", defaults.get("mini_port_api_url", "https://wl-ai-board.internal.wonder-link.com/board/wl"))
    out["mini_port_taskboard_url"] = cfg.get("mini_port_taskboard_url", defaults.get("mini_port_taskboard_url", "https://wl-ai-board.internal.wonder-link.com/boards/taskboard"))
    out["update_check_url"] = cfg.get("update_check_url", defaults.get("update_check_url", ""))
    out["update_network_check_host"] = cfg.get("update_network_check_host", defaults.get("update_network_check_host", ""))
    out["update_network_check_interval_sec"] = cfg.get("update_network_check_interval_sec", defaults.get("update_network_check_interval_sec", 5))
    out["update_network_check_max_wait_sec"] = cfg.get("update_network_check_max_wait_sec", defaults.get("update_network_check_max_wait_sec", 180))
    out["board_system_url"] = cfg.get("board_system_url", defaults.get("board_system_url", ""))
    out["board_system_personal_id"] = cfg.get("board_system_personal_id", defaults.get("board_system_personal_id", ""))
    out["linko_server_url"] = cfg.get("linko_server_url", defaults.get("linko_server_url", ""))
    out["linko_admin_token"] = cfg.get("linko_admin_token", defaults.get("linko_admin_token", ""))
    # features は辞書を丸ごと保存（未知キーも保つ）
    src_features = cfg.get("features") if isinstance(cfg.get("features"), dict) else {}
    out["features"] = {**(defaults.get("features") or {}), **src_features}
    out["task_remind_times"] = cfg.get("task_remind_times", defaults.get("task_remind_times", ["13:00", "17:00"]))
    out["task_remind_weekdays_only"] = cfg.get("task_remind_weekdays_only", defaults.get("task_remind_weekdays_only", True))
    if isinstance(cfg.get("task_remind_slots_shown"), dict):
        out["task_remind_slots_shown"] = cfg["task_remind_slots_shown"]
    out["task_remind_paused_until"] = cfg.get("task_remind_paused_until", defaults.get("task_remind_paused_until", ""))
    out["calendar_remind_minutes_before"] = normalize_calendar_remind_minutes(
        cfg.get("calendar_remind_minutes_before", defaults.get("calendar_remind_minutes_before", 15))
    )
    if isinstance(cfg.get("security"), dict):
        out["security"] = cfg["security"]
    try:
        from security import sanitize_config_urls
        sanitize_config_urls(out, defaults)
    except Exception as e:
        print(f"[security] config save sanitize skipped: {e}", flush=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def is_feature_enabled(name: str, cfg=None) -> bool:
    """features フラグの ON/OFF を取得 (未定義時は False)。

    例:
        if is_feature_enabled("visitor_notify"):
            ...
    """
    if cfg is None:
        cfg = load_config()
    features = cfg.get("features") if isinstance(cfg.get("features"), dict) else {}
    return bool(features.get(name, False))


def set_feature(name: str, enabled: bool, cfg=None):
    """features フラグを更新して保存する。"""
    if cfg is None:
        cfg = load_config()
    features = dict(cfg.get("features") or {})
    features[name] = bool(enabled)
    cfg["features"] = features
    save_config(cfg)
    return cfg


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
    try:
        from security import validate_http_url, validate_personal_board_id
        ok, _ = validate_http_url(frontend, cfg, purpose="personal_board")
        if not ok or not validate_personal_board_id(pid):
            return None
    except Exception:
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
