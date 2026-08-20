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

import threading
from typing import Optional

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
        log_warn(
            "[visitor_notify] python-socketio がインストールされていないため起動できません。"
        )
        return False
    log_info(
        f"[visitor_notify] socketio loaded ok (version={getattr(_sio, '__version__', '?')})"
    )

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
        log_warn(
            "[visitor_notify] linko_server_url が空のため接続をスキップ。設定で URL を指定してください。"
        )
        return False
    try:
        from security import validate_http_url

        ok, err = validate_http_url(url, cfg, purpose="socketio_connect")
        if not ok:
            log_warn(f"[visitor_notify] linko_server_url を拒否: {err}")
            return False
    except Exception as e:
        log_warn(f"[visitor_notify] URL 検証エラー: {e}")
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
        """
        socketio.Client の reconnection=True は「接続後の切断」のみカバーし、
        **初回 connect() の失敗は再試行しない**。スリープ復帰時のネットワーク
        未確立、CATO/VPN 遅延、Flask 起動直後等で初回失敗するとそのまま諦めて
        二度と接続しない問題があるため、自前の retry loop でラップする。
        """
        import time as _time
        from network_readiness import is_network_ready, unreachable_backoff_sec
        from config_loader import load_config

        # backoff: 5s, 10s, 20s, 30s, 30s, ...
        backoff_schedule = [5, 10, 20, 30]
        attempt = 0
        while not _stop_event.is_set():
            cfg = load_config()
            if not is_network_ready(cfg):
                wait_sec = unreachable_backoff_sec(cfg)
                if attempt == 0 or attempt % 5 == 0:
                    log_info(
                        f"[visitor_notify] 社内ネットワーク未到達のため接続待機 ({wait_sec}秒)"
                    )
                for _ in range(wait_sec):
                    if _stop_event.is_set():
                        return
                    _time.sleep(1)
                continue
            attempt += 1
            try:
                log_info(
                    f"[visitor_notify] {url} へ接続を試みます… (attempt={attempt})"
                )
                _client.connect(url, transports=["websocket", "polling"])
                log_info("[visitor_notify] connect() returned, waiting for events")
                _client.wait()
                log_info("[visitor_notify] wait() returned (loop ended)")
                # client.wait() がリターン = 正常切断 or stop。次のループへ
                if _stop_event.is_set():
                    break
                # disconnect 後の reconnection は socketio 内蔵が処理。
                # ここに来たということは諦めて runner も終わるが、念のためリトライ
                attempt = 0  # 一度成功したのでカウンタリセット
            except Exception as e:
                import traceback

                log_warn(f"[visitor_notify] 接続エラー (attempt={attempt}): {e}")
                if attempt == 1:
                    # 初回失敗時だけ traceback を出す (以降の retry は短く)
                    log_warn(f"[visitor_notify] traceback:\n{traceback.format_exc()}")
            # backoff 待機
            wait_sec = backoff_schedule[min(attempt - 1, len(backoff_schedule) - 1)]
            log_info(f"[visitor_notify] {wait_sec}秒後に再試行します")
            for _ in range(wait_sec):
                if _stop_event.is_set():
                    return
                _time.sleep(1)

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
    try:
        from notifications import are_enabled

        if not are_enabled():
            log_info(
                "[visitor_notify] notifications_enabled=False のため来客通知をスキップ"
            )
            return
    except Exception:
        pass
    name = (data.get("name") or "来客").strip() or "来客"
    location = (data.get("location") or "entrance").strip()
    message = (data.get("message") or f"{name} さんが来訪されました").strip()
    # audio_text: 読み上げテキスト (吹き出し用)。無ければ message を流用。
    audio_text = (data.get("audio_text") or message or "").strip()
    audio_url = (data.get("audio_url") or "").strip()
    server_click_url = (data.get("click_url") or "").strip()
    action = (data.get("action") or "").strip()

    # セキュリティ警報（なりすまし疑いで開錠を止め、人間の確認を要求するイベント）。
    # 通常の来客通知とは重みが違うため、opt-in の音設定にも TTS 成否にも依存せず必ず鳴らし、
    # トーストも強制表示する（見逃すと不審者の入館を許しかねない）。
    is_security_alert = action == "unlock_failed"

    title_map = {"entrance": "入口", "office_lobby": "ロビー", "meeting_room": "会議室"}
    title = (
        "⚠️ 開錠失敗（要確認）" if is_security_alert else title_map.get(location, "来客")
    )

    log_info(
        f"[visitor_notify] visitor_arrived 受信: name={name} location={location} "
        f"audio_url={audio_url!r} click_url={server_click_url!r}"
    )

    # クリック時に開く URL の優先順:
    # 1. サーバが渡してきた click_url (Chatwork と同じ remote_unlock パネル URL)
    # 2. linko_server_url + /entrance (フォールバック)
    # url を渡すと winotify (Action Center) 経路で確実にトーストが出る
    # (win10toast-click にフォールバックすると表示されない環境がある)。
    try:
        from config_loader import load_config
        from security import filter_allowed_url

        cfg_notify = load_config()
        click_url = (
            filter_allowed_url(server_click_url, cfg_notify, purpose="visitor_click")
            if server_click_url
            else None
        )
        if not click_url:
            fallback = (cfg_notify.get("linko_server_url") or "").rstrip(
                "/"
            ) + "/entrance"
            click_url = (
                filter_allowed_url(fallback, cfg_notify, purpose="visitor_click") or ""
            )
    except Exception:
        click_url = ""

    # トースト
    try:
        from notifications import show_toast

        log_info(
            f"[visitor_notify] show_toast 呼び出し: title={title!r} click_url={click_url!r}"
        )
        show_toast(
            title,
            message,
            url=click_url or None,
            duration_sec=8,
            force_show=is_security_alert,
        )
        log_info("[visitor_notify] show_toast 完了")
    except Exception as e:
        import traceback

        log_warn(f"[visitor_notify] トースト表示失敗: {e}")
        log_warn(f"[visitor_notify] traceback:\n{traceback.format_exc()}")

    # セキュリティ警報は最優先で「必ず鳴る」音を出す（opt-in 設定にも TTS にも依存しない）。
    # TTS 音声が来ていれば、警報音のあとに重ねて読み上げる（無くても警報は既に鳴っている）。
    if is_security_alert:
        _play_security_alert()
        try:
            if audio_url:
                _play_visitor_audio(audio_url, audio_text=audio_text)
        except Exception as e:
            log_warn(
                f"[visitor_notify] セキュリティ警報の読み上げ失敗（警報音は再生済み）: {e}"
            )
        return

    # 通常の来客通知の音声 (opt-in) + アバター連動 (Phase 2.1: 吹き出し + 口パク)
    try:
        from config_loader import is_feature_enabled

        if is_feature_enabled("visitor_notify_sound") and audio_url:
            log_info("[visitor_notify] 音声再生を開始 (visitor_notify_sound=True)")
            _play_visitor_audio(audio_url, audio_text=audio_text)
        else:
            log_info(
                f"[visitor_notify] 音声再生スキップ (sound_enabled={is_feature_enabled('visitor_notify_sound')}, audio_url={'有り' if audio_url else '無し'})"
            )
    except Exception as e:
        log_warn(f"[visitor_notify] 音声再生失敗: {e}")


def _play_security_alert() -> None:
    """なりすまし疑い等のセキュリティ警報音。

    通常の来客通知（opt-in・TTS 依存）とは別に、**必ず鳴る**確実な警報を出す。
    winsound.Beep をアラームパターンで鳴らすため音源ファイル同梱は不要。TTS(VOICEVOX/
    GPT-SoVITS)が落ちていても、音設定が OFF でも鳴る。Beep はブロッキングなので
    バックグラウンドスレッドで実行し、socket ハンドラを止めない。Windows 以外は no-op。
    """
    import threading

    def _beep():
        try:
            import winsound

            # 高低を繰り返す明確なアラーム音（通常の通知と区別できるパターン）。
            for _ in range(3):
                winsound.Beep(880, 250)
                winsound.Beep(660, 200)
            log_info("[visitor_notify] セキュリティ警報音を再生（unlock_failed）")
        except Exception as e:
            log_warn(f"[visitor_notify] セキュリティ警報音の再生に失敗: {e}")

    threading.Thread(target=_beep, daemon=True).start()


def _play_visitor_audio(audio_url: str, audio_text: str = "") -> None:
    """audio_url の WAV をダウンロードして winsound で再生 (Windows のみ)。

    共有プレイヤ audio_player.play_linko_audio へ委譲 (来客通知とブレストチャットで共通化)。
    """
    from audio_player import play_linko_audio

    play_linko_audio(audio_url, text=audio_text, log_prefix="[visitor_notify]")
