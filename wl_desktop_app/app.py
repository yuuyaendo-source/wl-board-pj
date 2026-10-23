# -*- coding: utf-8 -*-
"""
Wonder Linko Desktop App (DT_APP) - Personal Linko Agent
社員PCに常駐し、お知らせとワンクリックDeep Linkで各ユーザーのパーソナルモードへ誘導する。
タスクトレイ常駐＋ミニポート（付箋クイック投稿）を起動時に表示。トレイからミニポートの表示/非表示を切り替え可能。
"""
import os
import sys

# 凍結（cx_Freeze/MSI）時: lib を先に sys.path に追加し、PIL を lib/PIL から確実に読む
_exe_dir = (
    os.path.dirname(os.path.abspath(sys.executable))
    if getattr(sys, "frozen", False)
    else None
)
_lib_dir = os.path.join(_exe_dir, "lib") if _exe_dir else None


def _diagnostic_log_path() -> str:
    """診断ログの出力先パスを返す。LOCALAPPDATA 優先、無ければホームディレクトリ配下。"""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "WonderLink")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return os.path.join(d, "WonderLinko_diagnostic.txt")


def _write_diagnostic(line: str):
    r"""凍結時のみ、診断ログを %LOCALAPPDATA%\WonderLink に追記する。"""
    if not _exe_dir:
        return
    try:
        log_path = _diagnostic_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _diagnostic_frozen_env():
    """凍結時: lib/PIL の有無と _imaging*.pyd を診断ログに書き、デバイス側の切り分けに使う。"""
    if not _exe_dir or not _lib_dir:
        return
    try:
        log_path = _diagnostic_log_path()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(
                f"[{__import__('datetime').datetime.now().isoformat()}] 起動時診断\n"
            )
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

import atexit
import logging
import signal
import subprocess
import threading
import time
from urllib.parse import quote_plus
import pystray

_PIL_Image = _PIL_ImageDraw = None
try:
    from PIL import Image, ImageDraw

    _PIL_Image, _PIL_ImageDraw = Image, ImageDraw
except ImportError as e:
    if _exe_dir:
        _write_diagnostic(f"PIL import failed: {e}")
        _write_diagnostic(
            "デバイス側の確認: (1) lib\\PIL に _imaging*.pyd があるか (2) VC++ Redistributable 導入 (3) ウイルス対策で .pyd がブロックされていないか"
        )
    error_msg = (
        f"PIL（画像処理）の読み込みに失敗しました。\n\n{e}\n\n"
        "【デバイス側で確認してください】\n"
        "・インストール先の lib\\PIL フォルダに _imaging で始まる .pyd ファイルがあるか\n"
        "・Visual C++ Redistributable がインストールされているか\n"
        "・ウイルス対策ソフトで .pyd がブロックされていないか\n\n"
        "詳細は %LOCALAPPDATA%\\WonderLink\\WonderLinko_diagnostic.txt を参照してください。"
    )
    try:
        import tkinter
        from tkinter import messagebox

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror("Wonder Linko - 起動エラー", error_msg)
        root.destroy()
    except Exception as te:
        _write_diagnostic(f"tkinter messagebox failed: {te}")
    sys.exit(1)

Image = _PIL_Image
ImageDraw = _PIL_ImageDraw

from core.config_loader import load_config, save_config
from services import notifications
from services.postit_poll import start_postit_poll
from core import startup
from core.version import __version__
from core.update_checker import check_and_notify
from core.network_readiness import wait_for_network_ready as wait_for_network
from core.network_readiness import resolve_probe_url
from hardware.audio_player import cleanup_temp_audio_files

from core.app_log import setup_app_log, log_info

setup_app_log()

_config = {}
_icon = None
_miniport_window = None
_miniport_visible = True

# 単一インスタンス制御（Windows は OS 名前付き Mutex、その他はファイルロック）
_SINGLE_INSTANCE_FD = None
_SINGLE_INSTANCE_MUTEX = None
_SHOW_REQUEST_STOP = False


def cleanup_resources():
    """リソース（トレイアイコン・ミニポートウィンドウ・ファイルロック・一時音声ファイル）を確実に破棄する"""
    global _icon, _miniport_window, _SINGLE_INSTANCE_FD, _SINGLE_INSTANCE_MUTEX

    # 自身の PID を持つ一時音声ファイルのみをクリーンアップ
    cleanup_temp_audio_files(only_current_pid=True)

    if _icon is not None:
        try:
            _icon.stop()
        except Exception:
            pass
    if _miniport_window is not None:
        try:
            _miniport_window.quit()
            _miniport_window.destroy()
        except Exception:
            pass
    if _SINGLE_INSTANCE_FD is not None:
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(_SINGLE_INSTANCE_FD, msvcrt.LK_UNLCK, 1)
            os.close(_SINGLE_INSTANCE_FD)
            _SINGLE_INSTANCE_FD = None
        except Exception:
            pass
    if _SINGLE_INSTANCE_MUTEX is not None:
        try:
            import ctypes

            ctypes.windll.kernel32.CloseHandle(_SINGLE_INSTANCE_MUTEX)
        except Exception:
            pass
        _SINGLE_INSTANCE_MUTEX = None


def on_closing():
    """強制終了/WM_CLOSE要求時のフック"""
    cleanup_resources()
    sys.exit(0)


atexit.register(cleanup_resources)
try:
    signal.signal(signal.SIGTERM, lambda sig, frame: on_closing())
except Exception:
    pass


def _show_request_dir() -> str:
    """show_request / pid ファイルの置き場所。LOCALAPPDATA があれば優先、無ければユーザーホーム配下。"""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "WonderLink")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def _show_request_path() -> str:
    return os.path.join(_show_request_dir(), "show_request")


def _acquire_single_instance_lock() -> bool:
    """OSが終了時に解放するロックで単一インスタンスを保証する。
    Windows は名前付き Mutex を使い、クラッシュ後にロックファイルが残っても
    次回起動を妨げない。
    """
    global _SINGLE_INSTANCE_FD, _SINGLE_INSTANCE_MUTEX

    lock_dir = _show_request_dir()
    lock_file = os.path.join(lock_dir, "WonderLinko.lock")

    if sys.platform == "win32":
        try:
            # ファイルロックはアプリ更新・ネットワークドライブ等で不安定になることがあるため、
            # OS がプロセス終了時に必ず解放する名前付き Mutex を使う。
            import ctypes

            mutex_name = "Local\\WonderLinko.Desktop.SingleInstance"
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            handle = kernel32.CreateMutexW(None, False, mutex_name)
            if not handle:
                return False
            ERROR_ALREADY_EXISTS = 183
            if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
                ctypes.windll.kernel32.CloseHandle(handle)
                return False
            _SINGLE_INSTANCE_MUTEX = handle
            return True
        except Exception:
            return False
    else:
        # 非Windows環境でのフォールバック (fcntl)
        try:
            import fcntl

            fd = open(lock_file, "w")
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _SINGLE_INSTANCE_FD = fd
            return True
        except (OSError, IOError):
            return False


def _signal_existing_instance_to_show() -> None:
    """重複起動時、先発プロセスに前面化を依頼する。"""
    try:
        with open(_show_request_path(), "w", encoding="utf-8") as f:
            f.write(str(int(time.time())))
    except Exception:
        pass


def _start_show_request_watcher() -> None:
    """show_request ファイルを監視し、検出したらミニポートを前面化するスレッドを起動。"""
    path = _show_request_path()

    def loop():
        while not _SHOW_REQUEST_STOP:
            try:
                if os.path.isfile(path):
                    try:
                        os.unlink(path)
                    except Exception:
                        pass
                    if _miniport_window is not None:
                        try:
                            _miniport_window.after(0, _miniport_show)
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(1.0)

    t = threading.Thread(target=loop, daemon=True)
    t.start()


def _make_icon_image():
    try:
        from core.config_loader import get_app_base_dir

        base = get_app_base_dir()
    except Exception:
        base = os.path.dirname(os.path.abspath(__file__))
    for candidate in (
        os.path.join(base, "assets", "tray_icon.png"),
        os.path.join(base, "assets", "toast_icon.png"),
        os.path.join(base, "toast_icon.png"),
    ):
        if Image is not None and os.path.isfile(candidate):
            try:
                return Image.open(candidate).convert("RGBA")
            except Exception:
                pass
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, size - 4, size - 4], fill=(0, 200, 120), outline=(0, 255, 200))
    d.ellipse([16, 16, size - 16, size - 16], fill=(0, 60, 40))
    return img


def _personal_url():
    from core.config_loader import get_board_system_personal_url

    url = get_board_system_personal_url()
    if url:
        return url
    base = _config.get("ai_board_url", "http://127.0.0.1:5000/").rstrip("/")
    path = (_config.get("personal_path") or "").strip()
    if path:
        return base + "/" + path.lstrip("/")
    user_id = _config.get("user_id", "") or ""
    q = "user=" + quote_plus(user_id) if user_id else ""
    return base + "/personal" + ("?" + q if q else "")


def _linko_cards_url():
    from ui.linko_cards import build_linko_cards_url

    return build_linko_cards_url(_config)


def open_linko_cards(*args):
    from core.security import safe_webbrowser_open

    safe_webbrowser_open(_linko_cards_url(), _config)


def _postit_board_url():
    base = (_config.get("postit_board_url") or "").rstrip("/")
    board_id = (_config.get("postit_board_id") or "").strip()
    if not base or not board_id:
        return None
    return f"{base}/board/{board_id}"


def open_tray_click_target(*args):
    action = _config.get("tray_click_action", "postit")
    from core.security import safe_webbrowser_open

    if action == "personal":
        safe_webbrowser_open(_personal_url(), _config)
        return
    if action == "last_notification":
        if notifications.open_last_notification():
            return
        safe_webbrowser_open(_personal_url(), _config)
        return
    url = _postit_board_url()
    if url:
        safe_webbrowser_open(url, _config)
    else:
        open_personal_mode()


def open_personal_mode(*args):
    from core.security import safe_webbrowser_open

    safe_webbrowser_open(_personal_url(), _config)


def open_last_notification(*args):
    if notifications.open_last_notification():
        return
    open_personal_mode()


def _miniport_show():
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
    global _miniport_visible
    if _miniport_window is not None:
        try:
            _miniport_window.withdraw()
            _miniport_visible = False
        except Exception:
            pass


def show_miniport(icon=None, item=None):
    if _miniport_window is not None:
        _miniport_window.after(0, _miniport_show)


def hide_miniport(icon=None, item=None):
    if _miniport_window is not None:
        _miniport_window.after(0, _miniport_hide)


def _on_calendar_remind_ui(items):
    if not items:
        try:
            from services.calendar_notify_client import notify_delivery_done

            notify_delivery_done()
        except Exception:
            pass
        return

    def _show_one(index: int = 0) -> None:
        if index >= len(items):
            try:
                from services.calendar_notify_client import notify_delivery_done

                notify_delivery_done()
            except Exception:
                pass
            return
        item = items[index]
        try:
            from services.calendar_notify_client import (
                post_shown,
                calendar_remind_minutes_list,
                DEFAULT_MINUTES_BEFORE,
            )
            from services.remind_notify import deliver_remind

            cfg = load_config()
            minutes = item.get("minutes_before")
            if minutes is None:
                mins_list = calendar_remind_minutes_list(cfg)
                minutes = mins_list[0] if mins_list else DEFAULT_MINUTES_BEFORE
            if not post_shown(cfg, item, minutes_before=minutes):
                log_info("[calendar_notify] shown API 失敗")
            deliver_remind(
                "Wonder Linko",
                item.get("message") or item.get("title") or "予定",
                item.get("message") or item.get("title") or "",
                voice_text=item.get("voice_text"),
                duration_sec=12,
            )
        except Exception as e:
            log_info(f"[calendar_notify] 表示失敗: {e}")

        delay_ms = 12000 if index + 1 < len(items) else 500
        if _miniport_window is not None and index + 1 < len(items):
            _miniport_window.after(delay_ms, lambda: _show_one(index + 1))
        else:
            _show_one(index + 1)

    _show_one(0)


def _on_task_remind_ui(items, slot, summary=""):
    def _ack(item, action: str):
        try:
            from services.task_remind_client import post_ack

            cfg = load_config()
            if post_ack(cfg, item, slot, action):
                if action == "done":
                    notifications.show_toast(
                        "Wonder Linko",
                        f"「{item.get('title', '')}」を完了にしました。",
                        duration_sec=3,
                    )
        except Exception as e:
            log_info(f"[task_remind] ack failed: {e}")

    try:
        from ui.task_remind_dialog import show_task_remind_dialog

        show_task_remind_dialog(
            _miniport_window,
            items,
            slot,
            _ack,
            summary=summary or None,
            on_open_cards=open_linko_cards,
        )
    except Exception as e:
        log_info(f"[task_remind] dialog failed: {e}")
        try:
            from services.task_remind_client import notify_dialog_closed

            notify_dialog_closed()
        except Exception:
            pass


def _toggle_notifications(icon=None, item=None):
    global _config
    _config = load_config()
    _config["notifications_enabled"] = not _config.get("notifications_enabled", True)
    save_config(_config)
    notifications.set_notifications_enabled(_config["notifications_enabled"])
    on_off = "オン" if _config["notifications_enabled"] else "オフ"
    if not _config["notifications_enabled"]:
        try:
            from ui import linko_avatar

            linko_avatar.dismiss_ui()
        except Exception:
            pass
    notifications.show_toast(
        "Wonder Linko", f"通知を{on_off}にしました。", duration_sec=2, force_show=True
    )
    if _miniport_window is not None:
        try:
            _miniport_window.after(0, _miniport_window.refresh_notifications_button)
        except Exception:
            pass


def open_settings(icon=None, item=None):
    def _open():
        try:
            from ui.settings_dialog import open_settings_dialog

            open_settings_dialog(master=_miniport_window)
        except Exception as e:
            print("open_settings failed:", e, flush=True)

    if _miniport_window is not None:
        try:
            _miniport_window.after(0, _open)
            return
        except Exception:
            pass
    _open()


def quit_app(icon, item):
    if _miniport_window is not None:
        try:
            _miniport_window.after(0, on_closing)
        except Exception:
            on_closing()
    else:
        on_closing()


def _show_email_login_dialog() -> str | None:
    """メールアドレス入力ダイアログを表示し、入力値を返す。"""
    try:
        from ui.dialog_utils import ask_string_large

        return ask_string_large(
            "Wonder Linko - Board System ログイン",
            "Board System のパーソナルボードを開くには、登録済みのメールアドレスを入力してください:",
        )
    except Exception:
        return None


def build_menu(icon):
    return pystray.Menu(
        pystray.MenuItem("開く", open_tray_click_target, default=True),
        pystray.MenuItem("設定...", open_settings),
        pystray.MenuItem("ミニポートを表示", show_miniport),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("終了", quit_app),
    )


def run_tray():
    global _config, _icon
    _config = load_config()
    image = _make_icon_image()
    menu = build_menu(None)
    _icon = pystray.Icon("wonder_linko", image, f"Wonder Linko（v{__version__}）", menu)
    _icon.run()


def _show_display_name_dialog(current_name: str = "") -> str | None:
    try:
        from ui.dialog_utils import ask_string_large

        prompt = "ミニポートから投稿したときに付箋に表示する名前を入力してください:"
        if current_name:
            prompt += "\n（現在: " + current_name + "）"
        return ask_string_large(
            "Wonder Linko - 表示名", prompt, initial_value=current_name
        )
    except Exception:
        return None


def _prompt_display_name_if_empty():
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


def _prompt_board_system_login_if_needed() -> None:
    """起動時: board_system_url が設定済みで未ログインの場合にメール入力を促す。"""
    global _config
    board_url = (_config.get("board_system_url") or "").strip().rstrip("/")
    board_id = (_config.get("board_system_personal_id") or "").strip()
    if not board_url or board_id:
        return

    email = _show_email_login_dialog()
    if not email or "@" not in email:
        return

    from services.board_system_auth import login_with_email

    success, msg, _ = login_with_email(email, _config)
    if success:
        notifications.show_toast(
            "Wonder Linko",
            "Board System にログインしました。パーソナルは Board System のパーソナルボードを開きます。",
            duration_sec=4,
        )


def _wait_for_process_exit(pid: int):
    while True:
        try:
            os.kill(pid, 0)
        except (OSError, ProcessLookupError):
            break
        time.sleep(0.5)


def _launch_self():
    exe = sys.executable
    if getattr(sys, "frozen", False):
        flags = 0
        if sys.platform == "win32":
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.Popen([exe], creationflags=flags)
    else:
        args = [a for a in sys.argv[1:] if not a.startswith("--after-update-wait")]
        subprocess.Popen([exe, sys.argv[0]] + args)


def _sync_startup_setting():
    global _config
    if sys.platform != "win32":
        return
    try:
        taskmgr_disabled = startup.is_disabled_by_task_manager()
        shortcut_path = startup._get_shortcut_path()
        shortcut_exists = os.path.isfile(shortcut_path)

        if taskmgr_disabled:
            if _config.get("startup_enabled") is not False:
                _config["startup_enabled"] = False
                save_config(_config)
                log_info(
                    "[startup] タスクマネージャーでの無効化状態を検知し、設定を OFF に同期しました"
                )
        elif not shortcut_exists:
            if _config.get("startup_enabled", True):
                if startup.set_startup_enabled(True):
                    log_info("[startup] 初回スタートアップ自動登録を実行しました")
        else:
            if not _config.get("startup_enabled", True):
                _config["startup_enabled"] = True
                save_config(_config)
                log_info("[startup] OS側の有効状態に合わせて設定を ON に同期しました")
    except Exception as e:
        log_info(f"[startup] スタートアップ同期スキップ: {e}")


def main():
    global _config, _miniport_window, _miniport_visible

    # アプリ起動時に前回の強制終了などで残った自身のゴミ一時音声を一括削除
    cleanup_temp_audio_files(only_current_pid=False)

    for i, arg in enumerate(sys.argv):
        if arg == "--after-update-wait" and i + 1 < len(sys.argv):
            try:
                pid = int(sys.argv[i + 1])
                _wait_for_process_exit(pid)
                _launch_self()
            except (ValueError, OSError):
                pass
            return
        if arg.startswith("--after-update-wait="):
            try:
                pid = int(arg.split("=", 1)[1])
                _wait_for_process_exit(pid)
                _launch_self()
            except (ValueError, OSError):
                pass
            return

    if not _acquire_single_instance_lock():
        _signal_existing_instance_to_show()
        log_info(
            "既に Wonder Linko が起動中のため、ミニポートの前面化のみ依頼して終了します。"
        )
        return

    _config = load_config()

    _prompt_display_name_if_empty()
    _prompt_board_system_login_if_needed()

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

    _sync_startup_setting()

    try:
        import customtkinter as ctk
        from ui.mini_port import MiniPortWindow

        ctk.set_appearance_mode("system")

        def _miniport_on_hide():
            hide_miniport()

        def _miniport_on_notifications_toggle():
            _toggle_notifications()

        def _miniport_get_notifications_enabled():
            return notifications.are_enabled()

        _miniport_window = MiniPortWindow(
            on_hide=_miniport_on_hide,
            on_notifications_toggle=_miniport_on_notifications_toggle,
            get_notifications_enabled=_miniport_get_notifications_enabled,
        )
        notifications.set_ui_dispatch(
            lambda callback: _miniport_window.after(0, callback)
        )
        _miniport_visible = True

        try:
            _miniport_window.protocol("WM_DELETE_WINDOW", on_closing)
        except Exception:
            pass
    except Exception as e:
        _miniport_window = None
        _miniport_visible = False
        notifications.show_toast(
            "Wonder Linko",
            "ミニポートの起動に失敗しました: " + str(e)[:50],
            duration_sec=5,
        )

    tray_thread = threading.Thread(target=run_tray, daemon=True)
    tray_thread.start()

    _start_show_request_watcher()

    try:
        from services.task_remind_client import start_task_remind_poll

        start_task_remind_poll(
            lambda: _config,
            _on_task_remind_ui,
            tk_master=_miniport_window,
        )
        log_info("[task_remind] ポーリング開始")
    except Exception as e:
        log_info(f"[task_remind] 起動スキップ: {e}")

    try:
        from services.calendar_notify_client import start_calendar_notify_poll

        start_calendar_notify_poll(_on_calendar_remind_ui, tk_master=_miniport_window)
        log_info("[calendar_notify] ポーリング開始")
    except Exception as e:
        log_info(f"[calendar_notify] 起動スキップ: {e}")

    log_info("[visitor_notify] start_visitor_notify を呼ぶ準備中...")
    try:
        from services.visitor_notify_client import start_visitor_notify

        log_info("[visitor_notify] visitor_notify_client の import 成功")
        result = start_visitor_notify()
        log_info(f"[visitor_notify] start_visitor_notify 完了: result={result}")
    except Exception as e:
        import traceback

        log_info(f"[visitor_notify] 起動エラー: {e}")
        log_info(f"[visitor_notify] traceback:\n{traceback.format_exc()}")

    _cfg = load_config()
    _update_url = (_cfg.get("update_check_url") or "").strip()
    if _update_url:
        _network_host = (_cfg.get("update_network_check_host") or "").strip()
        _interval = int(_cfg.get("update_network_check_interval_sec") or 5)
        _max_wait = int(_cfg.get("update_network_check_max_wait_sec") or 180)

        def _startup_update_check():
            if _network_host or resolve_probe_url(_cfg):
                log_info("更新チェック: ネットワーク確立を待機中")
                if not wait_for_network(_network_host, _interval, _max_wait, cfg=_cfg):
                    return
            log_info("更新チェック開始: 起動時")
            logging.getLogger("WonderLinko").info("更新チェック開始: 起動時")

            def _on_startup_update_result(has_update, latest_version, download_url):
                if has_update:
                    log_info(
                        f"起動時更新チェック: 更新あり {latest_version} (手動更新待ち・ダイアログは出さない)"
                    )

            check_and_notify(__version__, _update_url, _on_startup_update_result)

    else:
        _startup_update_check = None

    if _update_url and _startup_update_check is not None:
        _update_thread = threading.Thread(target=_startup_update_check, daemon=True)
        _update_thread.start()

    if _miniport_window is not None:
        _miniport_window.mainloop()
    else:
        tray_thread.join()


if __name__ == "__main__":
    main()
