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

try:
    from app_log import log_info as _log
except Exception:  # pragma: no cover
    def _log(msg: str) -> None:
        print(msg, flush=True)

VOWELS = ["a", "i", "u", "e", "o"]
EMOTIONS = ["normal", "happy", "sad", "angry", "funny"]


class _LinkoAvatar:
    def __init__(self, size: int = 96):
        self.size = size
        self._images: dict[str, Image.Image] = {}
        self._current_pose = "normal"
        self._lipsync_thread: Optional[threading.Thread] = None
        self._lipsync_stop = threading.Event()
        self._idle_thread: Optional[threading.Thread] = None
        self._idle_stop = threading.Event()
        self._is_speaking = False  # 喋り中は idle を止める
        self._ui_callback: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()

    def load(self, base_dir: str) -> bool:
        ok = True
        missing = []
        for pose in VOWELS + EMOTIONS:
            path = os.path.join(base_dir, "assets", "avatar", f"{pose}_{self.size}.png")
            if os.path.isfile(path):
                try:
                    self._images[pose] = Image.open(path).convert("RGBA")
                except Exception as e:
                    ok = False
                    missing.append(f"{pose}(open失敗:{e})")
            else:
                ok = False
                missing.append(f"{pose}(無)")
        _log(f"[linko_avatar] load size={self.size} 読込={len(self._images)}/10 ok={ok}"
             + (f" 欠落={missing}" if missing else ""))
        return ok

    def get_image(self, pose: Optional[str] = None) -> Optional[Image.Image]:
        p = pose or self._current_pose
        return self._images.get(p) or self._images.get("normal")

    def set_ui_callback(self, cb: Callable[[str], None]) -> None:
        self._ui_callback = cb
        _log(f"[linko_avatar] set_ui_callback registered={cb is not None}")

    def set_pose(self, pose: str) -> None:
        if pose not in self._images:
            _log(f"[linko_avatar] set_pose skip: '{pose}' が images に無い (keys={list(self._images.keys())})")
            return
        with self._lock:
            self._current_pose = pose
        cb = self._ui_callback
        if cb is not None:
            try:
                cb(pose)
            except Exception as e:
                _log(f"[linko_avatar] set_pose callback error: {e}")
        else:
            _log("[linko_avatar] set_pose: _ui_callback が None")

    def start_lipsync(
        self,
        duration_sec: Optional[float] = None,
        base_pose: str = "normal",
    ) -> None:
        """音声再生開始時に呼ぶ。a/i/u/e/o をランダム切替で口パク演出。

        duration_sec を渡すと自動停止、None なら stop_lipsync() を呼ぶまで継続。
        """
        self.stop_lipsync(base_pose=base_pose, wait=True)
        self._is_speaking = True
        self._lipsync_stop.clear()
        _log(f"[linko_avatar] start_lipsync duration={duration_sec} images={len(self._images)} cb={self._ui_callback is not None}")

        def loop():
            start = time.time()
            while not self._lipsync_stop.is_set():
                self.set_pose(random.choice(VOWELS))
                time.sleep(random.uniform(0.10, 0.18))
                if duration_sec is not None and (time.time() - start) >= duration_sec:
                    break
            self._is_speaking = False
            self.set_pose(base_pose)

        self._lipsync_thread = threading.Thread(
            target=loop, name="linko_avatar_lipsync", daemon=True
        )
        self._lipsync_thread.start()

    def stop_lipsync(self, base_pose: str = "normal", wait: bool = False) -> None:
        self._lipsync_stop.set()
        self._is_speaking = False
        t = self._lipsync_thread
        if wait and t is not None:
            try:
                t.join(timeout=1.0)
            except Exception:
                pass
        self._lipsync_thread = None
        self.set_pose(base_pose)

    def start_idle_animation(self, base_pose: str = "normal") -> None:
        """アイドルアニメ: 30-60 秒に 1 回、200ms だけ 'happy' (目閉じ笑顔) にして
        まばたき + ふっと笑む演出。喋っている間はスキップ (lipsync 優先)。
        Clippy 化を避けるため、ごく控えめに動く。
        """
        self.stop_idle_animation(wait=True)
        self._idle_stop.clear()
        _log(f"[linko_avatar] start_idle_animation images={len(self._images)} cb={self._ui_callback is not None}")

        def loop():
            while not self._idle_stop.is_set():
                # 30-60 秒のランダム待機 (1秒刻みで stop check)
                wait_sec = random.randint(30, 60)
                for _ in range(wait_sec):
                    if self._idle_stop.is_set():
                        return
                    time.sleep(1.0)
                if self._is_speaking or self._idle_stop.is_set():
                    continue
                # 200ms だけ happy
                self.set_pose("happy")
                time.sleep(0.2)
                if not self._idle_stop.is_set() and not self._is_speaking:
                    self.set_pose(base_pose)

        self._idle_thread = threading.Thread(
            target=loop, name="linko_avatar_idle", daemon=True
        )
        self._idle_thread.start()

    def stop_idle_animation(self, wait: bool = False) -> None:
        self._idle_stop.set()
        t = self._idle_thread
        if wait and t is not None:
            try:
                t.join(timeout=1.0)
            except Exception:
                pass
        self._idle_thread = None


# --- モジュール公開関数 (シングルトン) ----------------------------------------

_singleton: Optional[_LinkoAvatar] = None
_speech_bubble = None  # SpeechBubble インスタンス (mini_port から register)


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


def start_idle_animation() -> None:
    if _singleton is not None:
        _singleton.start_idle_animation()


def stop_idle_animation() -> None:
    if _singleton is not None:
        _singleton.stop_idle_animation()


def register_speech_bubble(bubble) -> None:
    """SpeechBubble インスタンスを登録。say() で吹き出しを使うため。"""
    global _speech_bubble
    _speech_bubble = bubble


def say(
    text: str,
    duration_sec: Optional[float] = None,
    base_pose: str = "normal",
    lipsync: bool = True,
) -> None:
    """吹き出し + (任意で) 口パくを開始する統合 API。

    Phase 2.1: 1 発話 (toast) ベース。
    Phase 5a (ブレスト): _speech_bubble.append_text() を直接呼んで streaming する想定。

    duration_sec: 音声長 (秒)。lipsync=True かつ duration_sec が None/0 のときは
      text の長さから概算 (wav 長が取れなくても口パくさせる)。
    lipsync: False なら吹き出しのみ (アバタークリックの挨拶など、音声なしの場面)。
    """
    if _speech_bubble is not None and text:
        try:
            _speech_bubble.show_message(text, duration_sec=duration_sec or 3.0)
        except Exception as e:
            _log(f"[linko_avatar] speech bubble error: {e}")
    if lipsync:
        lip_dur = duration_sec
        if (lip_dur is None or lip_dur <= 0) and text:
            # wav 長が取れない/未指定でも text 長から概算 (1 文字 ~0.15 秒、最低 2 秒)
            lip_dur = max(2.0, len(text) * 0.15)
            _log(f"[linko_avatar] say: duration 概算 {lip_dur:.1f}s (text {len(text)}字)")
        if lip_dur and lip_dur > 0:
            start_lipsync(duration_sec=lip_dur, base_pose=base_pose)


def is_speaking() -> bool:
    return _singleton is not None and _singleton._is_speaking
