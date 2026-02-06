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


def get_last_notification_url():
    return _last_notification_url


def clear_last_notification_url():
    global _last_notification_url
    _last_notification_url = None


def _open_last_notification_url():
    """最後のお知らせURLをブラウザで開く（トーストクリック時など）。"""
    url = get_last_notification_url()
    if url:
        webbrowser.open(url)


def _get_toast_icon_path():
    """
    トースト用アイコンの絶対パスを返す。
    config の toast_icon_path があればそれを使い、なければデフォルト（トレイと同じデザイン）を生成して返す。
    """
    try:
        from config_loader import load_config, CONFIG_PATH
        cfg = load_config()
        path = (cfg.get("toast_icon_path") or "").strip()
        if path:
            if not os.path.isabs(path):
                path = os.path.join(os.path.dirname(CONFIG_PATH), path)
            if os.path.isfile(path):
                return os.path.abspath(path)
        path = ""
    except Exception:
        path = ""
    # デフォルト: アプリと同じ緑の丸デザインの PNG を生成
    app_dir = os.path.dirname(os.path.abspath(__file__))
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


def show_toast(title: str, message: str, url: str = None, duration_sec: int = 8):
    """
    右下にトーストを表示する。
    url を渡すと保存し、表示中にクリックするとそのお知らせへ飛べる。
    """
    global _last_notification_url
    if url:
        _last_notification_url = url

    if sys.platform == "win32":
        # 1) winotify（「開く」ボタンでURLを開く・ワンクリックで確実・アイコン指定可）
        if url:
            try:
                from winotify import Notification
                icon_path = _get_toast_icon_path()
                kwargs = {
                    "app_id": "Wonder Rinko",
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
        webbrowser.open(url)


def open_last_notification():
    """最後のお知らせURLをブラウザで開く。"""
    url = get_last_notification_url()
    if url:
        webbrowser.open(url)
        return True
    return False
