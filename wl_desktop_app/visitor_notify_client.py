# -*- coding: utf-8 -*-
"""Phase 3: 来客通知 SocketIO クライアント。

linko-system (受付サーバ) が ``visitor_arrived`` を全クライアントに broadcast する。
このモジュールはデスクトップ側で features.visitor_notify=True のとき接続して subscribe し、
受信したらトースト通知 + (opt-in なら) 音声再生を行う。

接続管理:
- features.visitor_notify=True のとき start() で接続スレッドを立ち上げ
- 切断時は python-socketio の reconnection を利用 (デフォルト無限再試行)
- features.visitor_notify=False に切り替えたら stop() で切断

利用側:
    from visitor_notify_client import start_visitor_notify, stop_visitor_notify
    start_visitor_notify()   # config を読んで判定し、必要なら接続開始

設計上の制約:
- python-socketio[client] は同期 API を持つ (Client クラス)。eventlet/asyncio に依存しない
- 接続スレッド (daemon) を作って .wait() でブロック
- audio_url は linko_server_url からの相対パス (/static/voices/xxx.wav) になっている想定
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import urllib.parse
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

try:
    import socketio as _sio
except ImportError:
    _sio = None

try:
    from app_log import log_info, log_warn
except Exception:  # pragma: no cover
    def log_info(msg: str) -> None:
        print(msg, flush=True)

    def log_warn(msg: str) -> None:
        print(msg, flush=True)


_client: Optional["_sio.Client"] = None
_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


# --- 公開 API ----------------------------------------------------------------


def start_visitor_notify() -> bool:
    """config.json を読んで features.visitor_notify=True のときだけ接続を開始する。

    既に接続済みなら何もしない。戻り値: 接続を開始したら True、スキップしたら False。
    """
    global _client, _thread

    log_info("[visitor_notify] start_visitor_notify() entered")

    if _sio is None:
        log_warn("[visitor_notify] python-socketio がインストールされていないため起動できません。")
        return False
    log_info(f"[visitor_notify] socketio loaded ok (version={getattr(_sio, '__version__', '?')})")

    try:
        from config_loader import load_config, is_feature_enabled
    except Exception as e:
        log_warn(f"[visitor_notify] config_loader 読み込み失敗: {e}")
        return False

    cfg = load_config()
    enabled = is_feature_enabled("visitor_notify", cfg)
    log_info(f"[visitor_notify] features.visitor_notify={enabled}")
    if not enabled:
        log_info("[visitor_notify] features.visitor_notify=False のためスキップ")
        return False

    url = (cfg.get("linko_server_url") or "").strip()
    log_info(f"[visitor_notify] linko_server_url={url!r}")
    if not url:
        log_warn("[visitor_notify] linko_server_url が空のため接続をスキップ。設定で URL を指定してください。")
        return False

    if _thread is not None and _thread.is_alive():
        log_info("[visitor_notify] 既に接続スレッドが動作中のためスキップ。")
        return False

    _stop_event.clear()
    _client = _sio.Client(
        reconnection=True,
        reconnection_attempts=0,  # 0 = 無限
        reconnection_delay=2,
        reconnection_delay_max=30,
    )
    _register_handlers(_client)

    def runner():
        try:
            log_info(f"[visitor_notify] {url} へ接続を試みます…")
            _client.connect(url, transports=["websocket", "polling"])
            log_info("[visitor_notify] connect() returned, waiting for events")
            _client.wait()
            log_info("[visitor_notify] wait() returned (loop ended)")
        except Exception as e:
            import traceback
            log_warn(f"[visitor_notify] 接続エラー: {e}")
            log_warn(f"[visitor_notify] traceback:\n{traceback.format_exc()}")

    _thread = threading.Thread(target=runner, name="visitor_notify_client", daemon=True)
    _thread.start()
    log_info("[visitor_notify] runner スレッドを起動しました")
    return True


def stop_visitor_notify() -> None:
    """接続を切る (features.visitor_notify を OFF にしたとき / アプリ終了時に呼ぶ)。"""
    global _client, _thread
    _stop_event.set()
    if _client is not None:
        try:
            _client.disconnect()
        except Exception:
            pass
    _client = None
    _thread = None


def is_running() -> bool:
    return _thread is not None and _thread.is_alive()


# --- 内部: ハンドラ登録 ------------------------------------------------------


def _register_handlers(c: "_sio.Client") -> None:
    @c.event
    def connect():
        log_info("[visitor_notify] connected.")

    @c.event
    def disconnect():
        log_info("[visitor_notify] disconnected.")

    @c.on("visitor_arrived")
    def on_visitor_arrived(data):
        try:
            _handle_visitor_arrived(data or {})
        except Exception as e:
            log_warn(f"[visitor_notify] visitor_arrived ハンドラエラー: {e}")


# --- 受信時の処理 -----------------------------------------------------------


def _handle_visitor_arrived(data: dict) -> None:
    """visitor_arrived payload を処理してトースト + (opt-in なら) 音声再生。"""
    name = (data.get("name") or "来客").strip() or "来客"
    location = (data.get("location") or "entrance").strip()
    message = (data.get("message") or f"{name} さんが来訪されました").strip()
    audio_url = (data.get("audio_url") or "").strip()

    title_map = {"entrance": "入口", "office_lobby": "ロビー", "meeting_room": "会議室"}
    title = title_map.get(location, "来客")

    log_info(f"[visitor_notify] visitor_arrived 受信: name={name} location={location} audio_url={audio_url!r}")

    # クリック時に開く URL (linko-board の entrance 画面)。これを渡すと winotify (Action Center) 経路で
    # 確実にトーストが出る (win10toast-click にフォールバックすると表示されない環境がある)。
    click_url = ""
    try:
        from config_loader import load_config
        click_url = (load_config().get("linko_server_url") or "").rstrip("/") + "/entrance"
    except Exception:
        pass

    # トースト
    try:
        from notifications import show_toast
        log_info(f"[visitor_notify] show_toast 呼び出し: title={title!r} click_url={click_url!r}")
        show_toast(title, message, url=click_url or None, duration_sec=8, force_show=False)
        log_info("[visitor_notify] show_toast 完了")
    except Exception as e:
        import traceback
        log_warn(f"[visitor_notify] トースト表示失敗: {e}")
        log_warn(f"[visitor_notify] traceback:\n{traceback.format_exc()}")

    # 音声 (opt-in)
    try:
        from config_loader import is_feature_enabled

        if is_feature_enabled("visitor_notify_sound") and audio_url:
            log_info("[visitor_notify] 音声再生を開始 (visitor_notify_sound=True)")
            _play_visitor_audio(audio_url)
        else:
            log_info(f"[visitor_notify] 音声再生スキップ (sound_enabled={is_feature_enabled('visitor_notify_sound')}, audio_url={'有り' if audio_url else '無し'})")
    except Exception as e:
        log_warn(f"[visitor_notify] 音声再生失敗: {e}")


def _play_visitor_audio(audio_url: str) -> None:
    """audio_url の WAV をダウンロードして winsound で再生 (Windows のみ)。
    audio_url は相対パスもしくは絶対 URL。相対なら linko_server_url を補う。
    """
    if requests is None:
        return
    if sys.platform != "win32":
        log_info("[visitor_notify] 音声再生は Windows のみ対応 (開発環境ではスキップ)。")
        return

    # 相対 URL を絶対に
    full_url = audio_url
    if not urllib.parse.urlparse(full_url).scheme:
        try:
            from config_loader import load_config

            base = (load_config().get("linko_server_url") or "").rstrip("/")
        except Exception:
            base = ""
        if base:
            full_url = base + (audio_url if audio_url.startswith("/") else "/" + audio_url)
        else:
            log_warn(f"[visitor_notify] audio_url が相対だが linko_server_url 未設定: {audio_url}")
            return

    try:
        r = requests.get(full_url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        log_warn(f"[visitor_notify] 音声ダウンロード失敗 ({full_url}): {e}")
        return

    fd, path = tempfile.mkstemp(suffix=".wav", prefix="linko_visitor_")
    try:
        os.close(fd)
        with open(path, "wb") as f:
            f.write(r.content)
        # winsound.SND_ASYNC で再生 (ブロックしない)
        import winsound

        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        # 一時ファイルは数十秒後に削除 (再生完了後)
        def _cleanup():
            import time as _t
            _t.sleep(30)
            try:
                os.unlink(path)
            except Exception:
                pass

        threading.Thread(target=_cleanup, daemon=True).start()
    except Exception as e:
        log_warn(f"[visitor_notify] 再生エラー: {e}")
        try:
            os.unlink(path)
        except Exception:
            pass
