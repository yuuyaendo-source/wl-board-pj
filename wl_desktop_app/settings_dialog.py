# -*- coding: utf-8 -*-
"""設定ダイアログ。

v2 機能フラグ (features.*) の ON/OFF と、表示名・主要 URL の確認/編集を 1 画面で行う。

トレイメニュー or ミニポートから ``open_settings_dialog()`` を呼ぶ。
別スレッドから呼んでも安全なように、Tk のメインスレッドで実行されるよう
``after`` でディスパッチするのは呼び出し側の責任とする (Tk の制約)。
"""
from __future__ import annotations

import os
import sys
from typing import Optional

try:
    import customtkinter as ctk
    import tkinter as tk
except ImportError as e:  # 開発時 / venv 不整合での失敗を可視化
    print("customtkinter が見つかりません。pip install -r requirements.txt を実行してください。", e)
    raise

from config_loader import load_config, save_config


# --- features の表示メタデータ -------------------------------------------------
# (キー, 表示ラベル, 説明文)。features 追加時はここに 1 行足すだけで UI に反映される。
_FEATURE_ROWS = [
    (
        "taskbar_mode",
        "タスクバーに常駐",
        "フローティングのミニポートではなく、通常 Window としてタスクバーに常駐します。",
    ),
    (
        "linko_avatar",
        "リン子アバター表示",
        "ミニポート / Window にリン子の 2D アバター (表情切替) を表示します。",
    ),
    (
        "visitor_notify",
        "来客通知 (トーストでお知らせ)",
        "受付 (入口) で来客が検知されたとき、トースト通知でお知らせします。Chatwork 通知とは併用されます。",
    ),
    (
        "visitor_notify_sound",
        "来客通知に音声も鳴らす (visitor_notify が ON の場合)",
        "上記がONのとき、リン子の音声 (受付で再生されたものと同じ) もデスクトップで鳴らします。会議中などは OFF 推奨。",
    ),
    (
        "brainstorm",
        "ブレスト機能 (チャット・音声)",
        "業務サポート的なブレスト相手 (社内情報を踏まえた回答)。CATO 経由で社内 LAN 到達できることが前提。",
    ),
    (
        "task_remind",
        "個人タスクをリマインド (Today)",
        "Board System の Today タスクを 13:00 / 17:00 頃に確認します。[継続][完了][相談] で応答。要: パーソナルログイン。",
    ),
]


_dialog_instance: Optional["SettingsDialog"] = None


class SettingsDialog(ctk.CTkToplevel):
    """設定ダイアログ Window。シングルトンで運用する想定。"""

    WIDTH = 520
    HEIGHT = 660

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Wonder Linko 設定")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)
        try:
            # ウィンドウアイコンを assets/linko.ico に
            base = os.path.dirname(os.path.abspath(__file__))
            ico = os.path.join(base, "assets", "linko.ico")
            if os.path.isfile(ico) and sys.platform.startswith("win"):
                self.iconbitmap(ico)
        except Exception:
            pass

        self._cfg = load_config()
        self._feature_vars: dict[str, tk.BooleanVar] = {}
        self._display_name_var = tk.StringVar(value=self._cfg.get("display_name", "") or "")
        times = self._cfg.get("task_remind_times") or ["13:00", "17:00"]
        if isinstance(times, list):
            times_str = ", ".join(str(t) for t in times)
        else:
            times_str = "13:00, 17:00"
        self._task_remind_times_var = tk.StringVar(value=times_str)
        self._task_remind_weekdays_var = tk.BooleanVar(
            value=bool(self._cfg.get("task_remind_weekdays_only", True))
        )

        self._build_ui()

        # 閉じた後に再オープン可能にする
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()

    # --- UI 構築 -----------------------------------------------------------
    def _build_ui(self) -> None:
        pad = 12

        # 下部ボタンを先に bottom に確保 (features が増えても必ず見える)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad, pady=(6, pad), side="bottom")
        ctk.CTkButton(btn_frame, text="保存", command=self._on_save).pack(side="right")
        ctk.CTkButton(btn_frame, text="キャンセル", command=self._on_close).pack(
            side="right", padx=(0, 8)
        )
        # アップデート確認ボタン (左寄せ)
        ctk.CTkButton(
            btn_frame, text="🔄 アップデート確認", command=self._on_update_clicked,
            fg_color=("#dcefdd", "#22692a"), hover_color=("#c8e6c9", "#2e7d32"),
            text_color=("#1b5e20", "#e8f5e9"),
        ).pack(side="left")

        # タイトル
        title = ctk.CTkLabel(self, text="Wonder Linko 設定", font=("", 16, "bold"))
        title.pack(pady=(pad, 4), padx=pad, anchor="w")

        # 表示名
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", padx=pad, pady=(0, pad))
        ctk.CTkLabel(name_frame, text="表示名 (付箋の投稿者名)", anchor="w").pack(fill="x")
        ctk.CTkEntry(name_frame, textvariable=self._display_name_var).pack(fill="x", pady=(2, 0))

        # 機能見出し
        ctk.CTkLabel(self, text="機能 (任意でON)", font=("", 14, "bold")).pack(
            padx=pad, anchor="w", pady=(0, 2)
        )
        ctk.CTkLabel(
            self,
            text="基本 OFF。ONにした機能だけがバックグラウンドで動作します。",
            text_color=("gray40", "gray60"),
            anchor="w",
        ).pack(padx=pad, anchor="w", pady=(0, 4))

        # 機能チェックボックスはスクロール可能領域に (項目が増えても見切れない)
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        features = self._cfg.get("features") if isinstance(self._cfg.get("features"), dict) else {}
        for key, label, desc in _FEATURE_ROWS:
            var = tk.BooleanVar(value=bool(features.get(key, False)))
            self._feature_vars[key] = var
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=(0, 6))
            cb = ctk.CTkCheckBox(row, text=label, variable=var)
            cb.pack(anchor="w")
            ctk.CTkLabel(
                row,
                text=desc,
                text_color=("gray40", "gray60"),
                wraplength=self.WIDTH - 80,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=(28, 0))

        tr_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        tr_frame.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(tr_frame, text="タスクリマインド時刻 (HH:MM, カンマ区切り)", anchor="w").pack(fill="x")
        ctk.CTkEntry(tr_frame, textvariable=self._task_remind_times_var).pack(fill="x", pady=(2, 4))
        ctk.CTkCheckBox(
            tr_frame,
            text="平日のみ (土日は鳴らさない)",
            variable=self._task_remind_weekdays_var,
        ).pack(anchor="w")

    # --- ハンドラ ----------------------------------------------------------
    def _on_save(self) -> None:
        # 表示名は空白除去のみ。空文字も許可 (旧仕様準拠)
        self._cfg["display_name"] = self._display_name_var.get().strip()
        # features を辞書ごと書き出し (未知キーは保つ)
        features = dict(self._cfg.get("features") or {})
        for key, var in self._feature_vars.items():
            features[key] = bool(var.get())
        prev_visitor_notify = bool((self._cfg.get("features") or {}).get("visitor_notify"))
        self._cfg["features"] = features
        parsed_times = []
        for part in self._task_remind_times_var.get().replace("、", ",").split(","):
            s = part.strip()
            try:
                from task_remind_client import _normalize_time
                norm = _normalize_time(s)
            except Exception:
                norm = None
            if norm:
                parsed_times.append(norm)
        if parsed_times:
            self._cfg["task_remind_times"] = parsed_times
        self._cfg["task_remind_weekdays_only"] = bool(self._task_remind_weekdays_var.get())
        try:
            save_config(self._cfg)
            self._cfg = load_config()
            try:
                import sys
                main = sys.modules.get("__main__")
                if main is not None and hasattr(main, "_config"):
                    main._config = self._cfg
            except Exception:
                pass
        except Exception as e:
            try:
                from tkinter import messagebox
                messagebox.showerror("保存エラー", f"設定の保存に失敗しました: {e}")
            except Exception:
                print("config save failed:", e, flush=True)
            return
        # 来客通知の ON/OFF が変わったら接続を切替
        new_visitor_notify = bool(features.get("visitor_notify"))
        if new_visitor_notify != prev_visitor_notify:
            try:
                from visitor_notify_client import start_visitor_notify, stop_visitor_notify
                if new_visitor_notify:
                    start_visitor_notify()
                else:
                    stop_visitor_notify()
            except Exception as e:
                print(f"visitor_notify toggle failed: {e}", flush=True)
        self._on_close()

    def _on_update_clicked(self) -> None:
        """設定パネルの「アップデート確認」ボタン。手動で更新チェック → 確認 → インストール。"""
        from tkinter import messagebox
        try:
            from update_checker import check_for_update, download_and_install
            from version import __version__
            from config_loader import load_config
        except Exception as e:
            messagebox.showerror("アップデート", f"更新モジュールの読み込みに失敗: {e}")
            return
        url = (load_config().get("update_check_url") or "").strip()
        if not url:
            messagebox.showinfo("アップデート", "更新チェック URL が設定されていません。")
            return
        has_update, latest, download_url = check_for_update(__version__, url)
        if not has_update:
            messagebox.showinfo("アップデート", f"最新版です (v{__version__})。")
            return
        if not messagebox.askyesno(
            "アップデート",
            f"新しいバージョン {latest} があります。\n"
            "更新を開始するとアプリは一度終了し、完了後に自動で起動します。\n\n今すぐ更新しますか？",
        ):
            return
        # download_and_install は成功時 sys.exit する (バッチ経由で更新)
        ok, err = download_and_install(download_url)
        if not ok:
            messagebox.showerror("アップデート", f"更新に失敗しました:\n{err}")

    def _on_close(self) -> None:
        global _dialog_instance
        _dialog_instance = None
        try:
            self.destroy()
        except Exception:
            pass


def open_settings_dialog(master=None) -> SettingsDialog:
    """設定ダイアログを開く (シングルトン)。
    既に開いているなら前面化して既存インスタンスを返す。
    Tk のメインスレッド上から呼ぶこと。
    """
    global _dialog_instance
    if _dialog_instance is not None:
        try:
            _dialog_instance.lift()
            _dialog_instance.focus_force()
            return _dialog_instance
        except Exception:
            _dialog_instance = None
    _dialog_instance = SettingsDialog(master=master)
    return _dialog_instance


# 単体起動 (動作確認用)
if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    root = ctk.CTk()
    root.withdraw()
    open_settings_dialog(root)
    root.mainloop()
