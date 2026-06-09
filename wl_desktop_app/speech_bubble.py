# -*- coding: utf-8 -*-
"""リン子の吹き出し。ミニポートの上に出る。

設計上の鉄則 (v3.2.2 で増殖バグを修正):
- 公開メソッドは内部で必ず parent.after(0, ...) を使い、実処理を Tk メインスレッドで
  実行する。これにより別スレッド (visitor_notify) / メインスレッド (avatar click) の
  どちらから呼ばれても安全。
- Toplevel は 1 個だけ (シングルトン)。build は _do_show 内で同期的に行い、既存があれば
  再利用する。非同期 build を複数キューして窓が増殖する問題を排除。

Phase 5a (ブレスト) で append_text() を使った streaming に拡張予定。
"""
from __future__ import annotations

import threading
import time
from typing import Optional

try:
    import customtkinter as ctk
except ImportError as e:
    print("customtkinter が見つかりません。pip install -r requirements.txt を実行してください。", e)
    raise

from theme import Theme, IS_WINDOWS


class SpeechBubble:
    PAD_X = 14
    PAD_Y = 10
    MAX_WIDTH = 260

    def __init__(self, parent_window):
        self._parent = parent_window
        self._top: Optional[ctk.CTkToplevel] = None
        self._label = None
        self._typing_thread: Optional[threading.Thread] = None
        self._typing_stop = threading.Event()
        self._hide_after_id = None  # parent.after で予約した hide のキャンセル用
        self._text = ""

    # --- 公開 API (どのスレッドから呼んでも安全) -----------------------------

    def show_message(self, text: str, duration_sec: float = 3.0) -> None:
        if not text or self._parent is None:
            return
        try:
            from notifications import are_enabled
            if not are_enabled():
                return
        except Exception:
            pass
        self._safe(lambda: self._do_show(text, duration_sec))

    def append_text(self, chunk: str) -> None:
        """Phase 5a streaming 用。"""
        if not chunk or self._parent is None:
            return
        try:
            from notifications import are_enabled
            if not are_enabled():
                return
        except Exception:
            pass
        self._safe(lambda: self._do_append(chunk))

    def clear(self) -> None:
        if self._parent is None:
            return
        self._safe(self._do_clear)

    def hide(self) -> None:
        if self._parent is None:
            return
        self._safe(self._do_hide)

    # --- メインスレッドで動く実処理 ------------------------------------------

    def _do_show(self, text: str, duration_sec: float) -> None:
        self._stop_typing()
        self._cancel_hide()
        self._ensure_window()
        if self._label is None:
            return
        self._text = ""
        self._label.configure(text="")
        self._reposition()
        # タイピング速度: 音声長 - 0.3 で打ち終わる
        anim_dur = max(0.4, duration_sec - 0.3)
        speed = max(8.0, len(text) / anim_dur)
        self._typing_stop.clear()
        self._typing_thread = threading.Thread(
            target=self._typing_loop, args=(text, speed), daemon=True
        )
        self._typing_thread.start()
        # 音声長 + 余韻 1 秒後に自動で消す
        self._hide_after_id = self._parent.after(
            int((duration_sec + 1.0) * 1000), self._do_hide
        )

    def _do_append(self, chunk: str) -> None:
        self._ensure_window()
        if self._label is None:
            return
        self._text += chunk
        self._label.configure(text=self._text)
        self._reposition()

    def _do_clear(self) -> None:
        self._stop_typing()
        self._text = ""
        if self._label is not None:
            self._label.configure(text="")

    def _do_hide(self) -> None:
        self._cancel_hide()
        self._stop_typing()
        try:
            if self._top is not None:
                self._top.destroy()
        except Exception:
            pass
        self._top = None
        self._label = None

    # --- 内部 ---------------------------------------------------------------

    def _ensure_window(self) -> None:
        """Toplevel を 1 個だけ作る (同期)。既存があれば何もしない。
        漫画風: 角丸白背景 + 緑の太枠 + 下に尻尾 ▼。外側は transparentcolor で透過。
        """
        if self._top is not None:
            try:
                self._top.deiconify()
                return
            except Exception:
                self._top = None
        try:
            top = ctk.CTkToplevel(self._parent)
            top.overrideredirect(True)
            top.attributes("-topmost", True)
            # Windows のみ transparentcolor で外枠を透明化。非 Windows は黒い四角が
            # 残るため使わず、尻尾の背景を白 (吹き出し色) に合わせて馴染ませる。
            if IS_WINDOWS:
                try:
                    key = Theme.TRANSPARENT_KEY
                    top.configure(fg_color=key)
                    top.attributes("-transparentcolor", key)
                    self._tail_bg = key
                except Exception:
                    top.configure(fg_color=Theme.BUBBLE_FG)
                    self._tail_bg = Theme.BUBBLE_FG[0]
            else:
                top.configure(fg_color=Theme.BUBBLE_FG)
                self._tail_bg = Theme.BUBBLE_FG[0]

            # 吹き出し本体 (角丸白 + 緑太枠)
            frame = ctk.CTkFrame(
                top,
                corner_radius=Theme.RADIUS_BUBBLE,
                border_width=2,
                border_color=Theme.BUBBLE_BORDER,
                fg_color=Theme.BUBBLE_FG,
            )
            frame.pack(padx=2, pady=(2, 0))
            label = ctk.CTkLabel(
                frame,
                text="",
                font=ctk.CTkFont(size=14),
                text_color=Theme.BUBBLE_TEXT,
                wraplength=self.MAX_WIDTH,
                justify="left",
            )
            label.pack(padx=self.PAD_X, pady=self.PAD_Y)

            # 尻尾 ▼ (吹き出しの下・中央 = 真下のアバター中心を指す)
            tail = ctk.CTkLabel(
                top,
                text="▼",
                font=ctk.CTkFont(size=22),
                text_color=Theme.BUBBLE_BORDER,
                fg_color=self._tail_bg,
            )
            tail.pack(anchor="center", pady=0)

            self._top = top
            self._label = label
        except Exception as e:
            print(f"[speech_bubble] build failed: {e}", flush=True)
            self._top = None
            self._label = None

    def _reposition(self) -> None:
        if self._top is None or self._parent is None:
            return
        try:
            self._top.update_idletasks()
            self._parent.update_idletasks()
            bw = self._top.winfo_width() or 200
            bh = self._top.winfo_height() or 50
            px = self._parent.winfo_rootx()
            py = self._parent.winfo_rooty()
            pw = self._parent.winfo_width() or 240
            # ミニポートの真上・中央寄せ (尻尾が中央のアバターを指すように)
            x = px + (pw - bw) / 2
            y = py - bh - 4
            if y < 0:
                y = py + (self._parent.winfo_height() or 140) + 4
            self._top.geometry(f"+{int(x)}+{int(y)}")
        except Exception:
            pass

    def _typing_loop(self, text: str, speed_cps: float) -> None:
        delay = 1.0 / max(1.0, speed_cps)
        shown = ""
        for ch in text:
            if self._typing_stop.is_set():
                return
            shown += ch
            # ラベル更新はメインスレッドへ
            self._safe(lambda s=shown: self._update_label(s))
            time.sleep(delay)

    def _update_label(self, s: str) -> None:
        self._text = s
        if self._label is not None:
            try:
                self._label.configure(text=s)
                self._reposition()
            except Exception:
                pass

    def _stop_typing(self) -> None:
        self._typing_stop.set()

    def _cancel_hide(self) -> None:
        if self._hide_after_id is not None:
            try:
                self._parent.after_cancel(self._hide_after_id)
            except Exception:
                pass
        self._hide_after_id = None

    def _safe(self, fn) -> None:
        """Tk メインスレッドで fn を実行 (after は thread-safe)。"""
        try:
            self._parent.after(0, fn)
        except Exception:
            try:
                fn()
            except Exception:
                pass
