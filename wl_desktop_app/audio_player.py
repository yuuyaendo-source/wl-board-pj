# -*- coding: utf-8 -*-
"""リン子音声の共有プレイヤ。

linko-system が配信する WAV (来客通知の audio_url・ブレストチャットの TTS など) を
ダウンロードし、URL 許可リストで検証したうえで winsound で再生する (Windows のみ)。
``features.linko_avatar`` 有効時は WAV の長さに合わせて吹き出し + 口パクを同期させる。

visitor_notify_client._play_visitor_audio から共通ロジックを抽出したもの。来客通知・
ブレストチャットの双方から ``play_linko_audio()`` を呼ぶ。
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import urllib.parse

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    from app_log import log_info, log_warn
except Exception:  # pragma: no cover
    def log_info(msg: str) -> None:
        print(msg, flush=True)

    def log_warn(msg: str) -> None:
        print(msg, flush=True)


def play_linko_audio(audio_url: str, text: str = "", log_prefix: str = "[audio]") -> None:
    """audio_url の WAV をダウンロードして winsound で再生 (Windows のみ)。

    - audio_url は相対パスもしくは絶対 URL。相対なら config の linko_server_url を補う。
    - text を渡すと features.linko_avatar=True のとき吹き出し + 口パクを音声長に同期。
    - URL は security.validate_http_url の許可リスト (.internal.wonder-link.com 等) で検証。
    - 失敗時は警告ログを残して静かに return (呼び出し側を壊さない)。
    """
    if requests is None:
        return
    if sys.platform != "win32":
        log_info(f"{log_prefix} 音声再生は Windows のみ対応 (開発環境ではスキップ)。")
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
            log_warn(f"{log_prefix} audio_url が相対だが linko_server_url 未設定: {audio_url}")
            return

    try:
        from config_loader import load_config
        from security import validate_http_url

        ok, err = validate_http_url(full_url, load_config(), purpose="linko_audio")
        if not ok:
            log_warn(f"{log_prefix} 音声 URL を拒否: {err} ({full_url!r})")
            return
    except Exception as e:
        log_warn(f"{log_prefix} 音声 URL 検証エラー: {e}")
        return

    try:
        r = requests.get(full_url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        log_warn(f"{log_prefix} 音声ダウンロード失敗 ({full_url}): {e}")
        return

    fd, path = tempfile.mkstemp(suffix=".wav", prefix="linko_audio_")
    try:
        os.close(fd)
        with open(path, "wb") as f:
            f.write(r.content)
        # WAV の長さを計算して lipsync を同期
        duration_sec = None
        try:
            import wave as _wave
            with _wave.open(path, "rb") as _wf:
                _frames = _wf.getnframes()
                _rate = _wf.getframerate()
                if _rate:
                    duration_sec = _frames / float(_rate)
        except Exception:
            duration_sec = None

        # features.linko_avatar=True なら 吹き出し + 口パク を同時開始
        try:
            from config_loader import is_feature_enabled
            if is_feature_enabled("linko_avatar"):
                import linko_avatar
                if linko_avatar.is_ready():
                    if duration_sec is not None and duration_sec > 0:
                        # text があれば吹き出しに表示 + lipsync。無ければ lipsync のみ
                        linko_avatar.say(
                            text=text,
                            duration_sec=duration_sec,
                            base_pose="normal",
                        )
                    else:
                        linko_avatar.start_lipsync(duration_sec=None, base_pose="normal")
        except Exception as _e:
            log_warn(f"{log_prefix} lipsync/bubble start 失敗: {_e}")

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
        log_warn(f"{log_prefix} 再生エラー: {e}")
        try:
            os.unlink(path)
        except Exception:
            pass
