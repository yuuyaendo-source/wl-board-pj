# -*- coding: utf-8 -*-
"""タスクリマインド用ダイアログ（Today 一覧・タスクごとに継続/完了/相談）。"""
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

LIST_SUMMARY_MESSAGE = "本日のタスクの進捗はいかがですか？"

_dialog_instance: Optional["TaskRemindListDialog"] = None


class TaskRemindListDialog(ctk.CTkToplevel):
    WIDTH = 400
    MAX_HEIGHT = 520
    ROW_HEIGHT = 72

    def __init__(
        self,
        master=None,
        *,
        items: list[dict],
        slot: str,
        summary: str,
        on_ack: Callable[[dict, str], None],
    ):
        super().__init__(master)
        self._items = list(items)
        self._slot = slot
        self._summary = summary
        self._on_ack = on_ack
        self._row_frames: dict[int, ctk.CTkFrame] = {}
        self._acked: set[int] = set()
        self.title("タスクリマインド")
        est_h = min(self.MAX_HEIGHT, 140 + len(self._items) * self.ROW_HEIGHT)
        self.geometry(f"{self.WIDTH}x{est_h}")
        self.minsize(self.WIDTH, 200)
        self.maxsize(self.WIDTH, self.MAX_HEIGHT)
        self.resizable(True, True)
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
        self.protocol("WM_DELETE_WINDOW", self._on_dismiss_all_continue)
        self.lift()
        self.focus_force()

    def _position_near(self, master) -> None:
        if master is None:
            self.update_idletasks()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            h = self.winfo_height()
            x = sw - self.WIDTH - 24
            y = sh - h - 80
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
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=pad, pady=(pad, 4))
        count = len(self._items)
        ctk.CTkLabel(
            header,
            text=f"Today のタスク（{count}件）",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            header,
            text=self._summary,
            wraplength=self.WIDTH - pad * 2,
            justify="left",
            anchor="w",
            text_color=("gray25", "gray75"),
        ).pack(fill="x", pady=(4, 0))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=pad, pady=(4, pad))

        show_consult = is_feature_enabled("brainstorm")
        for item in self._items:
            self._add_task_row(scroll, item, show_consult)

        ctk.CTkButton(
            self,
            text="閉じる（未操作は継続）",
            command=self._on_dismiss_all_continue,
            fg_color=("gray70", "gray35"),
            hover_color=("gray60", "gray45"),
        ).pack(fill="x", padx=pad, pady=(0, pad))

    def _add_task_row(self, parent, item: dict, show_consult: bool) -> None:
        note_id = item["note_id"]
        row = ctk.CTkFrame(parent, corner_radius=8)
        row.pack(fill="x", pady=(0, 8))
        self._row_frames[note_id] = row

        title = item.get("title") or "（無題）"
        ctk.CTkLabel(
            row,
            text=title,
            wraplength=self.WIDTH - 80,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(fill="x", padx=10, pady=(8, 4))

        btn_row = ctk.CTkFrame(row, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(
            btn_row,
            text="継続",
            width=72,
            height=28,
            font=ctk.CTkFont(size=12),
            command=lambda i=item: self._on_action(i, "continue"),
            fg_color=("#5a9a5c", "#2e7d32"),
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            btn_row,
            text="完了",
            width=72,
            height=28,
            font=ctk.CTkFont(size=12),
            command=lambda i=item: self._on_action(i, "done"),
            fg_color=("#3d7ea6", "#1565c0"),
        ).pack(side="left", padx=(0, 4))
        if show_consult:
            ctk.CTkButton(
                btn_row,
                text="相談",
                width=72,
                height=28,
                font=ctk.CTkFont(size=12),
                command=lambda i=item: self._on_consult(i),
                fg_color=("#7b5ea7", "#5e35b1"),
            ).pack(side="left")

    def _on_action(self, item: dict, action: str) -> None:
        note_id = item["note_id"]
        if note_id in self._acked:
            return
        self._acked.add(note_id)
        try:
            self._on_ack(item, action)
        except Exception as e:
            print(f"[task_remind] ack callback error: {e}", flush=True)
        self._remove_row(note_id)
        if not self._row_frames:
            self._close()

    def _on_consult(self, item: dict) -> None:
        title = item.get("title") or ""
        note_id = item.get("note_id")
        self._on_action(item, "continue")
        try:
            from chat_panel import open_chat_panel_with_task
            open_chat_panel_with_task(
                master=self.master,
                task_title=title,
                note_id=note_id,
            )
        except Exception as e:
            print(f"[task_remind] consult open failed: {e}", flush=True)

    def _remove_row(self, note_id: int) -> None:
        frame = self._row_frames.pop(note_id, None)
        if frame is not None:
            try:
                frame.destroy()
            except Exception:
                pass

    def _on_dismiss_all_continue(self) -> None:
        for item in list(self._items):
            nid = item["note_id"]
            if nid not in self._acked:
                self._acked.add(nid)
                try:
                    self._on_ack(item, "continue")
                except Exception:
                    pass
        self._close()

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
    items: list[dict],
    slot: str,
    on_ack: Callable[[dict, str], None],
    summary: Optional[str] = None,
) -> Optional[TaskRemindListDialog]:
    """Today タスク一覧のリマインドダイアログを表示（シングルトン）。"""
    global _dialog_instance
    if not items:
        return None
    if _dialog_instance is not None:
        try:
            _dialog_instance.lift()
            return _dialog_instance
        except Exception:
            _dialog_instance = None

    cfg = load_config()
    from task_remind_client import post_shown_all, notify_dialog_closed
    if not post_shown_all(cfg, items, slot):
        notify_dialog_closed()
        print("[task_remind] shown API 失敗 — リマインドをスキップ", flush=True)
        return None

    summary_text = (summary or LIST_SUMMARY_MESSAGE).strip()
    count = len(items)
    if count > 1 and "件" not in summary_text:
        summary_text = f"{summary_text}\n（{count}件）"

    def _show_bubble():
        try:
            from notifications import are_enabled
            if not are_enabled():
                return
            if not is_feature_enabled("linko_avatar"):
                return
            import linko_avatar
            linko_avatar.say(summary_text.split("\n")[0], duration_sec=10, lipsync=False)
        except Exception:
            pass

    def _show_toast():
        try:
            from notifications import are_enabled, show_toast
            if not are_enabled():
                return
            titles = "、".join((it.get("title") or "")[:20] for it in items[:5])
            if len(items) > 5:
                titles += f" ほか{len(items) - 5}件"
            show_toast(
                "Wonder Linko",
                f"{LIST_SUMMARY_MESSAGE}\n{titles}\n（横のパネルで選択してください）",
                duration_sec=12,
            )
        except Exception:
            pass

    _show_toast()
    _show_bubble()
    _dialog_instance = TaskRemindListDialog(
        master=master,
        items=items,
        slot=slot,
        summary=summary_text,
        on_ack=on_ack,
    )
    return _dialog_instance
