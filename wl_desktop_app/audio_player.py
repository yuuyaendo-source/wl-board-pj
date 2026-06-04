# -*- coding: utf-8 -*-
"""リン子音声の共有プレイヤ。

linko-system が配信する WAV (来客通知の audio_url・ブレストチャットの TTS など) を
ダウンロードし、URL 許可リストで検証したうえで winsound で再生する (Windows のみ)。
``features.linko_avatar`` 有効時は WAV の長さに合わせて吹き出し + 口パクを同期させる。

- play_linko_audio: ダウンロード→非同期再生 (来客通知・全文一括用)。
- download_linko_wav / play_wav: 文単位ストリーミング再生のため fetch と play を分離した部品。
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import urllib.parse
from typing import Optional, Tuple

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


def _resolve_url(audio_url: str, log_prefix: str) -> Optional[str]:
    """相対 URL を linko_server_url で補完し、許可リストで検証して絶対 URL を返す。"""
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
            return None

    try:
        from config_loader import load_config
        from security import validate_http_url

        ok, err = validate_http_url(full_url, load_config(), purpose="linko_audio")
        if not ok:
            log_warn(f"{log_prefix} 音声 URL を拒否: {err} ({full_url!r})")
            return None
    except Exception as e:
        log_warn(f"{log_prefix} 音声 URL 検証エラー: {e}")
        return None
    return full_url


def download_linko_wav(
    audio_url: str, log_prefix: str = "[audio]", timeout: int = 20
) -> Optional[Tuple[str, Optional[float]]]:
    """audio_url の WAV をダウンロードして一時ファイルへ保存。(path, duration_sec) を返す。

    失敗時は None。呼び出し側で path を再生後に削除すること。
    """
    if requests is None:
        return None
    full_url = _resolve_url(audio_url, log_prefix)
    if not full_url:
        return None
    try:
        r = requests.get(full_url, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        log_warn(f"{log_prefix} 音声ダウンロード失敗 ({full_url}): {e}")
        return None

    fd, path = tempfile.mkstemp(suffix=".wav", prefix="linko_audio_")
    try:
        os.close(fd)
        with open(path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        log_warn(f"{log_prefix} 音声保存失敗: {e}")
        try:
            os.unlink(path)
        except Exception:
            pass
        return None

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
    return path, duration_sec


def _start_avatar(text: str, duration_sec: Optional[float], log_prefix: str) -> None:
    """features.linko_avatar=True なら 吹き出し + 口パク を音声長に同期して開始。"""
    try:
        from config_loader import is_feature_enabled
        if is_feature_enabled("linko_avatar"):
            import linko_avatar
            if linko_avatar.is_ready():
                if duration_sec is not None and duration_sec > 0:
                    linko_avatar.say(text=text, duration_sec=duration_sec, base_pose="normal")
                else:
                    linko_avatar.start_lipsync(duration_sec=None, base_pose="normal")
    except Exception as e:
        log_warn(f"{log_prefix} lipsync/bubble start 失敗: {e}")


def play_wav(
    path: str,
    text: str = "",
    duration_sec: Optional[float] = None,
    blocking: bool = False,
    log_prefix: str = "[audio]",
) -> None:
    """一時 WAV を winsound で再生 (Windows のみ)。再生後に一時ファイルを削除する。

    - blocking=False: SND_ASYNC で再生し、30 秒後に削除 (来客通知・単発用)。
    - blocking=True : 再生完了までブロックし、終了後すぐ削除 (文ストリーミングの順次再生用)。
    """
    if sys.platform != "win32":
        log_info(f"{log_prefix} 音声再生は Windows のみ対応 (開発環境ではスキップ)。")
        try:
            os.unlink(path)
        except Exception:
            pass
        return
    try:
        _start_avatar(text, duration_sec, log_prefix)
        import winsound

        if blocking:
            winsound.PlaySound(path, winsound.SND_FILENAME)  # 再生完了までブロック
            try:
                os.unlink(path)
            except Exception:
                pass
        else:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)

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


def play_linko_audio(audio_url: str, text: str = "", log_prefix: str = "[audio]") -> None:
    """audio_url の WAV をダウンロードして winsound で非同期再生する (来客通知・全文一括用)。

    失敗時は警告ログを残して静かに return (呼び出し側を壊さない)。
    """
    if requests is None:
        return
    res = download_linko_wav(audio_url, log_prefix=log_prefix)
    if not res:
        return
    path, duration_sec = res
    play_wav(path, text=text, duration_sec=duration_sec, blocking=False, log_prefix=log_prefix)
