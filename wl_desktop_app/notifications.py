# -*- coding: utf-8 -*-
"""
トースト通知（右下・業務の邪魔にならない表示）。
「最後のお知らせURL」を保存し、トレイメニュー「最後のお知らせを開く」でワンクリックDeep Link。
デザイン: winotify ではアイコン（PNG/ICO）を指定可能。config の toast_icon_path で変更可。
"""
import os
import webbrowser
import sys

# 最後に表示したお知らせのURL（トーストクリック・トレイの「最後のお知らせを開く」で開く）
_last_notification_url = None


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
    # デフォルト: 新 assets/toast_icon.png を優先。なければ旧 top-level、最終フォールバックとして
    # 緑の丸デザインの PNG を自動生成（exe 時は exe と同じフォルダ）
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
            d.ellipse([4, 4, size - 4, size - 4], fill=(0, 200, 120), outline=(0, 255, 200))
            d.ellipse([size // 4, size // 4, size - size // 4, size - size // 4], fill=(0, 60, 40))
            img.save(default_path)
        except Exception:
            return None
    return os.path.abspath(default_path)


def show_toast(title: str, message: str, url: str = None, duration_sec: int = 8, force_show: bool = False):
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
        # 1) winotify（「開く」ボタンでURLを開く・ワンクリックで確実・アイコン指定可）
        if url:
            try:
                from winotify import Notification
                icon_path = _get_toast_icon_path()
                # app_id を変えると Windows が「別アプリ」と扱う。通知オフで復旧しない場合の対策で WonderLinko.Desktop に変更
                kwargs = {
                    "app_id": "WonderLinko.Desktop",
                    "title": title or "Wonder Rinko",
                    "msg": message,
                }
                if icon_path:
                    kwargs["icon"] = icon_path
                toast = Notification(**kwargs)
                toast.add_actions(label="開く", launch=url)
                toast.show()
                return
            except Exception:
                pass
        # 2) win10toast-click（トースト本体クリックで開く）
        try:
            from win10toast_click import ToastNotifier
            toaster = ToastNotifier()
            kwargs = {
                "title": title or "リン子のお知らせ",
                "msg": message + ("\n（クリックで開く）" if url else ""),
                "duration": duration_sec,
                "threaded": True,
            }
            if url:
                kwargs["callback_on_click"] = _open_last_notification_url
            toaster.show_toast(**kwargs)
            return
        except Exception:
            pass
        # 3) フォールバック: win10toast（表示のみ・トレイの「最後のお知らせを開く」で開く）
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title=title or "Wonder Rinko",
                msg=message + ("\n（トレイの「最後のお知らせを開く」で開く）" if url else ""),
                duration=duration_sec,
                threaded=True,
            )
            return
        except Exception:
            pass
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
