# -*- coding: utf-8 -*-
"""Webカメラからプレビュー・JPEG data URL 取得（社員顔登録用）。"""
from __future__ import annotations

import base64
import sys
from typing import Any, Optional

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore


def is_available() -> bool:
    """OpenCV が import でき、Windows 等でカメラ利用の前提を満たすか。"""
    if cv2 is None or Image is None:
        return False
    if sys.platform != "win32":
        return False
    return True


def _try_open(device_index: int, backend: int) -> Any:
    if cv2 is None:
        return None
    cap = cv2.VideoCapture(device_index, backend)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    for _ in range(8):
        cap.read()
    ok, frame = cap.read()
    if not ok or frame is None or getattr(frame, "size", 0) == 0:
        cap.release()
        return None
    return cap


def open_camera(device_index: int = 0) -> Any:
    """VideoCapture を開く。失敗時は None。複数デバイス・バックエンドを試す。"""
    if not is_available():
        return None
    backends: list[int] = []
    if sys.platform == "win32":
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    else:
        backends = [cv2.CAP_ANY]
    indices = [device_index] + [i for i in range(4) if i != device_index]
    for idx in indices:
        for backend in backends:
            cap = _try_open(idx, backend)
            if cap is not None:
                return cap
    return None


def release_camera(cap: Any) -> None:
    if cap is None:
        return
    try:
        cap.release()
    except Exception:
        pass


def read_bgr_frame(cap: Any) -> Optional[Any]:
    """1 フレーム BGR。失敗時 None。"""
    if cap is None or cv2 is None:
        return None
    ok, frame = cap.read()
    if not ok or frame is None or getattr(frame, "size", 0) == 0:
        return None
    return frame


def bgr_to_pil_image(frame: Any, max_width: int = 640) -> Optional["Image.Image"]:
    if cv2 is None or Image is None or frame is None:
        return None
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    w, h = pil.size
    if w > max_width > 0:
        nh = int(h * max_width / w)
        pil = pil.resize((max_width, nh), Image.Resampling.LANCZOS)
    return pil


def capture_jpeg_data_url(cap: Any, quality: int = 85) -> Optional[str]:
    """現在フレームを JPEG data URL で返す。"""
    frame = read_bgr_frame(cap)
    if frame is None or cv2 is None:
        return None
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return None
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"
