# -*- coding: utf-8 -*-
"""
Rinko Mini-Port: 常駐型フローティング入力ウィンドウ。
通常時はリン子ボタンと投稿ボタンのみ。「投稿」クリックで入力欄を表示し、送信ボタンで POST /sticky_notes に送信。
"""
from __future__ import annotations

import os
import re
import sys
import threading
import time
import webbrowser
from typing import Tuple

try:
    import requests
    import customtkinter as ctk
except ImportError as e:
    print("必要なパッケージがありません。以下を実行してください:")
    print("  pip install -r requirements.txt")
    print("エラー:", e)
    sys.exit(1)

from config_loader import load_config, get_app_base_dir

# 画像表示用（PIL が無い環境ではリン子はテキストボタンのみ）
# CTkImage は内部で PIL.Image と PIL.ImageTk を参照するため、先に両方 import する
try:
    import PIL.Image  # noqa: F401
    import PIL.ImageTk  # noqa: F401
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# ホットキー用（別スレッドで動作）
try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False


def _sticky_note_api_url():
    """付箋ボードの REST API URL（POST /api/sticky_notes）。board URL から導出。"""
    cfg = load_config()
    board_url = (cfg.get("mini_port_api_url") or "https://wl-ai-board.internal.wonder-link.co.jp/board/wl").rstrip("/")
    # https://wl-ai-board.../board/wl → https://wl-ai-board.../api/sticky_notes
    base = re.sub(r"/board/.*$", "", board_url).rstrip("/")
    return f"{base}/api/sticky_notes"


def _board_id():
    """送信先ボード ID（例: wl）。"""
    cfg = load_config()
    return (cfg.get("postit_board_id") or "wl").strip() or "wl"


def _taskboard_url():
    """ミニウィンドウのリン子クリックで開く Task ボードの URL。"""
    cfg = load_config()
    return (cfg.get("mini_port_taskboard_url") or "https://wl-ai-board.internal.wonder-link.co.jp/boards/taskboard").strip()


def _send_content(text: str) -> Tuple[bool, str]:
    """付箋ボード API (POST /api/sticky_notes) に boardId + note 形式で送信。"""
    text = (text or "").strip()
    if not text:
        return False, "入力が空です"
    url = _sticky_note_api_url()
    board_id = _board_id()
    cfg = load_config()
    author = (cfg.get("display_name") or "").strip() or "Mini-Port"
    note_id = f"miniport-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
    note = {
        "id": note_id,
        "text": text,
        "x": 100,
        "y": 100,
        "color": "#fff59d",
        "pinned": False,
        "author": author,
        "createdAt": int(time.time() * 1000),
    }
    try:
        r = requests.post(url, json={"boardId": board_id, "note": note}, timeout=10)
        if r.status_code in (200, 201):
            return True, "送信しました"
        try:
            body = (r.text or "")[:120].strip()
            detail = f" {body}" if body else ""
        except Exception:
            detail = ""
        return False, f"エラー: {r.status_code}{detail}"
    except requests.exceptions.RequestException as e:
        return False, f"接続エラー: {str(e)[:80]}"


def _rinko_icon_path() -> str:
    return os.path.normpath(os.path.abspath(os.path.join(get_app_base_dir(), "toast_icon.png")))


class MiniPortWindow(ctk.CTk):
    # 通常時サイズ（リン子 + 投稿のみ）
    COMPACT_W = 180
    COMPACT_H = 56
    # 入力表示時サイズ
    EXPANDED_W = 360
    EXPANDED_H = 200

    def __init__(self, on_hide=None, on_notifications_toggle=None, get_notifications_enabled=None):
        super().__init__()
        self._on_hide = on_hide if callable(on_hide) else None
        self._on_notifications_toggle = on_notifications_toggle if callable(on_notifications_toggle) else None
        self._get_notifications_enabled = get_notifications_enabled if callable(get_notifications_enabled) else (lambda: True)
        self._feedback_job = None
        self._input_visible = False
        self._placeholder_visible = False
        self._drag_win_x = 0
        self._drag_win_y = 0
        self._last_compact_x = 0
        self._last_compact_y = 0
        self._configure_window()
        self._build_ui()
        self._setup_context_menu()
        self._position_bottom_right(compact=True)
        if HAS_PYNPUT:
            self._start_hotkey_listener()
        else:
            print("Rinko Mini-Port: pynput が未インストールです。pip install pynput で Ctrl+Shift+Space が有効になります。")

    # プレースホルダー用（CTkTextbox は placeholder 非対応のため自前で表示）
    PLACEHOLDER_TEXT = "付箋を投稿するコメントを入力"

    def _configure_window(self):
        self.title("Rinko Mini-Port")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        # 緑基調の背景・透明度40%増し（不透明度60%）・背景色は30%明るく
        self.attributes("-alpha", 0.6)
        self.configure(fg_color=("#ddf2de", "#2a7d2e"))
        self.resizable(False, False)

    def _build_ui(self):
        # 緑基調のメインフレーム（ドラッグ用にバインドする）・背景30%明るく
        self.frame = ctk.CTkFrame(
            self,
            corner_radius=24,
            border_width=1,
            border_color=("#9dd4a0", "#2a7d2e"),
            fg_color=("#f0faf0", "#2a7d2e"),
        )
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)

        # --- 通常時: リン子 + 投稿 ---
        self.compact_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.compact_frame.pack(fill="x", padx=10, pady=8)

        icon_path = _rinko_icon_path()
        use_icon = _HAS_PIL and os.path.isfile(icon_path)
        self._rinko_image = None  # 参照を保持してアイコンが消えないようにする
        if use_icon:
            try:
                self._rinko_image = ctk.CTkImage(
                    light_image=icon_path,
                    dark_image=icon_path,
                    size=(36, 36),
                )
                self.btn_rinko = ctk.CTkButton(
                    self.compact_frame,
                    image=self._rinko_image,
                    text="",
                    width=44,
                    height=40,
                    corner_radius=22,
                    fg_color=("#5a9e5c", "#1b5e20"),
                    hover_color=("#4a8e4c", "#145214"),
                    command=self._open_taskboard,
                )
            except Exception:
                use_icon = False
        if not use_icon:
            self.btn_rinko = ctk.CTkButton(
                self.compact_frame,
                text="ボード",
                width=56,
                height=40,
                corner_radius=20,
                font=ctk.CTkFont(size=13),
                fg_color=("#5a9e5c", "#1b5e20"),
                hover_color=("#4a8e4c", "#145214"),
                command=self._open_taskboard,
            )
        self.btn_rinko.pack(side="left", padx=(0, 8))

        self.btn_post = ctk.CTkButton(
            self.compact_frame,
            text="投稿",
            width=70,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=14),
            fg_color=("#5a9e5c", "#1b5e20"),
            hover_color=("#4a8e4c", "#145214"),
            command=self._show_input,
        )
        self.btn_post.pack(side="left")

        # --- 入力表示時: テキストエリア + 閉じる + 送信 ---
        self.input_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        # 3行表示・スクロール・改行可（プレースホルダーは FocusIn/FocusOut で制御）
        self.textbox = ctk.CTkTextbox(
            self.input_frame,
            width=320,
            height=72,
            font=ctk.CTkFont(size=14),
            corner_radius=12,
            border_width=1,
            wrap="word",
            fg_color=("#fff", "#263238"),
            border_color=("#5a9e5c", "#2e7d32"),
        )
        self.textbox.pack(pady=(0, 6), fill="x")
        self.textbox.bind("<Control-Return>", self._on_send_shortcut)
        self.textbox.bind("<Escape>", lambda e: self._hide_input())
        self.textbox.bind("<FocusIn>", self._on_textbox_focus_in)
        self.textbox.bind("<FocusOut>", self._on_textbox_focus_out)
        self.textbox.bind("<KeyPress>", self._on_textbox_key, add="+")

        send_f = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        send_f.pack(fill="x")
        self.label_feedback = ctk.CTkLabel(
            send_f,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("#1b5e20", "#a5d6a7"),
        )
        self.label_feedback.pack(side="left", padx=(0, 8))
        self.btn_close = ctk.CTkButton(
            send_f,
            text="閉じる",
            width=70,
            height=32,
            corner_radius=16,
            font=ctk.CTkFont(size=13),
            fg_color=("#5a9e5c", "#1b5e20"),
            hover_color=("#4a8e4c", "#145214"),
            command=self._hide_input,
        )
        self.btn_close.pack(side="right", padx=(0, 6))
        self.btn_send = ctk.CTkButton(
            send_f,
            text="送信",
            width=80,
            height=32,
            corner_radius=16,
            font=ctk.CTkFont(size=13),
            fg_color=("#3d8b40", "#1b5e20"),
            hover_color=("#2e7d32", "#145214"),
            command=self._on_send,
        )
        self.btn_send.pack(side="right")

        self._setup_drag()

    def _setup_context_menu(self):
        """右クリックで通知オン/オフ・ミニポート非表示のメニューを表示。"""
        import tkinter as tk
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(label="", command=self._ctx_toggle_notifications)
        self._ctx_menu.add_command(label="ミニポートを非表示にする", command=self._ctx_hide_miniport)
        for widget in (self.frame, self.compact_frame):
            widget.bind("<Button-3>", self._on_right_click)
        if hasattr(self, "input_frame"):
            self.input_frame.bind("<Button-3>", self._on_right_click)

    def _on_right_click(self, event):
        """右クリックでコンテキストメニューを表示。"""
        enabled = self._get_notifications_enabled()
        self._ctx_menu.entryconfig(0, label="通知をオフにする" if enabled else "通知をオンにする")
        try:
            self._ctx_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._ctx_menu.grab_release()

    def _ctx_toggle_notifications(self):
        if self._on_notifications_toggle:
            self._on_notifications_toggle()

    def _ctx_hide_miniport(self):
        if self._on_hide:
            self._on_hide()

    def _setup_drag(self):
        """ウィンドウをマウス/タッチでドラッグ移動できるようにする。"""
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_win_x = 0
        self._drag_win_y = 0
        self.frame.bind("<Button-1>", self._on_drag_start)
        self.frame.bind("<B1-Motion>", self._on_drag_motion)
        self.compact_frame.bind("<Button-1>", self._on_drag_start)
        self.compact_frame.bind("<B1-Motion>", self._on_drag_motion)
        self.input_frame.bind("<Button-1>", self._on_drag_start)
        self.input_frame.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event):
        """ドラッグ開始。ボタン・テキストボックス上では開始しない。"""
        w = event.widget
        if w in (self.btn_rinko, self.btn_post, self.btn_send, self.btn_close, self.textbox):
            return
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._drag_win_x = self.winfo_x()
        self._drag_win_y = self.winfo_y()

    def _on_drag_motion(self, event):
        """ドラッグ中: ウィンドウを移動。"""
        w = event.widget
        if w in (self.btn_rinko, self.btn_post, self.btn_send, self.btn_close, self.textbox):
            return
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._drag_win_x += dx
        self._drag_win_y += dy
        self.geometry(f"+{self._drag_win_x}+{self._drag_win_y}")
        if not self._input_visible:
            self._last_compact_x = self._drag_win_x
            self._last_compact_y = self._drag_win_y

    def _show_input(self):
        if self._input_visible:
            return
        self._input_visible = True
        self.compact_frame.pack_forget()
        self.input_frame.pack(fill="both", expand=True, padx=12, pady=10)
        self._position_bottom_right(compact=False)
        self._show_placeholder()
        self.textbox.focus_set()

    def _hide_input(self):
        if not self._input_visible:
            return
        self._input_visible = False
        self.textbox.delete("1.0", "end")
        self._placeholder_visible = False
        self.input_frame.pack_forget()
        self.compact_frame.pack(fill="x", padx=10, pady=8)
        # 閉じる時は最後にドラッグしたコンパクト時の位置に戻す
        self.update_idletasks()
        x, y = self._last_compact_x, self._last_compact_y
        self.geometry(f"{self.COMPACT_W}x{self.COMPACT_H}+{x}+{y}")
        self._drag_win_x, self._drag_win_y = x, y

    def _show_placeholder(self):
        if self._placeholder_visible:
            return
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", self.PLACEHOLDER_TEXT)
        self.textbox.configure(text_color=("#2e5c30", "#9ccc9e"))
        self._placeholder_visible = True

    def _remove_placeholder(self):
        if not self._placeholder_visible:
            return
        self._placeholder_visible = False
        self.textbox.delete("1.0", "end")
        self.textbox.configure(text_color=("#1a1a1a", "#e0e0e0"))

    def _on_textbox_focus_in(self, event=None):
        if self._placeholder_visible:
            self._remove_placeholder()

    def _on_textbox_focus_out(self, event=None):
        try:
            t = self.textbox.get("1.0", "end").strip()
        except Exception:
            t = ""
        if not t and self._input_visible:
            self._show_placeholder()

    def _on_textbox_key(self, event=None):
        if self._placeholder_visible:
            self._remove_placeholder()

    def _open_taskboard(self):
        webbrowser.open(_taskboard_url())

    def _position_bottom_right(self, compact: bool = True):
        self.update_idletasks()
        w = self.COMPACT_W if compact else self.EXPANDED_W
        h = self.COMPACT_H if compact else self.EXPANDED_H
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        margin = 24
        taskbar_margin = 50
        x = sw - w - margin
        y = sh - h - taskbar_margin - margin
        self.geometry(f"{w}x{h}+{x}+{y}")
        self._drag_win_x = x
        self._drag_win_y = y
        if compact:
            self._last_compact_x = x
            self._last_compact_y = y

    def _on_send_shortcut(self, event=None):
        self._on_send()
        return "break"

    def _on_send(self):
        text = self.textbox.get("1.0", "end").strip()
        if not text or text == self.PLACEHOLDER_TEXT:
            return
        self.label_feedback.configure(text="送信中…", text_color=("#1b5e20", "#a5d6a7"))
        self.btn_send.configure(state="disabled")
        # 送信は別スレッドで実行し、結果を after で UI に反映（フリーズ防止・確実に完了）
        def do_send():
            result = _send_content(text)
            self.after(0, lambda: self._on_send_done(result))

        threading.Thread(target=do_send, daemon=True).start()

    def _on_send_done(self, result: Tuple[bool, str]):
        ok, msg = result
        self.btn_send.configure(state="normal")
        if ok:
            self.label_feedback.configure(
                text="✓ 送信しました（表示されない場合は付箋ボードを再読み込み）",
                text_color=("#2e7d32", "#81c784"),
            )
            self.textbox.delete("1.0", "end")
            if self._feedback_job:
                self.after_cancel(self._feedback_job)
            # 1.5秒後にフィードバックを消して元のサイズ（リン子+投稿のみ）に戻す
            self._feedback_job = self.after(1500, self._clear_feedback_and_hide)
        else:
            self.label_feedback.configure(text=msg[:60], text_color=("#c62828", "#ef5350"))
            if self._feedback_job:
                self.after_cancel(self._feedback_job)
            self._feedback_job = self.after(3000, self._clear_feedback)

    def _clear_feedback_and_hide(self):
        self._feedback_job = None
        self.label_feedback.configure(text="", text_color=("gray30", "gray70"))
        self._hide_input()

    def _clear_feedback(self):
        self._feedback_job = None
        self.label_feedback.configure(text="", text_color=("gray30", "gray70"))

    def focus_and_raise(self):
        self.after(0, self._do_focus)

    def _do_focus(self):
        self.lift()
        self.attributes("-topmost", True)
        if self._input_visible:
            self.textbox.focus_set()
        else:
            self.btn_post.focus_set()

    def _start_hotkey_listener(self):
        def on_activate():
            self.focus_and_raise()

        def listen():
            with keyboard.GlobalHotKeys({"<ctrl>+<shift>+<space>": on_activate}) as h:
                h.join()

        t = threading.Thread(target=listen, daemon=True)
        t.start()


def main():
    ctk.set_appearance_mode("system")
    app = MiniPortWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
