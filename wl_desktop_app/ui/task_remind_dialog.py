# -*- coding: utf-8 -*-
"""タスクリマインド用ダイアログ（Today 一覧・タスクごとに継続/完了/相談）。"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Callable, Optional
from zoneinfo import ZoneInfo

try:
    import customtkinter as ctk
except ImportError as e:
    print("customtkinter が見つかりません。", e)
    raise

from config_loader import is_feature_enabled, load_config

try:
    JST = ZoneInfo("Asia/Tokyo")
except Exception:
    from datetime import timedelta, timezone

    JST = timezone(timedelta(hours=9))

LIST_SUMMARY_MESSAGE = "本日のタスクの進捗はいかがですか？"

_dialog_instance: Optional["TaskRemindListDialog"] = None


def format_due_date_info(due_date_str: Optional[str]) -> tuple[str, str]:
    """due_date 文字列 (YYYY-MM-DD) から表示テキストとカラーコードを取得する。"""
    if not due_date_str:
        return "", ""
    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        return f"📅 期限: {due_date_str}", "#4b5563"

    today = datetime.now(JST).date()
    days = (due_date - today).days

    if days < 0:
        return f"⚠️ 期限切れ（{abs(days)}日経過）", "#ef4444"
    elif days == 0:
        return "🔥 本期日が期限！", "#ea580c"
    elif 0 < days <= 3:
        return f"⏰ 期限まであと{days}日", "#d97706"
    else:
        return f"📅 期限: {due_date_str}", "#2563eb"


def _ensure_master_visible(master) -> None:
    """タスクリマインド表示前にミニポートを前面へ。"""
    if master is None:
        return
    try:
        if str(master.state()) == "withdrawn":
            master.deiconify()
    except Exception:
        pass
    try:
        if hasattr(master, "focus_and_raise"):
            master.focus_and_raise()
        else:
            master.lift()
            master.attributes("-topmost", True)
    except Exception:
        pass


class TaskRemindListDialog(ctk.CTkToplevel):
    WIDTH = 420
    MAX_HEIGHT = 540
    ROW_HEIGHT = 90
    _GAP = 8

    @staticmethod
    def _rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2) -> bool:
        return not (x1 + w1 <= x2 or x1 >= x2 + w2 or y1 + h1 <= y2 or y1 >= y2 + h2)

    def __init__(
        self,
        master=None,
        *,
        items: list[dict],
        slot: str,
        summary: str,
        on_ack: Callable[[dict, str], None],
        on_open_cards: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master)
        self._items = list(items)
        self._slot = slot
        self._summary = summary
        self._on_ack = on_ack
        self._on_open_cards = on_open_cards
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
        _ensure_master_visible(master)
        if master is not None:
            try:
                self.transient(master)
            except Exception:
                pass
        self._position_near(master)
        self.protocol("WM_DELETE_WINDOW", self._on_dismiss_all_continue)
        try:
            if master is not None:
                self.lift(master)
        except Exception:
            pass
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

    def _position_near(self, master) -> None:
        """ミニポートの近く・画面内に収まる位置へ配置する（右側固定は画面外になりやすい）。"""
        self.update_idletasks()
        pw = self.winfo_width() or self.WIDTH
        ph = self.winfo_height() or 200
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        gap = self._GAP

        def clamp_x(x: int) -> int:
            return max(0, min(int(x), max(0, sw - pw - gap)))

        def clamp_y(y: int) -> int:
            return max(0, min(int(y), max(0, sh - ph - gap)))

        if master is None:
            x = clamp_x(sw - pw - 24)
            y = clamp_y(sh - ph - 80)
            self.geometry(f"+{x}+{y}")
            return

        try:
            master.update_idletasks()
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width() or 264
            mh = master.winfo_height() or 224

            def fits(x: int, y: int) -> bool:
                return (
                    x >= 0
                    and y >= 0
                    and x + pw <= sw
                    and y + ph <= sh
                    and not self._rects_overlap(x, y, pw, ph, mx, my, mw, mh)
                )

            candidates = [
                (mx + mw - pw, my - ph - gap),  # 上・右端揃え（ミニポート直上）
                (mx, my - ph - gap),  # 上・左端揃え
                (mx - pw - gap, my + mh - ph),  # 左・下揃え
                (mx - pw - gap, my),  # 左・上揃え
                (mx + mw - pw, my + mh + gap),  # 下・右端揃え
                (mx, my + mh + gap),  # 下・左端揃え
                (mx + mw + gap, my),  # 右（画面右端ならスキップされやすい）
            ]

            x, y = candidates[0]
            for cx, cy in candidates:
                cx, cy = clamp_x(cx), clamp_y(cy)
                if fits(cx, cy):
                    x, y = cx, cy
                    break
            else:
                x, y = clamp_x(mx + mw - pw), clamp_y(my - ph - gap)

            self.geometry(f"+{x}+{y}")
        except Exception:
            x = clamp_x(sw - pw - 24)
            y = clamp_y(sh - ph - 80)
            self.geometry(f"+{x}+{y}")

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

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=pad, pady=(0, pad))
        if self._on_open_cards is not None:
            ctk.CTkButton(
                footer,
                text="リン子カードを見る",
                command=self._on_open_cards,
                fg_color=("#16a34a", "#0e7a37"),
                hover_color=("#15803d", "#166534"),
            ).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            footer,
            text="閉じる（未操作は継続）",
            command=self._on_dismiss_all_continue,
            fg_color=("gray70", "gray35"),
            hover_color=("gray60", "gray45"),
        ).pack(fill="x")

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
        ).pack(fill="x", padx=10, pady=(6, 2))

        # 期限情報の表示を追加
        due_date_str = item.get("due_date")
        due_text, due_color = format_due_date_info(due_date_str)
        if due_text:
            ctk.CTkLabel(
                row,
                text=due_text,
                text_color=due_color,
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w",
            ).pack(fill="x", padx=10, pady=(0, 4))

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
    on_open_cards: Optional[Callable[[], None]] = None,
) -> Optional[TaskRemindListDialog]:
    """Today タスク一覧のリマインドダイアログを表示（シングルトン）。"""
    global _dialog_instance
    if not items:
        return None
    if _dialog_instance is not None:
        try:
            _ensure_master_visible(master)
            _dialog_instance.lift(master)
            _dialog_instance.attributes("-topmost", True)
            _dialog_instance.lift()
            _dialog_instance._position_near(master)
            return _dialog_instance
        except Exception:
            _dialog_instance = None

    cfg = load_config()
    from task_remind_client import (
        mark_slot_shown_today,
        notify_dialog_closed,
        post_shown_slot,
    )

    if not post_shown_slot(cfg, slot):
        notify_dialog_closed()
        print("[task_remind] shown_slot API 失敗 — リマインドをスキップ", flush=True)
        return None
    mark_slot_shown_today(cfg, slot)

    summary_text = (summary or LIST_SUMMARY_MESSAGE).strip()
    count = len(items)
    if count > 1 and "件" not in summary_text:
        summary_text = f"{summary_text}\n（{count}件）"

    from remind_notify import TASK_VOICE_TEXT, deliver_remind

    titles = "、".join((it.get("title") or "")[:20] for it in items[:5])
    if len(items) > 5:
        titles += f" ほか{len(items) - 5}件"
    bubble = summary_text.split("\n")[0]
    deliver_remind(
        "Wonder Linko",
        f"{LIST_SUMMARY_MESSAGE}\n{titles}\n（横のパネルで選択してください）",
        bubble,
        voice_text=TASK_VOICE_TEXT,
        duration_sec=12,
    )
    _dialog_instance = TaskRemindListDialog(
        master=master,
        items=items,
        slot=slot,
        summary=summary_text,
        on_ack=on_ack,
        on_open_cards=on_open_cards,
    )
    return _dialog_instance
