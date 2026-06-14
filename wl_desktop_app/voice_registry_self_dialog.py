# -*- coding: utf-8 -*-
"""社員向け音声セルフ登録ウィザード（OTP 共通 + チャレンジ録音）。"""
from __future__ import annotations

import threading
from typing import List, Optional

try:
    import customtkinter as ctk
    import tkinter as tk
except ImportError as e:
    print("customtkinter が見つかりません。", e)
    raise

from config_loader import load_config

_dialog_instance: Optional["VoiceSelfRegisterDialog"] = None
_capture_instance = None


class VoiceSelfRegisterDialog(ctk.CTkToplevel):
    WIDTH = 500
    HEIGHT = 480

    def __init__(self, master=None, cfg: Optional[dict] = None):
        super().__init__(master)
        self.title("自分の声を登録")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(440, 400)
        self.resizable(True, True)
        self.attributes("-topmost", True)

        self._cfg = dict(cfg) if cfg is not None else load_config()
        self._status_data: dict = {}
        self._challenge_id: str = ""
        self._token: str = ""
        self._person_id: str = ""
        self._person_name: str = ""
        self._scopes: List[str] = []
        self._consent_var = tk.BooleanVar(value=False)

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=12, pady=12)

        self._status = ctk.CTkLabel(self._body, text="準備しています…", anchor="w", wraplength=self.WIDTH - 40)
        self._status.pack(fill="x", pady=(0, 8))

        self._content = ctk.CTkFrame(self._body, fg_color="transparent")
        self._content.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(self._body, fg_color="transparent")
        footer.pack(fill="x", pady=(8, 0))
        self._btn_back = ctk.CTkButton(
            footer, text="戻る", command=self._on_back, fg_color="transparent", border_width=1, width=90
        )
        self._btn_back.pack(side="left")
        self._btn_next = ctk.CTkButton(footer, text="次へ", command=self._on_next, width=100)
        self._btn_next.pack(side="right")
        ctk.CTkButton(footer, text="閉じる", command=self._on_close, fg_color="transparent", border_width=1, width=90).pack(
            side="right", padx=(0, 8)
        )

        self._step = ""
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()
        self.after(50, self._init_status)

    def _clear_content(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()

    def _show_error(self, title: str, msg: str) -> None:
        from tkinter import messagebox

        messagebox.showerror(title, msg, parent=self)

    def _show_info(self, title: str, msg: str) -> None:
        from tkinter import messagebox

        messagebox.showinfo(title, msg, parent=self)

    def _init_status(self) -> None:
        from face_registry_self_client import FaceSelfRegisterError, get_self_register_status

        self._cfg = load_config()
        try:
            self._status_data = get_self_register_status(self._cfg)
        except FaceSelfRegisterError as e:
            self._show_error("自分の声を登録", str(e))
            self._on_close()
            return
        if not self._status_data.get("voice_enabled"):
            self._show_error(
                "自分の声を登録",
                "管理者が音声セルフ登録を有効にしていません。\n管理者に名簿登録・有効化を依頼してください。",
            )
            self._on_close()
            return
        self._show_consent_step()

    def _show_consent_step(self) -> None:
        self._step = "consent"
        self._clear_content()
        self._status.configure(text="")
        text = (self._status_data.get("voice_consent_text_ja") or "").strip() or (
            "登録する音声は、エントランス等での本人確認・開錠のために利用されます。"
        )
        required = int(self._status_data.get("voice_samples_required") or 3)
        ctk.CTkLabel(self._content, text=text, justify="left", anchor="w", wraplength=self.WIDTH - 48).pack(
            fill="x", pady=(0, 12)
        )
        ctk.CTkLabel(
            self._content,
            text=(
                f"録音はチャレンジ付き {required} サンプルです。"
                "各回、画面に表示されるセリフをそのまま読み上げます。ファイルアップロードはできません。"
            ),
            text_color=("gray40", "gray60"),
            justify="left",
            anchor="w",
            wraplength=self.WIDTH - 48,
        ).pack(fill="x", pady=(0, 12))
        ctk.CTkCheckBox(self._content, text="上記に同意して登録を続ける", variable=self._consent_var).pack(anchor="w")
        self._btn_back.configure(state="disabled")
        self._btn_next.configure(text="次へ")

    def _show_email_step(self) -> None:
        self._step = "email"
        self._clear_content()
        from config_loader import get_board_system_login_email

        prefill = get_board_system_login_email(self._cfg)
        if prefill:
            self._status.configure(
                text="Board System にログイン済みのメールを入力欄にセットしました。変更する場合は編集してください。"
            )
        else:
            self._status.configure(text="社内名簿に登録されているメールアドレスを入力してください。")
        ctk.CTkLabel(self._content, text="メールアドレス", anchor="w").pack(fill="x", pady=(0, 4))
        self._email_entry = ctk.CTkEntry(self._content, placeholder_text="name@example.com")
        self._email_entry.pack(fill="x")
        if prefill:
            self._email_entry.insert(0, prefill)
        self._btn_back.configure(state="normal")
        self._btn_next.configure(text="コードを送信")

    def _show_otp_step(self, email_masked: str) -> None:
        self._step = "otp"
        self._clear_content()
        self._status.configure(text=f"{email_masked} に送信した確認コードを入力してください。")
        ctk.CTkLabel(self._content, text="確認コード（6桁）", anchor="w").pack(fill="x", pady=(0, 4))
        self._otp_entry = ctk.CTkEntry(self._content, placeholder_text="123456")
        self._otp_entry.pack(fill="x")
        self._btn_back.configure(state="normal")
        self._btn_next.configure(text="確認")

    def _on_back(self) -> None:
        if self._step == "otp":
            self._show_email_step()
        elif self._step == "email":
            self._show_consent_step()
        elif self._step == "consent":
            self._on_close()

    def _on_next(self) -> None:
        if self._step == "consent":
            if not self._consent_var.get():
                self._show_error("同意", "同意にチェックを入れてください。")
                return
            self._show_email_step()
        elif self._step == "email":
            self._submit_email()
        elif self._step == "otp":
            self._submit_otp()

    def _submit_email(self) -> None:
        from face_registry_self_client import FaceSelfRegisterError, start_self_register

        email = (self._email_entry.get() or "").strip()
        if not email or "@" not in email:
            self._show_error("メール", "有効なメールアドレスを入力してください。")
            return
        self._btn_next.configure(state="disabled")
        self._status.configure(text="送信しています…")

        def work() -> None:
            self._cfg = load_config()
            try:
                data = start_self_register(self._cfg, email)
            except FaceSelfRegisterError as e:
                self.after(0, lambda: self._email_failed(str(e)))
                return
            self.after(0, lambda: self._email_done(data))

        threading.Thread(target=work, daemon=True).start()

    def _email_failed(self, msg: str) -> None:
        self._btn_next.configure(state="normal")
        self._status.configure(text="")
        self._show_error("確認コード", msg)

    def _email_done(self, data: dict) -> None:
        self._btn_next.configure(state="normal")
        if data.get("skip_otp"):
            self._apply_session(data)
            self._open_capture()
            return
        self._challenge_id = str(data.get("challenge_id") or "")
        masked = str(data.get("email_masked") or "")
        self._status.configure(text="確認コードを送信しました（届かない場合は管理者に名簿登録を確認してください）。")
        self._show_otp_step(masked)

    def _submit_otp(self) -> None:
        from face_registry_self_client import FaceSelfRegisterError, verify_self_register

        otp = (self._otp_entry.get() or "").strip()
        if not otp:
            self._show_error("確認コード", "確認コードを入力してください。")
            return
        self._btn_next.configure(state="disabled")
        self._status.configure(text="確認しています…")

        def work() -> None:
            self._cfg = load_config()
            try:
                data = verify_self_register(self._cfg, self._challenge_id, otp)
            except FaceSelfRegisterError as e:
                self.after(0, lambda: self._otp_failed(str(e)))
                return
            self.after(0, lambda: self._otp_done(data))

        threading.Thread(target=work, daemon=True).start()

    def _otp_failed(self, msg: str) -> None:
        self._btn_next.configure(state="normal")
        self._status.configure(text="")
        self._show_error("確認コード", msg)

    def _otp_done(self, data: dict) -> None:
        self._btn_next.configure(state="normal")
        scopes = data.get("scopes") or []
        if isinstance(scopes, list) and "voice_put" not in scopes:
            self._show_error("自分の声を登録", "このセッションでは音声登録が許可されていません。")
            return
        self._apply_session(data)
        self._open_capture()

    def _apply_session(self, data: dict) -> None:
        self._token = str(data.get("self_register_token") or "")
        self._person_id = str(data.get("person_id") or "")
        self._person_name = str(data.get("person_name") or "")
        scopes = data.get("scopes") or []
        self._scopes = list(scopes) if isinstance(scopes, list) else []

    def _open_capture(self) -> None:
        begin_voice_self_capture(self, self._cfg, self._person_id, self._person_name, self._token)

    def _on_uploaded(self, ok: int, total: int, err: Optional[str]) -> None:
        if ok == 0:
            self._show_error("音声登録", err or "登録に失敗しました。")
            return
        if ok == total:
            msg = f"{self._person_name} さんの声を{ok}サンプル登録しました。"
        else:
            reason = err or "通信エラー"
            msg = f"{self._person_name} さんの声を {ok}/{total} サンプル登録しました（{total - ok}件は{reason}）。"
        self._show_info("登録完了", msg)
        self._on_close()

    def _on_close(self) -> None:
        global _dialog_instance
        _dialog_instance = None
        try:
            self.destroy()
        except Exception:
            pass


def begin_voice_self_capture(
    master,
    cfg: dict,
    person_id: str,
    person_name: str,
    token: str,
) -> None:
    """OTP 済みセッションでチャレンジ録音→アップロードを開始する。"""
    global _capture_instance
    from face_registry_admin_dialog import VoiceCaptureDialog
    from face_registry_self_client import FaceSelfRegisterError, get_voice_challenges, upload_voices_self_serial

    if _capture_instance is not None:
        try:
            _capture_instance.lift()
            return
        except Exception:
            _capture_instance = None

    try:
        ch_data = get_voice_challenges(cfg, token)
    except FaceSelfRegisterError as e:
        if master is not None and hasattr(master, "_show_error"):
            master._show_error("音声登録", str(e))
        return

    session_id = str(ch_data.get("session_id") or "")
    challenges = ch_data.get("challenges") or []
    if not session_id or not isinstance(challenges, list) or not challenges:
        if master is not None and hasattr(master, "_show_error"):
            master._show_error("音声登録", "チャレンジの取得に失敗しました。")
        return

    samples: list[tuple[str, str]] = []
    total = len(challenges)

    def _upload_all(items: list[tuple[str, str]]) -> None:
        def work() -> None:
            try:
                ok, total_n, err = upload_voices_self_serial(cfg, person_id, token, session_id, items)
            except FaceSelfRegisterError as e:
                if master is not None and hasattr(master, "after"):
                    master.after(0, lambda: master._on_uploaded(0, total, str(e)))
                return
            if master is not None and hasattr(master, "after"):
                master.after(0, lambda: master._on_uploaded(ok, total_n, err))

        threading.Thread(target=work, daemon=True).start()

    def capture_next(index: int) -> None:
        global _capture_instance
        if index >= total:
            _upload_all(list(samples))
            return
        ch = challenges[index]
        phrase = str(ch.get("phrase_ja") or "")
        cid = str(ch.get("challenge_id") or "")

        def on_one(data_url: str) -> None:
            samples.append((cid, data_url))
            capture_next(index + 1)

        _capture_instance = VoiceCaptureDialog(
            master,
            person_name=person_name,
            challenge_phrase=phrase,
            sample_index=index + 1,
            sample_total=total,
            on_captured=on_one,
        )
        _capture_instance.lift()
        _capture_instance.focus_force()
        _capture_instance.attributes("-topmost", True)

    capture_next(0)


def open_voice_self_register_dialog(master=None, cfg: Optional[dict] = None) -> Optional[VoiceSelfRegisterDialog]:
    global _dialog_instance
    from config_loader import is_feature_enabled, load_config

    if cfg is None:
        cfg = load_config()
    if not is_feature_enabled("voice_registry_self", cfg):
        from tkinter import messagebox

        if master is not None:
            messagebox.showinfo(
                "自分の声を登録",
                "設定で「自分の声を登録」を ON にしてください。",
                parent=master,
            )
        return None
    if not (cfg.get("linko_server_url") or "").strip():
        from tkinter import messagebox

        if master is not None:
            messagebox.showerror("自分の声を登録", "linko_server_url が未設定です。", parent=master)
        return None

    if _dialog_instance is not None:
        try:
            _dialog_instance.lift()
            _dialog_instance.focus_force()
            _dialog_instance.attributes("-topmost", True)
            return _dialog_instance
        except Exception:
            _dialog_instance = None

    _dialog_instance = VoiceSelfRegisterDialog(master, cfg=cfg)
    return _dialog_instance
