# -*- coding: utf-8 -*-
"""ミニポート用 2D リン子アバターのマネージャ。

- features.linko_avatar=True のとき有効化
- 11 ポーズ (normal/happy/sad/angry/funny + 母音 a/i/u/e/o) を assets/avatar/ から読む
- 音声再生中に start_lipsync(duration_sec) を呼ぶと a/i/u/e/o をランダム切替
- 終了時に stop_lipsync() で normal に戻す
- mini_port から register_ui_callback(cb) を呼んで UI 更新フックを登録

シングルトン運用 (アプリ全体で 1 つのアバター)。
"""
from __future__ import annotations

import os
import random
import threading
import time
from typing import Callable, Optional

from PIL import Image

VOWELS = ["a", "i", "u", "e", "o"]
EMOTIONS = ["normal", "happy", "sad", "angry", "funny"]


class _LinkoAvatar:
    def __init__(self, size: int = 96):
        self.size = size
        self._images: dict[str, Image.Image] = {}
        self._current_pose = "normal"
        self._lipsync_thread: Optional[threading.Thread] = None
        self._lipsync_stop = threading.Event()
        self._ui_callback: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()

    def load(self, base_dir: str) -> bool:
        ok = True
        for pose in VOWELS + EMOTIONS:
            path = os.path.join(base_dir, "assets", "avatar", f"{pose}_{self.size}.png")
            if os.path.isfile(path):
                try:
                    self._images[pose] = Image.open(path).convert("RGBA")
                except Exception:
                    ok = False
            else:
                ok = False
        return ok

    def get_image(self, pose: Optional[str] = None) -> Optional[Image.Image]:
        p = pose or self._current_pose
        return self._images.get(p) or self._images.get("normal")

    def set_ui_callback(self, cb: Callable[[str], None]) -> None:
        self._ui_callback = cb

    def set_pose(self, pose: str) -> None:
        if pose not in self._images:
            return
        with self._lock:
            self._current_pose = pose
        cb = self._ui_callback
        if cb is not None:
            try:
                cb(pose)
            except Exception:
                pass

    def start_lipsync(
        self,
        duration_sec: Optional[float] = None,
        base_pose: str = "normal",
    ) -> None:
        """音声再生開始時に呼ぶ。a/i/u/e/o をランダム切替で口パク演出。

        duration_sec を渡すと自動停止、None なら stop_lipsync() を呼ぶまで継続。
        """
        self.stop_lipsync(base_pose=base_pose, wait=True)
        self._lipsync_stop.clear()

        def loop():
            start = time.time()
            while not self._lipsync_stop.is_set():
                self.set_pose(random.choice(VOWELS))
                time.sleep(random.uniform(0.10, 0.18))
                if duration_sec is not None and (time.time() - start) >= duration_sec:
                    break
            self.set_pose(base_pose)

        self._lipsync_thread = threading.Thread(
            target=loop, name="linko_avatar_lipsync", daemon=True
        )
        self._lipsync_thread.start()

    def stop_lipsync(self, base_pose: str = "normal", wait: bool = False) -> None:
        self._lipsync_stop.set()
        t = self._lipsync_thread
        if wait and t is not None:
            try:
                t.join(timeout=1.0)
            except Exception:
                pass
        self._lipsync_thread = None
        self.set_pose(base_pose)


# --- モジュール公開関数 (シングルトン) ----------------------------------------

_singleton: Optional[_LinkoAvatar] = None


def init(size: int = 96) -> bool:
    """アバターをロードして使用可能にする。features.linko_avatar=True のときに mini_port から呼ぶ。
    戻り値: すべての画像が読み込めたら True。
    """
    global _singleton
    try:
        from config_loader import get_app_base_dir
        base_dir = get_app_base_dir()
    except Exception:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    _singleton = _LinkoAvatar(size=size)
    return _singleton.load(base_dir)


def is_ready() -> bool:
    return _singleton is not None and bool(_singleton._images)


def get_image(pose: Optional[str] = None) -> Optional[Image.Image]:
    if _singleton is None:
        return None
    return _singleton.get_image(pose)


def set_ui_callback(cb: Callable[[str], None]) -> None:
    if _singleton is not None:
        _singleton.set_ui_callback(cb)


def set_pose(pose: str) -> None:
    if _singleton is not None:
        _singleton.set_pose(pose)


def start_lipsync(duration_sec: Optional[float] = None, base_pose: str = "normal") -> None:
    if _singleton is not None:
        _singleton.start_lipsync(duration_sec=duration_sec, base_pose=base_pose)


def stop_lipsync(base_pose: str = "normal") -> None:
    if _singleton is not None:
        _singleton.stop_lipsync(base_pose=base_pose)
