# -*- coding: utf-8 -*-
"""リン子音声の共有プレイヤ。"""
from __future__ import annotations

import glob
import os
import sys
import tempfile
import threading
import urllib.parse
from typing import Optional, Tuple

try:
    import requests
except ImportError:
    requests = None

from core.config_loader import load_config, is_feature_enabled
from core.security import validate_http_url, assert_http_url
from services.notifications import are_enabled
from core.app_log import log_info, log_warn


def get_audio_temp_prefix() -> str:
    """自プロセスの PID をプレフィックスに含めて他プロセスと独立管理。"""
    return f"linko_audio_{os.getpid()}_"


def cleanup_temp_audio_files(only_current_pid: bool = True) -> None:
    """
    一時音声ファイル（*.wav）を削除する。
    only_current_pid=True : 自身のPIDのファイルのみ削除（アプリ終了時用。既定）
    only_current_pid=False: 過去の強制終了ゴミを含めてすべての自アプリ一時ファイルを削除（アプリ起動時用）
    """
    if only_current_pid:
        pattern = os.path.join(tempfile.gettempdir(), f"{get_audio_temp_prefix()}*.wav")
    else:
        pattern = os.path.join(tempfile.gettempdir(), "linko_audio_*.wav")

    for path in glob.glob(pattern):
        try:
            os.unlink(path)
        except Exception:
            pass


def _resolve_url(audio_url: str, log_prefix: str) -> Optional[str]:
    full_url = audio_url
    if not urllib.parse.urlparse(full_url).scheme:
        base = (load_config().get("linko_server_url") or "").strip().rstrip("/")
        if base:
            full_url = base + (
                audio_url if audio_url.startswith("/") else "/" + audio_url
            )
        else:
            log_warn(
                f"{log_prefix} audio_url が相対だが linko_server_url 未設定: {audio_url}"
            )
            return None

    try:
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
    """audio_url の WAV をダウンロードして一時ファイルへ保存。"""
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

    fd, path = tempfile.mkstemp(suffix=".wav", prefix=get_audio_temp_prefix())
    os.close(
        fd
    )  # Windows でのファイルロックを防ぐため即座にファイルディスクリプタを閉じる

    try:
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
    if not are_enabled():
        return
    try:
        if is_feature_enabled("linko_avatar"):
            from ui import linko_avatar

            if linko_avatar.is_ready():
                if duration_sec is not None and duration_sec > 0:
                    linko_avatar.say(
                        text=text, duration_sec=duration_sec, base_pose="normal"
                    )
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
    """一時 WAV を winsound で再生 (Windows のみ)。"""
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
            winsound.PlaySound(path, winsound.SND_FILENAME)
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


def _tts_api_url() -> Optional[str]:
    base = (load_config().get("linko_server_url") or "").strip().rstrip("/")
    return f"{base}/api/v2/tts" if base else None


def speak_text(text: str, log_prefix: str = "[remind_voice]") -> None:
    if requests is None or not (text or "").strip():
        return
    url = _tts_api_url()
    if not url:
        log_info(f"{log_prefix} linko_server_url 未設定のため音声スキップ")
        return
    try:
        assert_http_url(url, load_config(), purpose="remind_tts")
    except ValueError as e:
        log_warn(f"{log_prefix} TTS URL 拒否: {e}")
        return
    except Exception as e:
        log_warn(f"{log_prefix} TTS URL 検証エラー: {e}")
        return
    try:
        r = requests.post(url, json={"text": text.strip()}, timeout=(5, 60))
        if r.status_code == 503:
            log_info(f"{log_prefix} TTS 混雑のため音声スキップ (503)")
            return
        if r.status_code != 200:
            log_warn(f"{log_prefix} TTS HTTP {r.status_code}")
            return
        audio_url = (r.json() or {}).get("audio_url")
    except Exception as e:
        log_warn(f"{log_prefix} TTS 取得失敗: {e}")
        return
    if not audio_url:
        return
    res = download_linko_wav(audio_url, log_prefix=log_prefix)
    if not res:
        return
    path, duration_sec = res
    play_wav(
        path,
        text=text.strip(),
        duration_sec=duration_sec,
        blocking=False,
        log_prefix=log_prefix,
    )


def play_linko_audio(
    audio_url: str, text: str = "", log_prefix: str = "[audio]"
) -> None:
    if requests is None:
        return
    res = download_linko_wav(audio_url, log_prefix=log_prefix)
    if not res:
        return
    path, duration_sec = res
    play_wav(
        path,
        text=text,
        duration_sec=duration_sec,
        blocking=False,
        log_prefix=log_prefix,
    )
