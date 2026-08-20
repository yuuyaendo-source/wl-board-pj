# -*- coding: utf-8 -*-
"""社員向け『呼ばれ方（呼び名・敬称・読み）を編集』ダイアログ。

本人確認はセルフ顔登録と同じ メール→OTP（self_register_token）。
編集できるのは自分の 呼び名(call_name) / 敬称(honorific) / 呼び名の読み(call_name_kana)。
"""
from __future__ import annotations

import threading
from typing import Optional

try:
    import customtkinter as ctk
except ImportError as e:
    print("customtkinter が見つかりません。", e)
    raise

from config_loader import load_config

_dialog_instance: Optional["EditNameDialog"] = None


class EditNameDialog(ctk.CTkToplevel):
    WIDTH = 500
    HEIGHT = 420

    def __init__(self, master=None, cfg: Optional[dict] = None):
        super().__init__(master)
        self.title("呼ばれ方を編集")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(440, 360)
        self.resizable(True, True)
        self.attributes("-topmost", True)

        self._cfg = dict(cfg) if cfg is not None else load_config()
        self._challenge_id = ""
        self._token = ""
        self._person_id = ""
        self._person_name = ""
        self._step = ""

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=12, pady=12)
        self._status = ctk.CTkLabel(
            self._body, text="", anchor="w", wraplength=self.WIDTH - 40
        )
        self._status.pack(fill="x", pady=(0, 8))
        self._content = ctk.CTkFrame(self._body, fg_color="transparent")
        self._content.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(self._body, fg_color="transparent")
        footer.pack(fill="x", pady=(8, 0))
        self._btn_back = ctk.CTkButton(
            footer,
            text="戻る",
            command=self._on_back,
            fg_color="transparent",
            border_width=1,
            width=90,
        )
        self._btn_back.pack(side="left")
        self._btn_next = ctk.CTkButton(
            footer, text="次へ", command=self._on_next, width=110
        )
        self._btn_next.pack(side="right")
        ctk.CTkButton(
            footer,
            text="閉じる",
            command=self._on_close,
            fg_color="transparent",
            border_width=1,
            width=90,
        ).pack(side="right", padx=(0, 8))

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()
        self.after(50, self._show_email_step)

    # --- 共通 --------------------------------------------------------------
    def _clear_content(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()

    def _err(self, title: str, msg: str) -> None:
        from tkinter import messagebox

        messagebox.showerror(title, msg, parent=self)

    def _info(self, title: str, msg: str) -> None:
        from tkinter import messagebox

        messagebox.showinfo(title, msg, parent=self)

    def _on_close(self) -> None:
        global _dialog_instance
        _dialog_instance = None
        try:
            self.destroy()
        except Exception:
            pass

    def _on_back(self) -> None:
        if self._step == "otp":
            self._show_email_step()
        elif self._step == "edit":
            self._show_email_step()

    def _on_next(self) -> None:
        if self._step == "email":
            self._submit_email()
        elif self._step == "otp":
            self._submit_otp()
        elif self._step == "edit":
            self._submit_profile()

    # --- ステップ: メール ---------------------------------------------------
    def _show_email_step(self) -> None:
        self._step = "email"
        self._clear_content()
        from config_loader import get_board_system_login_email

        prefill = get_board_system_login_email(self._cfg)
        self._status.configure(
            text="本人確認のため、社内名簿のメールに確認コードを送ります。"
            + ("（ログイン中のメールをセットしました）" if prefill else "")
        )
        ctk.CTkLabel(self._content, text="メールアドレス", anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self._email_entry = ctk.CTkEntry(
            self._content, placeholder_text="name@example.com"
        )
        self._email_entry.pack(fill="x")
        if prefill:
            self._email_entry.insert(0, prefill)
        self._btn_back.configure(state="disabled")
        self._btn_next.configure(text="コードを送信", state="normal")

    def _submit_email(self) -> None:
        from face_registry_self_client import FaceSelfRegisterError, start_self_register

        email = (self._email_entry.get() or "").strip()
        if not email or "@" not in email:
            self._err("メール", "有効なメールアドレスを入力してください。")
            return
        self._btn_next.configure(state="disabled")
        self._status.configure(text="送信中…")

        def work():
            try:
                self._cfg = load_config()
                data = start_self_register(self._cfg, email)
            except FaceSelfRegisterError as e:
                self.after(0, lambda: self._fail(str(e)))
                return
            self.after(0, lambda: self._email_done(data))

        threading.Thread(target=work, daemon=True).start()

    def _email_done(self, data: dict) -> None:
        self._btn_next.configure(state="normal")
        self._challenge_id = str(data.get("challenge_id") or "")
        masked = str(data.get("email_masked") or "")
        if not self._challenge_id:
            self._err(
                "送信", "確認コードを送信できませんでした。メールをご確認ください。"
            )
            return
        self._show_otp_step(masked)

    # --- ステップ: OTP ------------------------------------------------------
    def _show_otp_step(self, email_masked: str) -> None:
        self._step = "otp"
        self._clear_content()
        self._status.configure(
            text=f"{email_masked} に送信した確認コードを入力してください。"
        )
        ctk.CTkLabel(self._content, text="確認コード（6桁）", anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self._otp_entry = ctk.CTkEntry(self._content, placeholder_text="123456")
        self._otp_entry.pack(fill="x")
        self._btn_back.configure(state="normal")
        self._btn_next.configure(text="確認", state="normal")

    def _submit_otp(self) -> None:
        from face_registry_self_client import (
            FaceSelfRegisterError,
            get_self_profile,
            verify_self_register,
        )

        otp = (self._otp_entry.get() or "").strip()
        if not otp:
            self._err("確認コード", "確認コードを入力してください。")
            return
        self._btn_next.configure(state="disabled")
        self._status.configure(text="確認中…")

        def work():
            try:
                data = verify_self_register(self._cfg, self._challenge_id, otp)
                token = str(data.get("self_register_token") or "")
                pid = str(data.get("person_id") or "")
                if not token or not pid:
                    self.after(
                        0,
                        lambda: self._fail("確認コードが正しくないか、期限切れです。"),
                    )
                    return
                profile = get_self_profile(self._cfg, pid, token)
            except FaceSelfRegisterError as e:
                self.after(0, lambda: self._fail(str(e)))
                return
            self.after(0, lambda: self._otp_done(token, pid, profile))

        threading.Thread(target=work, daemon=True).start()

    def _otp_done(self, token: str, pid: str, profile: dict) -> None:
        self._btn_next.configure(state="normal")
        self._token = token
        self._person_id = pid
        self._person_name = str(profile.get("name") or "")
        self._show_edit_step(profile)

    # --- ステップ: 編集 -----------------------------------------------------
    def _show_edit_step(self, profile: dict) -> None:
        self._step = "edit"
        self._clear_content()
        self._status.configure(
            text=f"{self._person_name or '本人'} さんの呼ばれ方を編集できます。"
            "（敬称を空欄にすると敬称なしで呼ばれます）"
        )

        def _row(label, value):
            ctk.CTkLabel(self._content, text=label, anchor="w").pack(
                fill="x", pady=(6, 2)
            )
            e = ctk.CTkEntry(self._content)
            e.pack(fill="x")
            if value:
                e.insert(0, value)
            return e

        self._call_name_entry = _row(
            "呼び名（リン子が呼ぶ名前）", profile.get("call_name") or ""
        )
        self._kana_entry = _row(
            "呼び名の読み（発話の読み）", profile.get("call_name_kana") or ""
        )
        # 敬称は「未設定＝さん」なので既定値を入れておく
        hon = profile.get("honorific")
        self._honorific_entry = _row(
            "敬称（さん / 様 / ちゃん / 空欄＝なし）", "さん" if hon is None else hon
        )

        self._btn_back.configure(state="normal")
        self._btn_next.configure(text="保存", state="normal")

    def _submit_profile(self) -> None:
        from face_registry_self_client import FaceSelfRegisterError, update_self_profile

        call_name = (self._call_name_entry.get() or "").strip()
        kana = (self._kana_entry.get() or "").strip()
        honorific = (self._honorific_entry.get() or "").strip()
        self._btn_next.configure(state="disabled")
        self._status.configure(text="保存中…")

        def work():
            try:
                update_self_profile(
                    self._cfg,
                    self._person_id,
                    self._token,
                    call_name=call_name,
                    honorific=honorific,
                    call_name_kana=kana,
                )
            except FaceSelfRegisterError as e:
                self.after(0, lambda: self._fail(str(e)))
                return
            self.after(0, self._profile_saved)

        threading.Thread(target=work, daemon=True).start()

    def _profile_saved(self) -> None:
        self._info(
            "保存しました", "呼ばれ方を更新しました。次回からリン子が反映します。"
        )
        self._on_close()

    # --- 失敗共通 -----------------------------------------------------------
    def _fail(self, msg: str) -> None:
        self._btn_next.configure(state="normal")
        self._status.configure(text="")
        self._err("エラー", msg)


def open_edit_name_dialog(master=None, cfg: Optional[dict] = None) -> "EditNameDialog":
    """呼ばれ方編集ダイアログを開く（多重起動は既存を前面へ）。"""
    global _dialog_instance
    if _dialog_instance is not None and _dialog_instance.winfo_exists():
        _dialog_instance.lift()
        _dialog_instance.focus_force()
        return _dialog_instance
    _dialog_instance = EditNameDialog(master=master, cfg=cfg)
    return _dialog_instance
