# -*- coding: utf-8 -*-
"""
Wonder Rinko Desktop App (DT_APP) - Personal Rinko Agent
社員PCに常駐し、お知らせとワンクリックDeep Linkで各ユーザーのパーソナルモードへ誘導する。
タスクトレイ常駐＋ミニポート（付箋クイック投稿）を起動時に表示。トレイからミニポートの表示/非表示を切り替え可能。
"""
import os
import sys

# 凍結（cx_Freeze/MSI）時: lib を先に sys.path に追加し、PIL を lib/PIL から確実に読む
_exe_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else None
_lib_dir = os.path.join(_exe_dir, "lib") if _exe_dir else None

def _write_diagnostic(line: str):
    """凍結時のみ、診断ログを exe と同じフォルダに追記する。"""
    if not _exe_dir:
        return
    try:
        log_path = os.path.join(_exe_dir, "WonderLinko_diagnostic.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def _diagnostic_frozen_env():
    """凍結時: lib/PIL の有無と _imaging*.pyd を診断ログに書き、デバイス側の切り分けに使う。"""
    if not _exe_dir or not _lib_dir:
        return
    try:
        log_path = os.path.join(_exe_dir, "WonderLinko_diagnostic.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"[{__import__('datetime').datetime.now().isoformat()}] 起動時診断\n")
            f.write(f"exe_dir: {_exe_dir}\n")
            f.write(f"lib_dir exists: {os.path.isdir(_lib_dir)}\n")
            pil_dir = os.path.join(_lib_dir, "PIL")
            f.write(f"lib/PIL exists: {os.path.isdir(pil_dir)}\n")
            if os.path.isdir(pil_dir):
                files = []
                for root, _dirs, names in os.walk(pil_dir):
                    for n in names:
                        rel = os.path.relpath(os.path.join(root, n), pil_dir)
                        files.append(rel.replace("\\", "/"))
                f.write(f"lib/PIL files ({len(files)}): {sorted(files)[:50]}\n")
                imaging = [x for x in files if "_imaging" in x and x.endswith(".pyd")]
                f.write(f"_imaging*.pyd: {imaging}\n")
    except Exception as e:
        _write_diagnostic(f"diagnostic error: {e}")

if getattr(sys, "frozen", False):
    if os.path.isdir(_lib_dir) and _lib_dir not in sys.path:
        sys.path.insert(0, _lib_dir)
    _diagnostic_frozen_env()

import threading
import warnings
import webbrowser
from urllib.parse import quote_plus

# win10toast の pkg_resources 非推奨警告を抑制
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

import pystray

# PIL は凍結環境で _imaging の読み込みに失敗することがある（デバイス側要因の可能性あり）
_PIL_Image = _PIL_ImageDraw = None
try:
    from PIL import Image, ImageDraw
    _PIL_Image, _PIL_ImageDraw = Image, ImageDraw
except ImportError as e:
    if _exe_dir:
        _write_diagnostic(f"PIL import failed: {e}")
        _write_diagnostic("デバイス側の確認: (1) lib\\PIL に _imaging*.pyd があるか (2) VC++ Redistributable 導入 (3) ウイルス対策で .pyd がブロックされていないか")
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(  # type: ignore
            None,
            f"PIL（画像処理）の読み込みに失敗しました。\n\n{e}\n\n"
            "【デバイス側で確認してください】\n"
            "・インストール先の lib\\PIL フォルダに _imaging で始まる .pyd ファイルがあるか\n"
            "・Visual C++ Redistributable がインストールされているか\n"
            "・ウイルス対策ソフトで .pyd がブロックされていないか\n\n"
            "詳細は exe と同じフォルダの WonderLinko_diagnostic.txt を参照してください。",
            "Wonder Linko - 起動エラー",
            0x10,
        )
    except Exception:
        pass
    raise

# 以降のコードで Image / ImageDraw をそのまま使えるようにする
Image = _PIL_Image
ImageDraw = _PIL_ImageDraw

from config_loader import load_config, save_config
import notifications
from postit_poll import start_postit_poll, fetch_summary_with_error
import startup


# メニューから参照するためグローバルに設定を保持
_config = {}
_icon = None
_miniport_window = None
_miniport_visible = True


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


def toggle_startup(icon, item):
    """PC起動時に自動で起動するかどうかをトグル。"""
    if sys.platform != "win32":
        notifications.show_toast("Wonder Rinko", "Windows のみ対応しています。", duration_sec=3)
        return
    currently = startup.is_startup_enabled()
    ok = startup.set_startup_enabled(not currently)
    if ok:
        enabled = startup.is_startup_enabled()
        notifications.show_toast(
            "Wonder Rinko",
            "PC起動時に自動で起動: " + ("ON" if enabled else "OFF"),
            duration_sec=3,
        )
    else:
        notifications.show_toast("Wonder Rinko", "設定の変更に失敗しました。", duration_sec=3)


def _miniport_show():
    """ミニポートを表示（メインスレッドで実行する想定）。"""
    global _miniport_visible
    if _miniport_window is not None:
        try:
            _miniport_window.deiconify()
            _miniport_window.lift()
            _miniport_window.attributes("-topmost", True)
            _miniport_visible = True
        except Exception:
            pass


def _miniport_hide():
    """ミニポートを非表示（メインスレッドで実行する想定）。"""
    global _miniport_visible
    if _miniport_window is not None:
        try:
            _miniport_window.withdraw()
            _miniport_visible = False
        except Exception:
            pass


def show_miniport(icon=None, item=None):
    """トレイメニュー「ミニポートを表示」."""
    if _miniport_window is not None:
        _miniport_window.after(0, _miniport_show)


def hide_miniport(icon=None, item=None):
    """トレイメニュー「ミニポートを非表示」."""
    if _miniport_window is not None:
        _miniport_window.after(0, _miniport_hide)


def toggle_miniport(icon=None, item=None):
    """トレイメニュー「ミニポート」の表示/非表示トグル。"""
    if _miniport_window is None:
        return
    if _miniport_visible:
        _miniport_window.after(0, _miniport_hide)
    else:
        _miniport_window.after(0, _miniport_show)


def quit_app(icon, item):
    """終了。"""
    if _miniport_window is not None:
        try:
            _miniport_window.after(0, _miniport_window.quit)
        except Exception:
            pass
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
        pystray.MenuItem("ミニポート", toggle_miniport, checked=lambda *_: _miniport_visible),
        pystray.MenuItem("ミニポートを表示", show_miniport),
        pystray.MenuItem("ミニポートを非表示", hide_miniport),
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
        pystray.MenuItem("PC起動時に自動で起動", toggle_startup, checked=lambda *_: startup.is_startup_enabled()),
        pystray.MenuItem("表示名を変更（付箋の投稿者名）", _change_display_name),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("終了", quit_app),
    )


def run_tray():
    """トレイアイコンを表示してイベントループを開始（別スレッドで実行）。"""
    global _config, _icon
    _config = load_config()
    image = _make_icon_image()
    menu = build_menu(None)
    _icon = pystray.Icon("wonder_rinko", image, "Wonder Rinko（リン子）", menu)
    _icon.run()


def _show_display_name_dialog(current_name: str = "") -> str | None:
    """表示名入力ダイアログを表示し、入力された名前を返す。キャンセル時は None。"""
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        prompt = "ミニポートから投稿したときに付箋に表示する名前を入力してください:"
        if current_name:
            prompt += "\n（現在: " + current_name + "）"
        name = simpledialog.askstring("Wonder Linko - 表示名", prompt, parent=root)
        root.destroy()
        return name
    except Exception:
        return None


def _prompt_display_name_if_empty():
    """表示名が未設定なら入力ダイアログを表示し、config に保存する。"""
    global _config
    name = (_config.get("display_name") or "").strip()
    if name:
        return
    name = _show_display_name_dialog()
    if name:
        name = name.strip()
    if name:
        _config["display_name"] = name
        save_config(_config)


def _change_display_name(*args):
    """トレイメニュー「表示名を変更」で表示名を再入力して保存する。"""
    global _config
    _config = load_config()
    current = (_config.get("display_name") or "").strip()
    name = _show_display_name_dialog(current)
    if name:
        name = name.strip()
    if name:
        _config["display_name"] = name
        save_config(_config)
        notifications.show_toast("Wonder Linko", "表示名を「" + name + "」に変更しました。", duration_sec=2)


def main():
    global _config, _miniport_window, _miniport_visible
    _config = load_config()

    # 表示名未設定時は起動時に名前入力を促す
    _prompt_display_name_if_empty()

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

    # MSI 等でインストールした exe の初回起動時のみ、Windows 再起動後もミニポートを自動表示するためスタートアップに登録
    if sys.platform == "win32" and getattr(sys, "frozen", False) and not startup.is_startup_enabled():
        if startup.set_startup_enabled(True):
            notifications.show_toast(
                "Wonder Rinko",
                "PC起動時に自動で起動するように設定しました。",
                duration_sec=4,
            )

    # ミニポートを起動時に強制表示（タスクトレイは常駐、ミニポートはトレイから表示/非表示可能）
    try:
        import customtkinter as ctk
        from mini_port import MiniPortWindow
        ctk.set_appearance_mode("system")
        _miniport_window = MiniPortWindow()
        _miniport_visible = True
    except Exception as e:
        _miniport_window = None
        _miniport_visible = False
        notifications.show_toast(
            "Wonder Rinko",
            "ミニポートの起動に失敗しました: " + str(e)[:50],
            duration_sec=5,
        )

    # トレイを別スレッドで開始（メインスレッドはミニポートの mainloop で使用）
    tray_thread = threading.Thread(target=run_tray, daemon=True)
    tray_thread.start()

    # ミニポートのメインループ（メインスレッド）。終了時はトレイの「終了」で quit が呼ばれる
    if _miniport_window is not None:
        _miniport_window.mainloop()
    else:
        # ミニポートが作れなかった場合はトレイだけ待つ
        tray_thread.join()


if __name__ == "__main__":
    main()
