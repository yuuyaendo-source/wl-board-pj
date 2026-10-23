# -*- coding: utf-8 -*-
"""
アバター吹き出し通知への一括ディスパッチ（OSネイティブトースト廃止・吹き出し一本化）。
"""
from typing import Callable, Optional
import threading

from core.config_loader import is_feature_enabled, load_config
from core.security import filter_allowed_url
from core.app_log import log_info, log_warn

_last_url: Optional[str] = None
_ui_dispatch: Optional[Callable[[Callable[[], None]], None]] = None
_pending_notifications: list[dict] = []
_queue_lock = threading.Lock()


def set_ui_dispatch(dispatch_fn: Callable[[Callable[[], None]], None]) -> None:
    """UI ディスパッチ関数を登録し、保留中の通知があればフラッシュする。"""
    global _ui_dispatch
    _ui_dispatch = dispatch_fn
    flush_pending_notifications()


def flush_pending_notifications() -> None:
    """起動前などにキューイングされていた通知を順次ディスパッチする。"""
    global _pending_notifications
    if not _ui_dispatch:
        return

    with _queue_lock:
        if not _pending_notifications:
            return
        queue = list(_pending_notifications)
        _pending_notifications.clear()

    log_info(f"[Notify] 保留中通知をフラッシュします ({len(queue)}件)")
    for item in queue:
        show_toast(
            title=item["title"],
            msg=item["msg"],
            url=item.get("url"),
            duration_sec=item.get("duration_sec", 8),
            force_show=item.get("force_show", False),
        )


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

    # UI ディスパッチャが未登録（アプリ起動直後など）の場合はキューに保留
    if not _ui_dispatch:
        with _queue_lock:
            _pending_notifications.append(
                {
                    "title": title,
                    "msg": msg,
                    "url": safe_url,
                    "duration_sec": duration_sec,
                    "force_show": force_show,
                }
            )
        log_info(f"[Notify] UI未準備のため通知をキューに保留: title={title!r}")
        return

    def _trigger(retries_left: int = 15):
        try:
            from ui import linko_avatar

            # 吹き出し（_speech_bubble）がまだ登録されていない場合は、別スレッドタイマーで待機して再試行
            bubble = getattr(linko_avatar, "_speech_bubble", None)
            if bubble is None:
                if retries_left > 0 and _ui_dispatch:
                    t = threading.Timer(
                        0.5,
                        lambda: (
                            _ui_dispatch(lambda: _trigger(retries_left - 1))
                            if _ui_dispatch
                            else None
                        ),
                    )
                    t.daemon = True
                    t.start()
                    return
                else:
                    log_warn(
                        f"[Notify] 吹き出し未準備のため通知表示を中断: title={title!r}"
                    )
                    return

            # タイトルが存在する場合は先頭に付与して吹き出しに反映
            display_text = f"【{title}】\n{msg}" if title else msg

            if is_feature_enabled("linko_avatar", cfg) and linko_avatar.is_ready():
                # OSネイティブトーストの代わりに、吹き出し(スタンドアロン)として一時表示
                linko_avatar.say(
                    text=display_text,
                    duration_sec=float(duration_sec),
                    standalone=True,
                    force_show=force_show,
                )
            else:
                # アバター機能が無効・未準備の場合のフォールバック (吹き出しのみを表示)
                linko_avatar.say(
                    text=display_text,
                    duration_sec=float(duration_sec),
                    lipsync=False,
                    standalone=True,
                    force_show=force_show,
                )
            log_info(f"[Notify] 吹き出し通知表示成功: title={title!r}")
        except Exception as e:
            log_info(f"[Notify] avatar say 失敗: {e}")

    _ui_dispatch(lambda: _trigger(15))


def open_last_notification() -> bool:
    global _last_url
    if not _last_url:
        return False
    from core.security import safe_webbrowser_open

    safe_webbrowser_open(_last_url, load_config())
    return True
