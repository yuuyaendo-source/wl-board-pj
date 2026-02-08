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
        "personal_path": "asakawa",  # デモ用: パーソナルモードのパス（/asakawa でAIボード・デスクトップアプリ同一ページ）
        "open_personal_on_start": False,
        "avatar_visible": True,
        "sound_enabled": True,
        "toast_duration_sec": 8,
        "postit_poll_interval_sec": 60,  # 付箋ボードの新付箋チェック間隔（0で無効）
        "tray_click_action": "postit",  # トレイアイコンクリックで開く先: "postit" | "personal" | "last_notification"
        "toast_icon_path": "",  # トースト用アイコン（PNG/ICOの絶対パス。空ならデフォルトアイコン）
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
    return cfg


def save_config(cfg):
    """config.json に保存（AI_BOARD_URL 等は保存しない）。"""
    defaults = _get_defaults()
    out = {k: v for k, v in cfg.items() if k in defaults and k not in ("ai_board_url", "postit_board_url")}
    out["ai_board_url"] = cfg.get("ai_board_url", defaults["ai_board_url"])
    out["postit_board_url"] = cfg.get("postit_board_url", defaults["postit_board_url"])
    out["user_id"] = cfg.get("user_id", defaults["user_id"])
    out["personal_path"] = cfg.get("personal_path", defaults.get("personal_path", ""))
    out["postit_board_id"] = cfg.get("postit_board_id", defaults.get("postit_board_id", ""))
    if cfg.get("postit_board_ids") is not None:
        out["postit_board_ids"] = cfg.get("postit_board_ids")
    out["postit_poll_interval_sec"] = cfg.get("postit_poll_interval_sec", defaults.get("postit_poll_interval_sec", 60))
    out["tray_click_action"] = cfg.get("tray_click_action", defaults.get("tray_click_action", "postit"))
    out["toast_icon_path"] = cfg.get("toast_icon_path", defaults.get("toast_icon_path", ""))
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
