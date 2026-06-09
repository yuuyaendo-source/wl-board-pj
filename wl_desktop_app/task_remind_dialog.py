# -*- coding: utf-8 -*-
"""タスクリマインド用の小さな応答ダイアログ（継続 / 完了 / 相談）。"""
from __future__ import annotations

import os
import sys
from typing import Callable, Optional

try:
    import customtkinter as ctk
except ImportError as e:
    print("customtkinter が見つかりません。", e)
    raise

from config_loader import is_feature_enabled, load_config

_dialog_instance: Optional["TaskRemindDialog"] = None


class TaskRemindDialog(ctk.CTkToplevel):
    WIDTH = 360
    HEIGHT = 200

    def __init__(
        self,
        master=None,
        *,
        item: dict,
        slot: str,
        on_ack: Callable[[str], None],
    ):
        super().__init__(master)
        self._item = item
        self._slot = slot
        self._on_ack = on_ack
        self._closed = False
        self.title("タスクリマインド")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            ico = os.path.join(base, "assets", "linko.ico")
            if os.path.isfile(ico) and sys.platform.startswith("win"):
                self.iconbitmap(ico)
        except Exception:
            pass
        self._build_ui()
        self._position_near(master)
        self.protocol("WM_DELETE_WINDOW", self._on_dismiss)
        self.lift()
        self.focus_force()

    def _position_near(self, master) -> None:
        if master is None:
            self.update_idletasks()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = sw - self.WIDTH - 24
            y = sh - self.HEIGHT - 80
            self.geometry(f"+{x}+{y}")
            return
        try:
            master.update_idletasks()
            mx = master.winfo_x()
            my = master.winfo_y()
            mw = master.winfo_width()
            x = mx + mw + 8
            y = my
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _build_ui(self) -> None:
        pad = 12
        msg = self._item.get("message") or self._item.get("title") or "タスクの確認"
        ctk.CTkLabel(
            self,
            text="Today のタスク",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=pad, pady=(pad, 4))
        ctk.CTkLabel(
            self,
            text=msg,
            wraplength=self.WIDTH - pad * 2,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=pad, pady=(0, 8))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=pad, pady=(0, pad))
        ctk.CTkButton(
            btn_row,
            text="継続",
            width=90,
            command=lambda: self._finish("continue"),
            fg_color=("#5a9a5c", "#2e7d32"),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_row,
            text="完了",
            width=90,
            command=lambda: self._finish("done"),
            fg_color=("#3d7ea6", "#1565c0"),
        ).pack(side="left", padx=(0, 6))
        if is_feature_enabled("brainstorm"):
            ctk.CTkButton(
                btn_row,
                text="相談",
                width=90,
                command=self._on_consult,
                fg_color=("#7b5ea7", "#5e35b1"),
            ).pack(side="left")

    def _finish(self, action: str) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._on_ack(action)
        except Exception as e:
            print(f"[task_remind] ack callback error: {e}", flush=True)
        self._close()

    def _on_consult(self) -> None:
        if self._closed:
            return
        title = self._item.get("title") or ""
        note_id = self._item.get("note_id")
        self._finish("continue")
        try:
            from chat_panel import open_chat_panel_with_task
            open_chat_panel_with_task(
                master=self.master,
                task_title=title,
                note_id=note_id,
            )
        except Exception as e:
            print(f"[task_remind] consult open failed: {e}", flush=True)

    def _on_dismiss(self) -> None:
        if not self._closed:
            self._finish("continue")

    def _close(self) -> None:
        global _dialog_instance
        _dialog_instance = None
        try:
            from task_remind_client import notify_dialog_closed
            notify_dialog_closed()
        except Exception:
            pass
        try:
            import linko_avatar
            linko_avatar.dismiss_ui()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


def show_task_remind_dialog(
    master,
    item: dict,
    slot: str,
    on_ack: Callable[[str], None],
) -> Optional[TaskRemindDialog]:
    """リマインドダイアログを表示（シングルトン）。"""
    global _dialog_instance
    if _dialog_instance is not None:
        try:
            _dialog_instance.lift()
            return _dialog_instance
        except Exception:
            _dialog_instance = None

    cfg = load_config()
    from task_remind_client import post_shown, notify_dialog_closed
    if not post_shown(cfg, item, slot):
        notify_dialog_closed()
        print("[task_remind] shown API 失敗 — リマインドをスキップ", flush=True)
        return None

    def _show_bubble():
        try:
            from notifications import are_enabled
            if not are_enabled():
                return
            if not is_feature_enabled("linko_avatar"):
                return
            import linko_avatar
            msg = item.get("message") or ""
            if msg:
                linko_avatar.say(msg, duration_sec=8, lipsync=False)
        except Exception:
            pass

    def _show_toast():
        try:
            from notifications import are_enabled, show_toast
            if not are_enabled():
                return
            title = item.get("title") or "タスク"
            show_toast(
                "Wonder Linko",
                (item.get("message") or title) + "\n（ミニポート横で選択してください）",
                duration_sec=10,
            )
        except Exception:
            pass

    _show_toast()
    _show_bubble()
    _dialog_instance = TaskRemindDialog(
        master=master,
        item=item,
        slot=slot,
        on_ack=on_ack,
    )
    return _dialog_instance
