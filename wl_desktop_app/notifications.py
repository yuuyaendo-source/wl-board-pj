# -*- coding: utf-8 -*-
"""
トースト通知（右下・業務の邪魔にならない表示）。
「最後のお知らせURL」を保存し、トレイメニュー「最後のお知らせを開く」でワンクリックDeep Link。
デザイン: winotify ではアイコン（PNG/ICO）を指定可能。config の toast_icon_path で変更可。
"""
import os
import webbrowser
import sys

_last_notification_url = None
_fallback_toasts = []
_ui_dispatch = None


def set_ui_dispatch(dispatch) -> None:
    """Tk のメインスレッドでフォールバック通知を作るためのディスパッチャー。"""
    global _ui_dispatch
    _ui_dispatch = dispatch if callable(dispatch) else None


def are_enabled(cfg=None) -> bool:
    """アプリ内の通知表示が ON か (トースト・吹き出し・来客通知などの総合スイッチ)。"""
    try:
        if cfg is None:
            from config_loader import load_config

            cfg = load_config()
        return bool(cfg.get("notifications_enabled", True))
    except Exception:
        return True


def get_last_notification_url():
    return _last_notification_url


def clear_last_notification_url():
    global _last_notification_url
    _last_notification_url = None


def _open_last_notification_url():
    """最後のお知らせURLをブラウザで開く（トーストクリック時など）。"""
    url = get_last_notification_url()
    if url:
        from security import safe_webbrowser_open

        safe_webbrowser_open(url)


def _get_toast_icon_path():
    """
    トースト用アイコンの絶対パスを返す。
    config の toast_icon_path があればそれを使い、なければデフォルト（トレイと同じデザイン）を生成して返す。
    """
    try:
        from config_loader import load_config, get_app_base_dir

        cfg = load_config()
        path = (cfg.get("toast_icon_path") or "").strip()
        if path:
            base = get_app_base_dir()
            if not os.path.isabs(path):
                path = os.path.join(base, path)
            if os.path.isfile(path):
                return os.path.abspath(path)
        path = ""
    except Exception:
        path = ""

    try:
        from config_loader import get_app_base_dir

        app_dir = get_app_base_dir()
    except Exception:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    for candidate in (
        os.path.join(app_dir, "assets", "toast_icon.png"),
        os.path.join(app_dir, "toast_icon.png"),
    ):
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
    default_path = os.path.join(app_dir, "toast_icon.png")
    if not os.path.isfile(default_path):
        try:
            from PIL import Image, ImageDraw

            size = 256
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse(
                [4, 4, size - 4, size - 4], fill=(0, 200, 120), outline=(0, 255, 200)
            )
            d.ellipse(
                [size // 4, size // 4, size - size // 4, size - size // 4],
                fill=(0, 60, 40),
            )
            img.save(default_path)
        except Exception:
            return None
    return os.path.abspath(default_path)


def _show_fallback_toast(title: str, message: str, url: str, duration_sec: int):
    """【課題3対応】winotify失敗・ブロック環境向けの自前UIトーストフォールバック。
    フォーカスを奪わず、連続発生時は古いものを閉じてスタッキング表示を制御する。
    """
    import customtkinter as ctk

    global _fallback_toasts

    # 既存のトーストがあれば破棄（スタッキング制御）
    for t in _fallback_toasts:
        try:
            t.destroy()
        except Exception:
            pass
    _fallback_toasts.clear()

    win = ctk.CTkToplevel()
    win.title("Wonder Linko 通知")
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    try:
        # フォーカスを奪わないための設定
        win.attributes("-toolwindow", True)
    except Exception:
        pass

    _fallback_toasts.append(win)

    frame = ctk.CTkFrame(win, fg_color="#333333", corner_radius=8)
    frame.pack(fill="both", expand=True)

    lbl_title = ctk.CTkLabel(
        frame,
        text=title or "Wonder Linko",
        font=("", 13, "bold"),
        text_color="#ffffff",
        anchor="w",
    )
    lbl_title.pack(fill="x", padx=12, pady=(12, 4))

    lbl_msg = ctk.CTkLabel(
        frame,
        text=message,
        font=("", 12),
        text_color="#eeeeee",
        anchor="w",
        justify="left",
    )
    lbl_msg.pack(fill="x", padx=12, pady=(0, 12))

    def _open_and_close():
        if url:
            from security import safe_webbrowser_open

            safe_webbrowser_open(url)
        try:
            win.destroy()
        except Exception:
            pass

    if url:
        btn = ctk.CTkButton(
            frame,
            text="開く",
            command=_open_and_close,
            fg_color="#2563eb",
            width=60,
            height=24,
        )
        btn.pack(side="right", padx=12, pady=(0, 12))

    win.update_idletasks()
    w = win.winfo_reqwidth()
    h = win.winfo_reqheight()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = sw - w - 20
    y = sh - h - 60
    win.geometry(f"{w}x{h}+{x}+{y}")

    win.after(duration_sec * 1000, lambda: _close_fallback_toast(win))


def _close_fallback_toast(win):
    global _fallback_toasts
    try:
        win.destroy()
    except Exception:
        pass
    if win in _fallback_toasts:
        _fallback_toasts.remove(win)


def _schedule_fallback_toast(title: str, message: str, url: str | None, duration_sec: int) -> None:
    """通知元スレッドにかかわらず、Tk のUIスレッドで代替トーストを表示する。"""
    show = lambda: _show_fallback_toast(title, message, url, duration_sec)
    if _ui_dispatch is not None:
        _ui_dispatch(show)
        return
    show()


def show_toast(
    title: str,
    message: str,
    url: str = None,
    duration_sec: int = 8,
    force_show: bool = False,
):
    """
    右下にトーストを表示する。
    url を渡すと保存し、表示中にクリックするとそのお知らせへ飛べる。
    アプリ設定で notifications_enabled が False の場合は表示しない（URL は保存する）。
    force_show=True のときは設定を無視して表示（通知オン/オフの確認メッセージ用）。
    """
    global _last_notification_url
    if url:
        try:
            from config_loader import load_config
            from security import filter_allowed_url

            url = filter_allowed_url(url, load_config(), purpose="toast")
        except Exception:
            url = None
        if url:
            _last_notification_url = url

    if not force_show and not are_enabled():
        return

    if sys.platform == "win32":
        try:
            from winotify import Notification

            icon_path = _get_toast_icon_path()
            kwargs = {
                "app_id": "WonderLinko.Desktop",
                "title": title or "Wonder Linko",
                "msg": message,
            }
            if icon_path:
                kwargs["icon"] = icon_path
            toast = Notification(**kwargs)
            if url:
                toast.add_actions(label="開く", launch=url)
            toast.show()
            return
        except Exception as _toast_err:
            _err_msg = f"[Notify] winotify 失敗: {_toast_err} -> 自前フォールバックUIを表示します"
            try:
                from app_log import log_info

                log_info(_err_msg)
            except Exception:
                print(_err_msg, flush=True)

            _schedule_fallback_toast(title, message, url, duration_sec)
            return

    print(f"[Notify] {title}: {message}")
    if url:
        from security import safe_webbrowser_open

        safe_webbrowser_open(url)


def open_last_notification():
    """最後のお知らせURLをブラウザで開く。"""
    url = get_last_notification_url()
    if url:
        from security import safe_webbrowser_open

        return safe_webbrowser_open(url)
    return False
