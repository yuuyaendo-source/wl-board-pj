# -*- coding: utf-8 -*-
"""設定の読み込み（config.json + 環境変数）。"""
import os
import sys
import json

# アプリのベースディレクトリ（アセット等の参照用・core サブディレクトリから1階層上を参照）
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_config_dir() -> str:
    """設定ファイルの保存先ディレクトリを返す。LOCALAPPDATA 優先、無ければホームディレクトリ配下。"""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "WonderLink")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception as e:
        print(f"[config] 設定ディレクトリ作成失敗: {e}", file=sys.stderr)
    return d


CONFIG_DIR = _get_config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def _ensure_config_file():
    """%LOCALAPPDATA% に config.json が存在しない場合のみ、ベースディレクトリの雛形を安全にコピーする。
    shutil.copy を使うと Program Files 側の ACL を引き継いで書き込み権限エラーになる恐れがあるため、
    json.load / json.dump によるクリーンなファイル生成を行う。
    """
    if os.path.isfile(CONFIG_PATH):
        return
    base_config = os.path.join(_BASE_DIR, "config.json")
    if os.path.isfile(base_config):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(base_config, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[config] 初期設定ファイルの配置失敗: {e}", file=sys.stderr)


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


def parse_calendar_remind_minutes_list(cfg: dict) -> list[int]:
    """カレンダーリマインドの「何分前」を複数返す（降順・重複なし）。"""
    raw = cfg.get("calendar_remind_minutes_before_list")
    out: list[int] = []
    if isinstance(raw, list) and raw:
        for v in raw:
            out.append(normalize_calendar_remind_minutes(v))
    elif cfg.get("calendar_remind_minutes_before") is not None:
        out.append(
            normalize_calendar_remind_minutes(cfg.get("calendar_remind_minutes_before"))
        )
    else:
        out.append(CALENDAR_REMIND_MINUTES_DEFAULT)
    return sorted(set(out), reverse=True)


def parse_calendar_remind_minutes_from_text(text: str) -> list[int]:
    """設定文字列 (分, カンマ区切り) → 正規化済み「何分前」リスト（降順・重複なし）。"""
    out: list[int] = []
    for part in (text or "").replace("、", ",").split(","):
        s = part.strip()
        if not s:
            continue
        n = normalize_calendar_remind_minutes(s)
        if n not in out:
            out.append(n)
    if not out:
        return [CALENDAR_REMIND_MINUTES_DEFAULT]
    return sorted(out, reverse=True)


def parse_task_remind_times_from_text(text: str) -> list[str]:
    """設定文字列 (HH:MM, カンマ区切り) → 正規化済み時刻リスト。"""
    from core.time_utils import normalize_time as _normalize_time

    out: list[str] = []
    for part in (text or "").replace("、", ",").split(","):
        norm = _normalize_time(part.strip())
        if norm and norm not in out:
            out.append(norm)
    return out


def get_app_base_dir():
    """アプリのベースディレクトリ（exe 時は exe と同じフォルダ）。config.json の基準に使う。"""
    return _BASE_DIR


def _default_user_id():
    """デスクトップアプリ利用者を識別するID（未設定時はWindowsのUSERNAMEなど）。"""
    return os.environ.get("WLINKO_USER_ID") or os.environ.get("USERNAME", "")


def _get_defaults():
    return {
        "ai_board_url": "https://wlboardsys.internal.wonder-link.com/",
        "postit_board_url": "https://wlboardsys.internal.wonder-link.com/",
        "postit_board_id": "wl",
        "postit_board_ids": None,
        "user_id": _default_user_id(),
        "display_name": "",
        "face_registry_person_id": "",
        "postit_poll_interval_sec": 60,
        "tray_click_action": "postit",
        "notifications_enabled": True,
        "startup_enabled": True,
        "mini_port_taskboard_url": "https://wlboardsys.internal.wonder-link.com/boards/taskboard",
        "update_check_url": "https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/latest.json",
        "update_network_check_url": "",
        "update_network_check_interval_sec": 5,
        "update_network_check_max_wait_sec": 180,
        "network_unreachable_backoff_sec": 30,
        "board_system_url": "https://wlboardsys.internal.wonder-link.com/api/bs",
        "board_system_personal_id": "",
        "board_system_email": "",
        "linko_server_url": "https://linkosys.internal.wonder-link.com",
        "linko_admin_token": "",
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
            "voice_registry_self": False,
        },
        "task_remind_times": ["13:00", "17:00"],
        "task_remind_weekdays_only": True,
        "task_remind_slots_shown": {
            "date": "",
            "slots": [],
        },
        "task_remind_paused_until": "",
        "calendar_remind_minutes_before": 15,
        "calendar_remind_minutes_before_list": [15],
        "security": {
            "allowed_host_suffixes": [".internal.wonder-link.com"],
            "allowed_hosts": ["localhost", "127.0.0.1"],
            "allow_private_ips": False,
        },
    }


DEFAULTS = _get_defaults()


def load_config():
    """config.json を読み、環境変数で上書き可能にする。"""
    _ensure_config_file()
    cfg = dict(_get_defaults())
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded.get("features"), dict):
                merged_features = dict(cfg.get("features") or {})
                merged_features.update(loaded["features"])
                loaded["features"] = merged_features
            cfg.update(loaded)
        except Exception as e:
            print(f"[config] config.json 読み込み失敗: {e}", file=sys.stderr)
    cfg["ai_board_url"] = (
        os.environ.get("AI_BOARD_URL", cfg["ai_board_url"]).rstrip("/") + "/"
    )
    cfg["postit_board_url"] = (
        os.environ.get("POSTIT_BOARD_URL", cfg["postit_board_url"]).rstrip("/") + "/"
    )
    cfg["mini_port_taskboard_url"] = (
        os.environ.get(
            "MINI_PORT_TASKBOARD_URL",
            cfg.get(
                "mini_port_taskboard_url",
                "https://wlboardsys.internal.wonder-link.com/boards/taskboard",
            ),
        )
    ).strip()
    cfg["board_system_url"] = (
        (os.environ.get("BOARD_SYSTEM_URL", cfg.get("board_system_url", "")) or "")
        .strip()
        .rstrip("/")
    )
    cfg["linko_server_url"] = (
        (os.environ.get("LINKO_SERVER_URL", cfg.get("linko_server_url", "")) or "")
        .strip()
        .rstrip("/")
    )
    cfg["linko_admin_token"] = (
        os.environ.get("LINKO_ADMIN_TOKEN", cfg.get("linko_admin_token", "")) or ""
    ).strip()

    needs_save = False
    if cfg.get("linko_server_url") == "https://linko-board.internal.wonder-link.com":
        cfg["linko_server_url"] = "https://linkosys.internal.wonder-link.com"
        needs_save = True

    if needs_save:
        save_config(cfg)

    try:
        from core.security import sanitize_config_urls

        sanitize_config_urls(cfg, _get_defaults())
    except Exception as e:
        print(f"[security] config URL sanitize skipped: {e}", flush=True)
    mins_list = parse_calendar_remind_minutes_list(cfg)
    cfg["calendar_remind_minutes_before_list"] = mins_list
    cfg["calendar_remind_minutes_before"] = (
        mins_list[0] if mins_list else CALENDAR_REMIND_MINUTES_DEFAULT
    )
    return cfg


_PASSTHROUGH_KEYS: tuple[str, ...] = (
    "ai_board_url",
    "postit_board_url",
    "user_id",
    "display_name",
    "postit_board_id",
    "postit_poll_interval_sec",
    "tray_click_action",
    "notifications_enabled",
    "startup_enabled",
    "mini_port_taskboard_url",
    "update_check_url",
    "update_network_check_url",
    "update_network_check_interval_sec",
    "update_network_check_max_wait_sec",
    "network_unreachable_backoff_sec",
    "board_system_url",
    "board_system_personal_id",
    "board_system_email",
    "linko_server_url",
    "linko_admin_token",
    "task_remind_times",
    "task_remind_weekdays_only",
    "task_remind_paused_until",
    "face_registry_person_id",
)


def save_config(cfg: dict) -> None:
    """config.json に保存する。"""
    defaults = _get_defaults()
    out: dict = {}

    for key in _PASSTHROUGH_KEYS:
        out[key] = cfg.get(key, defaults.get(key))

    if cfg.get("postit_board_ids") is not None:
        out["postit_board_ids"] = cfg["postit_board_ids"]

    src_features = cfg.get("features") if isinstance(cfg.get("features"), dict) else {}
    out["features"] = {**(defaults.get("features") or {}), **src_features}

    if isinstance(cfg.get("task_remind_slots_shown"), dict):
        out["task_remind_slots_shown"] = cfg["task_remind_slots_shown"]

    mins_list = parse_calendar_remind_minutes_list(cfg)
    if not mins_list:
        mins_list = parse_calendar_remind_minutes_list(defaults)
    out["calendar_remind_minutes_before_list"] = mins_list
    out["calendar_remind_minutes_before"] = mins_list[0]

    if isinstance(cfg.get("security"), dict):
        out["security"] = cfg["security"]

    try:
        from core.security import sanitize_config_urls

        sanitize_config_urls(out, defaults)
    except Exception as e:
        print(f"[security] config save sanitize skipped: {e}", flush=True)

    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[config] config.json 保存失敗: {e}", file=sys.stderr)


def is_feature_enabled(name: str, cfg=None) -> bool:
    if cfg is None:
        cfg = load_config()
    features = cfg.get("features") or {}
    return bool(features.get(name, False))


def set_feature(name: str, enabled: bool, cfg=None):
    if cfg is None:
        cfg = load_config()
    features = dict(cfg.get("features") or {})
    features[name] = bool(enabled)
    cfg["features"] = features
    save_config(cfg)
    return cfg


def get_board_system_frontend_base(cfg=None):
    if cfg is None:
        cfg = load_config()
    base = (cfg.get("board_system_url") or "").strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/api/bs"):
        return base[: -len("/api/bs")].rstrip("/")
    return base


def get_board_system_personal_url(cfg=None):
    if cfg is None:
        cfg = load_config()
    frontend = get_board_system_frontend_base(cfg)
    pid = (cfg.get("board_system_personal_id") or "").strip()
    if not frontend or not pid:
        return None
    try:
        from core.security import validate_http_url, validate_personal_board_id

        ok, _ = validate_http_url(frontend, cfg, purpose="personal_board")
        if not ok or not validate_personal_board_id(pid):
            return None
    except Exception:
        return None
    return f"{frontend}/boards/personal/{pid}"


def get_effective_board_system_url(cfg=None):
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


def save_board_system_login(
    cfg: dict, *, board_url: str, user_id, user_data: dict, login_email: str = ""
) -> None:
    cfg["board_system_url"] = (board_url or "").strip().rstrip("/")
    cfg["board_system_personal_id"] = str(user_id)
    cfg["user_id"] = str(user_id)
    if (user_data.get("call_name") or user_data.get("name") or "").strip():
        cfg["display_name"] = (
            user_data.get("call_name") or user_data.get("name") or ""
        ).strip()
    email = (login_email or user_data.get("email") or "").strip()
    if email and "@" in email:
        cfg["board_system_email"] = email
    save_config(cfg)


def get_board_system_login_email(cfg=None) -> str:
    """Board System ログイン済みユーザーのメール。config または API から取得。"""
    if cfg is None:
        cfg = load_config()
    email = (cfg.get("board_system_email") or "").strip()
    if email and "@" in email:
        return email
    pid = (cfg.get("board_system_personal_id") or "").strip()
    board_url = get_effective_board_system_url(cfg)
    if not pid or not board_url:
        return ""
    try:
        import requests

        from core.security import assert_http_url

        user_url = f"{board_url}/users/{pid}"
        assert_http_url(user_url, cfg, purpose="users_get")
        r = requests.get(user_url, timeout=10)
        if r.status_code != 200:
            return ""
        data = r.json() if r.content else {}
        if not isinstance(data, dict):
            return ""
        fetched = (data.get("email") or "").strip()
        if fetched and "@" in fetched:
            cfg["board_system_email"] = fetched
            save_config(cfg)
            return fetched
    except Exception as e:
        print(f"[config] ログインメールの API 取得失敗: {e}", file=sys.stderr)
    return ""
