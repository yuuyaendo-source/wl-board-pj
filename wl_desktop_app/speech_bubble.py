# -*- coding: utf-8 -*-
"""リン子の吹き出し。

ミニポートの上にニュッと出る吹き出し。

Phase 2.1 では "toast" モード (自動消失) のみ実装。
Phase 5a (ブレスト) では "interactive" モード (入力欄付き、ユーザが閉じるまで残る)
へ拡張する想定で、外向き API は将来の追加に耐える形にしてある。

公開 API:
    bubble = SpeechBubble(parent_window=miniport)
    bubble.show_message(text, duration_sec=3.0)       # toast 表示
    bubble.append_text(chunk)                          # 後から文字追加 (streaming)
    bubble.clear()                                     # テキストクリア
    bubble.hide()                                      # 即時非表示

スレッド: タイピングアニメや fade は別スレッドだが、Tk ウィジェット更新は
parent_window.after(0, ...) で main thread に dispatch する。
"""
from __future__ import annotations

import threading
import time
from typing import Optional

try:
    import customtkinter as ctk
    import tkinter as tk
except ImportError as e:
    print("customtkinter が見つかりません。pip install -r requirements.txt を実行してください。", e)
    raise


class SpeechBubble:
    """ミニポートの上に表示される吹き出し。"""

    BUBBLE_FG_LIGHT = "#f0faf0"
    BUBBLE_FG_DARK = "#2a7d2e"
    BUBBLE_BORDER_LIGHT = "#5a9e5c"
    BUBBLE_BORDER_DARK = "#1b5e20"
    TEXT_COLOR_LIGHT = "#1b5e20"
    TEXT_COLOR_DARK = "#e8f5e9"

    PAD_X = 14
    PAD_Y = 10
    MAX_WIDTH = 320

    def __init__(self, parent_window):
        self._parent = parent_window
        self._toplevel: Optional[ctk.CTkToplevel] = None
        self._label: Optional[ctk.CTkLabel] = None
        self._typing_thread: Optional[threading.Thread] = None
        self._typing_stop = threading.Event()
        self._hide_timer: Optional[threading.Timer] = None
        self._current_text = ""
        self._lock = threading.Lock()

    # --- 公開 API -----------------------------------------------------------

    def show_message(self, text: str, duration_sec: float = 3.0, typing_speed_cps: Optional[float] = None) -> None:
        """toast モード: タイピングアニメで text を表示し、duration_sec 後に自動非表示。

        typing_speed_cps を渡すと文字/秒。None なら text と duration_sec から自動算出
        (音声と同期したいときは duration_sec に音声秒数を渡す)。
        """
        if not text:
            return
        self._cancel_hide_timer()
        self._stop_typing()
        self._ensure_window()
        self._current_text = ""
        self._set_label_text("")
        speed = typing_speed_cps
        if speed is None:
            # 音声の長さに合わせる: text 全部を duration_sec - 0.5 で表示完了
            anim_dur = max(0.5, duration_sec - 0.3)
            speed = max(8.0, len(text) / anim_dur)
        self._typing_stop.clear()
        self._typing_thread = threading.Thread(
            target=self._typing_loop, args=(text, speed), daemon=True
        )
        self._typing_thread.start()
        # 音声長 + 余韻 1 秒で非表示
        self._schedule_hide(duration_sec + 1.0)

    def append_text(self, chunk: str) -> None:
        """streaming 用: 既存テキストに追記する。Phase 5a のブレスト streaming で利用想定。"""
        if not chunk:
            return
        self._ensure_window()
        with self._lock:
            self._current_text = (self._current_text or "") + chunk
            text = self._current_text
        self._dispatch(lambda: self._set_label_text(text))

    def clear(self) -> None:
        self._stop_typing()
        with self._lock:
            self._current_text = ""
        self._dispatch(lambda: self._set_label_text(""))

    def hide(self) -> None:
        self._cancel_hide_timer()
        self._stop_typing()
        self._dispatch(self._destroy_window)

    # --- 内部 ---------------------------------------------------------------

    def _ensure_window(self) -> None:
        if self._toplevel is not None:
            try:
                self._toplevel.deiconify()
                self._reposition()
                return
            except Exception:
                self._toplevel = None
        self._dispatch(self._build_window)
        # build を待つために短く wait
        for _ in range(20):
            if self._toplevel is not None:
                return
            time.sleep(0.02)

    def _build_window(self) -> None:
        try:
            top = ctk.CTkToplevel(self._parent)
            top.overrideredirect(True)
            top.attributes("-topmost", True)
            try:
                top.attributes("-alpha", 0.95)
            except Exception:
                pass
            top.configure(fg_color="transparent")

            frame = ctk.CTkFrame(
                top,
                corner_radius=14,
                border_width=1,
                border_color=(self.BUBBLE_BORDER_LIGHT, self.BUBBLE_BORDER_DARK),
                fg_color=(self.BUBBLE_FG_LIGHT, self.BUBBLE_FG_DARK),
            )
            frame.pack(padx=4, pady=4)

            label = ctk.CTkLabel(
                frame,
                text="",
                font=ctk.CTkFont(size=13),
                text_color=(self.TEXT_COLOR_LIGHT, self.TEXT_COLOR_DARK),
                wraplength=self.MAX_WIDTH,
                justify="left",
                anchor="w",
            )
            label.pack(padx=self.PAD_X, pady=self.PAD_Y)

            self._toplevel = top
            self._label = label
            self._reposition()
        except Exception as e:
            print(f"[speech_bubble] build_window failed: {e}", flush=True)

    def _reposition(self) -> None:
        """parent (ミニポート) の上に位置決め。"""
        if self._toplevel is None or self._parent is None:
            return
        try:
            self._toplevel.update_idletasks()
            self._parent.update_idletasks()
            bw = self._toplevel.winfo_width() or 200
            bh = self._toplevel.winfo_height() or 60
            px = self._parent.winfo_rootx()
            py = self._parent.winfo_rooty()
            pw = self._parent.winfo_width() or 240
            # ミニポートの「上の真ん中」あたりに配置 (右寄せ気味で)
            x = px + pw - bw - 8
            y = py - bh - 6
            if y < 0:
                # 画面上端を超えたらミニポートの右に出す
                y = py
                x = px + pw + 8
            self._toplevel.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _set_label_text(self, text: str) -> None:
        if self._label is not None:
            try:
                self._label.configure(text=text)
                self._reposition()
            except Exception:
                pass

    def _typing_loop(self, text: str, speed_cps: float) -> None:
        if speed_cps <= 0:
            speed_cps = 30.0
        delay = 1.0 / speed_cps
        shown = ""
        for ch in text:
            if self._typing_stop.is_set():
                break
            shown += ch
            with self._lock:
                self._current_text = shown
            self._dispatch(lambda s=shown: self._set_label_text(s))
            time.sleep(delay)

    def _stop_typing(self) -> None:
        self._typing_stop.set()
        t = self._typing_thread
        if t is not None and t.is_alive():
            try:
                t.join(timeout=0.5)
            except Exception:
                pass
        self._typing_thread = None

    def _schedule_hide(self, after_sec: float) -> None:
        self._cancel_hide_timer()
        timer = threading.Timer(after_sec, self.hide)
        timer.daemon = True
        timer.start()
        self._hide_timer = timer

    def _cancel_hide_timer(self) -> None:
        t = self._hide_timer
        if t is not None:
            try:
                t.cancel()
            except Exception:
                pass
        self._hide_timer = None

    def _destroy_window(self) -> None:
        try:
            if self._toplevel is not None:
                self._toplevel.destroy()
        except Exception:
            pass
        self._toplevel = None
        self._label = None

    def _dispatch(self, fn) -> None:
        """Tk のメインスレッドで関数を実行する。"""
        if self._parent is None:
            try:
                fn()
            except Exception:
                pass
            return
        try:
            self._parent.after(0, fn)
        except Exception:
            try:
                fn()
            except Exception:
                pass
