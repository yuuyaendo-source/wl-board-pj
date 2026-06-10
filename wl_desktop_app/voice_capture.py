# -*- coding: utf-8 -*-
"""マイクから音声サンプルを録音し WAV data URL を返す（将来の話者照合用）。"""
from __future__ import annotations

import base64
import io
import sys
import wave
from typing import Optional

try:
    import sounddevice as sd
except ImportError:
    sd = None  # type: ignore

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_DURATION_SEC = 4.0


def is_available() -> bool:
    if sd is None or np is None:
        return False
    if sys.platform != "win32":
        return False
    return True


def record_wav_data_url(
    duration_sec: float = DEFAULT_DURATION_SEC,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> Optional[str]:
    """マイクから指定秒数録音し `data:audio/wav;base64,...` を返す。"""
    if not is_available():
        return None
    frames = int(max(0.5, duration_sec) * sample_rate)
    try:
        recording = sd.rec(
            frames,
            samplerate=sample_rate,
            channels=DEFAULT_CHANNELS,
            dtype="int16",
        )
        sd.wait()
    except Exception:
        return None
    if recording is None or getattr(recording, "size", 0) == 0:
        return None
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(DEFAULT_CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())
    raw = buf.getvalue()
    if len(raw) < 44:
        return None
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:audio/wav;base64,{b64}"
