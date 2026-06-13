# -*- coding: utf-8 -*-
"""設定ダイアログ。

v2 機能フラグ (features.*) の ON/OFF と、表示名・主要 URL の確認/編集を 1 画面で行う。

トレイメニューまたはミニポートから ``open_settings_dialog()`` を呼ぶ。
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
from version import __version__


# --- features の表示メタデータ -------------------------------------------------
# (キー, 表示ラベル, 説明文)。features 追加時はここに 1 行足すだけで UI に反映される。
_TRAY_CLICK_OPTIONS = [
    ("postit", "付箋ボード"),
    ("personal", "パーソナル"),
    ("last_notification", "最後のお知らせ"),
]

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
        "Today のタスクを一覧で確認します（既定 13:00 / 17:00）。各タスクに [継続][完了][相談] で応答。要: パーソナルログイン。",
    ),
    (
        "calendar_notify",
        "カレンダー予定をリマインド",
        "Personal ボードで Google 連携済みのとき、開始の N 分前に通知（下で 1〜15 分を指定）。未連携時は何もしません。",
    ),
    (
        "calendar_create",
        "カレンダーに予定を登録 (リン子に依頼)",
        "ブレストで「明日14時に会議入れて」などと話しかけ、確認後に Google カレンダーへ登録。要: パーソナルログイン・Google 連携。",
    ),
    (
        "remind_voice",
        "リマインドをリン子の声で読み上げる",
        "タスク/カレンダーリマインド時に TTS 音声を再生 (要: linko_server_url)。会議中は OFF 推奨。",
    ),
    (
        "face_registry_manage",
        "社員・顔・音声の管理 (管理者)",
        "linko-system の社員名簿・顔・音声サンプルを管理（要: linko_admin_token）。管理者 PC のみ ON にしてください。",
    ),
    (
        "face_registry_self",
        "自分の顔を登録",
        "社内メールで本人確認後、自分の顔を登録（連写3枚）。要: linko 名簿にメール登録済み・社内ネットワーク。",
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
        from config_loader import normalize_calendar_remind_minutes

        self._calendar_remind_minutes_var = tk.StringVar(
            value=str(normalize_calendar_remind_minutes(self._cfg.get("calendar_remind_minutes_before")))
        )
        tray_labels = {k: v for k, v in _TRAY_CLICK_OPTIONS}
        tray_action = self._cfg.get("tray_click_action", "postit")
        self._tray_click_var = tk.StringVar(value=tray_labels.get(tray_action, "付箋ボード"))
        try:
            import startup

            startup_on = startup.is_startup_enabled()
        except Exception:
            startup_on = False
        self._startup_var = tk.BooleanVar(value=startup_on)
        self._linko_admin_token_var = tk.StringVar(value=self._cfg.get("linko_admin_token", "") or "")

        self._build_ui()

        # 閉じた後に再オープン可能にする
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()

    # --- UI 構築 -----------------------------------------------------------
    def _build_ui(self) -> None:
        pad = 12

        # 下部ボタンを先に bottom に確保
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad, pady=(6, pad), side="bottom")
        ctk.CTkButton(btn_frame, text="保存", command=self._on_save).pack(side="right")
        ctk.CTkButton(btn_frame, text="キャンセル", command=self._on_close).pack(
            side="right", padx=(0, 8)
        )
        ctk.CTkButton(
            btn_frame, text="🔄 アップデート確認", command=self._on_update_clicked,
            fg_color=("#dcefdd", "#22692a"), hover_color=("#c8e6c9", "#2e7d32"),
            text_color=("#1b5e20", "#e8f5e9"),
        ).pack(side="left")

        # 設定全体をスクロール（機能 ON/OFF だけでなく表示名・管理者操作も含む）
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=pad, pady=(pad, 0))

        ctk.CTkLabel(scroll, text="Wonder Linko 設定", font=("", 16, "bold")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            scroll,
            text=f"バージョン v{__version__}",
            text_color=("gray40", "gray60"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(scroll, text="表示名 (付箋の投稿者名)", anchor="w").pack(fill="x")
        ctk.CTkEntry(scroll, textvariable=self._display_name_var).pack(fill="x", pady=(2, 12))

        ctk.CTkLabel(scroll, text="トレイアイコン左クリックで開く先", anchor="w").pack(fill="x")
        ctk.CTkOptionMenu(
            scroll,
            values=[label for _, label in _TRAY_CLICK_OPTIONS],
            variable=self._tray_click_var,
            width=160,
        ).pack(anchor="w", pady=(2, 4))
        ctk.CTkCheckBox(
            scroll,
            text="PC起動時に自動で起動 (Windows)",
            variable=self._startup_var,
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(scroll, text="linko 管理者トークン (社員・顔・音声の管理)", anchor="w").pack(fill="x")
        ctk.CTkEntry(scroll, textvariable=self._linko_admin_token_var, show="*").pack(fill="x", pady=(2, 8))
        ctk.CTkButton(
            scroll,
            text="社員・顔・音声の管理を開く…",
            command=self._on_open_face_registry_admin,
        ).pack(anchor="w", fill="x")
        ctk.CTkButton(
            scroll,
            text="自分の顔を登録…",
            command=self._on_open_face_self_register,
        ).pack(anchor="w", fill="x", pady=(6, 12))

        ctk.CTkLabel(scroll, text="機能 (任意でON)", font=("", 14, "bold")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            scroll,
            text="基本 OFF。ONにした機能だけがバックグラウンドで動作します。",
            text_color=("gray40", "gray60"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        features = self._cfg.get("features") if isinstance(self._cfg.get("features"), dict) else {}
        for key, label, desc in _FEATURE_ROWS:
            var = tk.BooleanVar(value=bool(features.get(key, False)))
            self._feature_vars[key] = var
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=(0, 6))
            ctk.CTkCheckBox(row, text=label, variable=var).pack(anchor="w")
            ctk.CTkLabel(
                row,
                text=desc,
                text_color=("gray40", "gray60"),
                wraplength=self.WIDTH - 80,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=(28, 0))

        ctk.CTkLabel(scroll, text="タスクリマインド時刻 (HH:MM, カンマ区切り)", anchor="w").pack(fill="x", pady=(8, 0))
        ctk.CTkEntry(scroll, textvariable=self._task_remind_times_var).pack(fill="x", pady=(2, 4))
        ctk.CTkCheckBox(
            scroll,
            text="平日のみ (土日は鳴らさない)",
            variable=self._task_remind_weekdays_var,
        ).pack(anchor="w")
        ctk.CTkButton(
            scroll,
            text="今日はタスクリマインドを止める",
            command=self._on_pause_task_remind_today,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(scroll, text="カレンダーリマインド (開始の何分前)", anchor="w").pack(fill="x", pady=(12, 0))
        cal_row = ctk.CTkFrame(scroll, fg_color="transparent")
        cal_row.pack(fill="x", pady=(2, 8))
        ctk.CTkOptionMenu(
            cal_row,
            values=[str(i) for i in range(1, 16)],
            variable=self._calendar_remind_minutes_var,
            width=80,
        ).pack(side="left")
        ctk.CTkLabel(
            cal_row,
            text="分前（1〜15。calendar_notify が ON のとき有効）",
            text_color=("gray40", "gray60"),
        ).pack(side="left", padx=(8, 0))

    # --- ハンドラ ----------------------------------------------------------
    def _on_open_face_registry_admin(self) -> None:
        try:
            from face_registry_admin_dialog import open_face_registry_admin_dialog

            draft = dict(self._cfg)
            draft["linko_admin_token"] = self._linko_admin_token_var.get().strip()
            features = dict(draft.get("features") or {})
            if "face_registry_manage" in self._feature_vars:
                features["face_registry_manage"] = bool(self._feature_vars["face_registry_manage"].get())
            draft["features"] = features
            open_face_registry_admin_dialog(master=self, cfg=draft)
        except Exception as e:
            try:
                from tkinter import messagebox

                messagebox.showerror("社員・顔の管理", str(e), parent=self)
            except Exception:
                print(f"face registry admin open failed: {e}", flush=True)

    def _on_open_face_self_register(self) -> None:
        try:
            from face_registry_self_dialog import open_face_self_register_dialog

            draft = dict(self._cfg)
            features = dict(draft.get("features") or {})
            if "face_registry_self" in self._feature_vars:
                features["face_registry_self"] = bool(self._feature_vars["face_registry_self"].get())
            draft["features"] = features
            open_face_self_register_dialog(master=self, cfg=draft)
        except Exception as e:
            try:
                from tkinter import messagebox

                messagebox.showerror("自分の顔を登録", str(e), parent=self)
            except Exception:
                print(f"face self register open failed: {e}", flush=True)

    def _on_pause_task_remind_today(self) -> None:
        try:
            from tkinter import messagebox
            from task_remind_client import pause_reminders_today

            cfg = load_config()
            pause_reminders_today(cfg)
            messagebox.showinfo(
                "タスクリマインド",
                "今日はタスクリマインドを停止しました。明日から再開します。",
            )
        except Exception as e:
            try:
                from tkinter import messagebox
                messagebox.showerror("タスクリマインド", f"設定の保存に失敗しました: {e}")
            except Exception:
                print(f"task remind pause failed: {e}", flush=True)

    def _on_save(self) -> None:
        # 表示名は空白除去のみ。空文字も許可 (旧仕様準拠)
        self._cfg["display_name"] = self._display_name_var.get().strip()
        self._cfg["linko_admin_token"] = self._linko_admin_token_var.get().strip()
        tray_reverse = {label: key for key, label in _TRAY_CLICK_OPTIONS}
        self._cfg["tray_click_action"] = tray_reverse.get(self._tray_click_var.get(), "postit")
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
        from config_loader import normalize_calendar_remind_minutes

        self._cfg["calendar_remind_minutes_before"] = normalize_calendar_remind_minutes(
            self._calendar_remind_minutes_var.get()
        )
        import sys

        if sys.platform == "win32":
            try:
                import startup

                desired_startup = bool(self._startup_var.get())
                if desired_startup != startup.is_startup_enabled():
                    startup.set_startup_enabled(desired_startup)
            except Exception as e:
                print(f"startup toggle failed: {e}", flush=True)
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
