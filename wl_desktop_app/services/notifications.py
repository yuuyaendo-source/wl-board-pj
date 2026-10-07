# -*- coding: utf-8 -*-
"""
アバター吹き出し通知への一括ディスパッチ（OSネイティブトースト廃止・吹き出し一本化）。
"""
import threading
from typing import Callable, Optional

from core.config_loader import is_feature_enabled, load_config
from core.security import filter_allowed_url
from core.app_log import log_info

_last_url: Optional[str] = None
_ui_dispatch: Optional[Callable[[Callable[[], None]], None]] = None


def set_ui_dispatch(dispatch_fn: Callable[[Callable[[], None]], None]) -> None:
    global _ui_dispatch
    _ui_dispatch = dispatch_fn


_enabled_cache: Optional[bool] = None


def set_notifications_enabled(val: bool) -> None:
    """通知有効フラグのインメモリキャッシュを明示的に更新する。"""
    global _enabled_cache
    _enabled_cache = val


def are_enabled(refresh: bool = False) -> bool:
    """通知が有効かどうかを返す（キャッシュを使用しファイルI/Oを削減）。"""
    global _enabled_cache
    if _enabled_cache is not None and not refresh:
        return _enabled_cache
    _enabled_cache = bool(load_config().get("notifications_enabled", True))
    return _enabled_cache


def show_toast(
    title: str,
    msg: str,
    url: Optional[str] = None,
    duration_sec: int = 8,
    force_show: bool = False,
) -> None:
    global _last_url
    if not are_enabled() and not force_show:
        return

    cfg = load_config()
    safe_url = filter_allowed_url(url, cfg, purpose="toast") if url else None
    if safe_url:
        _last_url = safe_url

    if _ui_dispatch:

        def _trigger():
            try:
                from ui import linko_avatar

                if is_feature_enabled("linko_avatar", cfg) and linko_avatar.is_ready():
                    # OSネイティブトーストの代わりに、吹き出し(スタンドアロン)として一時表示
                    linko_avatar.say(
                        text=msg, duration_sec=float(duration_sec), standalone=True
                    )
            except Exception as e:
                log_info(f"[Notify] avatar say 失敗: {e}")

        _ui_dispatch(_trigger)


def open_last_notification() -> bool:
    global _last_url
    if not _last_url:
        return False
    from core.security import safe_webbrowser_open

    safe_webbrowser_open(_last_url, load_config())
    return True
