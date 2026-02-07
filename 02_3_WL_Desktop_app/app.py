# -*- coding: utf-8 -*-
"""
Wonder Rinko Desktop App (DT_APP) - Personal Rinko Agent
社員PCに常駐し、お知らせとワンクリックDeep Linkで各ユーザーのパーソナルモードへ誘導する。
"""
import sys
import threading
import warnings
import webbrowser
from urllib.parse import quote_plus

# win10toast の pkg_resources 非推奨警告を抑制
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

import pystray
from PIL import Image, ImageDraw

from config_loader import load_config, save_config
import notifications
from postit_poll import start_postit_poll, fetch_summary_with_error


# メニューから参照するためグローバルに設定を保持
_config = {}
_icon = None


def _make_icon_image():
    """トレイ用のシンプルなアイコン画像（64x64）。"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 丸で「R」の代わりにリンク風の丸
    d.ellipse([4, 4, size - 4, size - 4], fill=(0, 200, 120), outline=(0, 255, 200))
    d.ellipse([16, 16, size - 16, size - 16], fill=(0, 60, 40))
    return img


def _personal_url():
    """このユーザー用のパーソナルモードURL（personal_path があれば /asakawa 等、なければ /personal?user=xxx）。"""
    base = _config.get("ai_board_url", "http://127.0.0.1:5000/").rstrip("/")
    path = (_config.get("personal_path") or "").strip()
    if path:
        return base + "/" + path.lstrip("/")
    user_id = _config.get("user_id", "") or ""
    q = "user=" + quote_plus(user_id) if user_id else ""
    return base + "/personal" + ("?" + q if q else "")


def _postit_board_url():
    """付箋ボードの該当ボードを開くURL。"""
    base = (_config.get("postit_board_url") or "").rstrip("/")
    board_id = (_config.get("postit_board_id") or "").strip()
    if not base or not board_id:
        return None
    return f"{base}/board/{board_id}"


def open_tray_click_target(*args):
    """トレイアイコンクリックで開く先（設定に従う）。"""
    action = _config.get("tray_click_action", "postit")
    if action == "personal":
        webbrowser.open(_personal_url())
        return
    if action == "last_notification":
        if notifications.open_last_notification():
            return
        webbrowser.open(_personal_url())
        return
    # デフォルト: postit（付箋ボード）
    url = _postit_board_url()
    if url:
        webbrowser.open(url)
    else:
        open_personal_mode()


def open_personal_mode(*args):
    """このユーザー用のパーソナルモード（個人用）をブラウザで開く。"""
    webbrowser.open(_personal_url())


def open_last_notification(*args):
    """最後のお知らせURLを開く。"""
    if notifications.open_last_notification():
        return
    # 未設定ならパーソナルを開く
    open_personal_mode()


def toggle_avatar(icon, item):
    """アバター表示/非表示をトグル（将来のアバターウィンドウ用に設定のみ保存）。"""
    _config["avatar_visible"] = not _config.get("avatar_visible", True)
    save_config(_config)
    visible = _config["avatar_visible"]
    notifications.show_toast(
        "Wonder Rinko",
        "アバター表示: " + ("ON" if visible else "OFF") + "（準備中）",
        duration_sec=3,
    )


def toggle_sound(icon, item):
    """音声ON/OFFをトグル。"""
    _config["sound_enabled"] = not _config.get("sound_enabled", True)
    save_config(_config)
    notifications.show_toast(
        "Wonder Rinko",
        "音声: " + ("ON" if _config["sound_enabled"] else "OFF"),
        duration_sec=3,
    )


def quit_app(icon, item):
    """終了。"""
    icon.stop()


def _test_postit_connection(*args):
    """付箋ボードへの接続をテストし、結果をトーストで表示。"""
    def do_test():
        cfg = load_config()
        url = (cfg.get("postit_board_url") or "").strip().rstrip("/")
        board_id = (cfg.get("postit_board_id") or "").strip()
        if not url or not board_id:
            notifications.show_toast(
                "付箋ボード接続テスト",
                "config.json の postit_board_url と postit_board_id を設定してください。",
                duration_sec=5,
            )
            return
        summary, err = fetch_summary_with_error(url, board_id)
        if err:
            notifications.show_toast(
                "付箋ボード接続テスト",
                "接続できません: " + err,
                duration_sec=8,
            )
        else:
            n = summary.get("notesCount", 0)
            notifications.show_toast(
                "付箋ボード接続テスト",
                f"接続できました。付箋 {n} 件（通知は約1分間隔でチェックしています）",
                duration_sec=5,
            )
    threading.Thread(target=do_test, daemon=True).start()


def _set_tray_click_action(action):
    """トレイアイコンクリックで開く先を設定して保存。"""
    global _config
    _config["tray_click_action"] = action
    save_config(_config)
    labels = {"postit": "付箋ボード", "personal": "パーソナル", "last_notification": "最後のお知らせ"}
    notifications.show_toast(
        "Wonder Rinko",
        "アイコンクリックで開く: " + labels.get(action, action),
        duration_sec=3,
    )


def build_menu(icon):
    """トレイメニューを組み立てる。"""
    global _config
    _config = load_config()
    avatar_visible = _config.get("avatar_visible", True)
    sound_enabled = _config.get("sound_enabled", True)
    tray_action = _config.get("tray_click_action", "postit")

    tray_click_submenu = pystray.Menu(
        pystray.MenuItem("付箋ボード", lambda *_: _set_tray_click_action("postit"), checked=lambda *_: tray_action == "postit"),
        pystray.MenuItem("パーソナル", lambda *_: _set_tray_click_action("personal"), checked=lambda *_: tray_action == "personal"),
        pystray.MenuItem("最後のお知らせ", lambda *_: _set_tray_click_action("last_notification"), checked=lambda *_: tray_action == "last_notification"),
    )

    return pystray.Menu(
        pystray.MenuItem("開く（設定で変更可）", open_tray_click_target, default=True),
        pystray.MenuItem("アイコンクリックで開く", tray_click_submenu),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("パーソナルモードを開く", open_personal_mode),
        pystray.MenuItem("最後のお知らせを開く", open_last_notification, enabled=True),
        pystray.MenuItem("付箋ボード接続テスト", _test_postit_connection),
        pystray.MenuItem("テストお知らせ（付箋ボードURL付き）", lambda *_: notifications.show_toast(
            "テスト", "新しい付箋が投稿されました。", url=_config.get("postit_board_url"), duration_sec=5
        )),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("アバターを表示", toggle_avatar, checked=lambda *_: _config.get("avatar_visible", True)),
        pystray.MenuItem("音声ON", toggle_sound, checked=lambda *_: _config.get("sound_enabled", True)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("終了", quit_app),
    )


def run_tray():
    """トレイアイコンを表示してイベントループを開始。"""
    global _config, _icon
    _config = load_config()
    image = _make_icon_image()
    menu = build_menu(None)
    _icon = pystray.Icon("wonder_rinko", image, "Wonder Rinko（リン子）", menu)
    _icon.run()


def main():
    global _config
    _config = load_config()

    # 付箋ボード連携: 新付箋をポーリングし、変化時にトースト＋「最後のお知らせ」にURLを保存
    def on_new_postit_notes(summary, board_open_url):
        duration = _config.get("toast_duration_sec", 8)
        notifications.show_toast(
            "リン子のお知らせ",
            "新しい付箋が投稿されました。",
            url=board_open_url,
            duration_sec=duration,
        )

    if _config.get("postit_poll_interval_sec", 0) > 0:
        start_postit_poll(lambda: _config, on_new_postit_notes)

    # 起動時にはブラウザを開かない（ユーザーがトレイの「パーソナルモードを開く」で個人用URLを開く）
    run_tray()


if __name__ == "__main__":
    main()
