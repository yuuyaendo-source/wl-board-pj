# -*- coding: utf-8 -*-
"""社員向け顔セルフ登録ウィザード。"""
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

_dialog_instance: Optional["FaceSelfRegisterDialog"] = None
_capture_instance = None


class FaceSelfRegisterDialog(ctk.CTkToplevel):
    WIDTH = 500
    HEIGHT = 480

    def __init__(self, master=None, cfg: Optional[dict] = None):
        super().__init__(master)
        self.title("自分の顔を登録")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(440, 400)
        self.resizable(True, True)

        self._cfg = dict(cfg) if cfg is not None else load_config()
        self._status_data: dict = {}
        self._challenge_id: str = ""
        self._token: str = ""
        self._person_id: str = ""
        self._person_name: str = ""
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
            self._show_error("自分の顔を登録", str(e))
            self._on_close()
            return
        if not self._status_data.get("enabled"):
            self._show_error(
                "自分の顔を登録",
                "管理者がセルフ登録を有効にしていません。\n管理者に名簿登録・有効化を依頼してください。",
            )
            self._on_close()
            return
        self._show_consent_step()

    def _show_consent_step(self) -> None:
        self._step = "consent"
        self._clear_content()
        self._status.configure(text="")
        text = (self._status_data.get("consent_text_ja") or "").strip() or (
            "登録する顔画像は、入退室・執務室モード等での本人確認のために利用されます。"
        )
        ctk.CTkLabel(self._content, text=text, justify="left", anchor="w", wraplength=self.WIDTH - 48).pack(
            fill="x", pady=(0, 12)
        )
        ctk.CTkLabel(
            self._content,
            text="撮影は連写3枚です。照合データは最大5件（古いものから入れ替え）。",
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
        self._status.configure(text="社内名簿に登録されているメールアドレスを入力してください。")
        ctk.CTkLabel(self._content, text="メールアドレス", anchor="w").pack(fill="x", pady=(0, 4))
        self._email_entry = ctk.CTkEntry(self._content, placeholder_text="name@example.com")
        self._email_entry.pack(fill="x")
        self._btn_back.configure(state="normal")
        self._btn_next.configure(text="コードを送信")

    def _show_otp_step(self, email_masked: str) -> None:
        self._step = "otp"
        self._clear_content()
        self._status.configure(text=f"{email_masked} に送信した確認コードを入力してください。")
        ctk.CTkLabel(self._content, text="確認コード（6桁）", anchor="w").pack(fill="x", pady=(0, 4))
        self._otp_entry = ctk.CTkEntry(self._content, placeholder_text="123456")
        self._otp_entry.pack(fill="x")
        self._btn_next.configure(text="確認")

    def _on_back(self) -> None:
        if self._step == "email":
            self._show_consent_step()
        elif self._step == "otp":
            self._show_email_step()

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
        self._status.configure(text="送信中…")

        def work() -> None:
            try:
                self._cfg = load_config()
                data = start_self_register(self._cfg, email)
            except FaceSelfRegisterError as e:
                self.after(0, lambda: self._email_failed(str(e)))
                return
            self.after(0, lambda: self._email_done(data))

        threading.Thread(target=work, daemon=True).start()

    def _email_failed(self, msg: str) -> None:
        self._btn_next.configure(state="normal")
        self._status.configure(text="")
        self._show_error("送信", msg)

    def _email_done(self, data: dict) -> None:
        self._btn_next.configure(state="normal")
        if data.get("skip_otp") and data.get("self_register_token"):
            self._apply_session(data)
            self._open_capture(burst_count=3)
            return
        self._challenge_id = str(data.get("challenge_id") or "")
        masked = str(data.get("email_masked") or "")
        self._status.configure(text=str(data.get("message") or "確認コードを送信しました。"))
        if self._status_data.get("otp_required", True):
            self._show_otp_step(masked)
        else:
            self._show_info("送信", "メールを確認してください。")

    def _submit_otp(self) -> None:
        from face_registry_self_client import FaceSelfRegisterError, verify_self_register

        otp = (self._otp_entry.get() or "").strip()
        if not otp:
            self._show_error("確認コード", "確認コードを入力してください。")
            return
        self._btn_next.configure(state="disabled")
        self._status.configure(text="確認中…")

        def work() -> None:
            try:
                self._cfg = load_config()
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
        self._apply_session(data)
        self._open_capture(burst_count=3)

    def _apply_session(self, data: dict) -> None:
        self._token = str(data.get("self_register_token") or "")
        self._person_id = str(data.get("person_id") or "")
        self._person_name = str(data.get("person_name") or "")

    def _open_capture(self, *, burst_count: int = 3) -> None:
        global _capture_instance
        from face_registry_admin_dialog import FaceCaptureDialog

        if _capture_instance is not None:
            try:
                _capture_instance.lift()
                return
            except Exception:
                _capture_instance = None

        person_id = self._person_id
        person_name = self._person_name
        token = self._token

        def _upload(data_urls: List[str]) -> None:
            def work() -> None:
                from face_registry_self_client import FaceSelfRegisterError, upload_faces_self_serial

                self._cfg = load_config()
                try:
                    ok, total, err = upload_faces_self_serial(self._cfg, person_id, token, data_urls)
                except FaceSelfRegisterError as e:
                    self.after(0, lambda: self._show_error("顔登録", str(e)))
                    return
                prompt_glasses = burst_count >= 3 and ok == total and total >= 3
                self.after(
                    0,
                    lambda: self._on_faces_uploaded(person_id, person_name, token, ok, total, err, prompt_glasses),
                )

            threading.Thread(target=work, daemon=True).start()

        _capture_instance = FaceCaptureDialog(
            self, person_name=person_name, burst_count=burst_count, on_captured=_upload
        )

    def _on_faces_uploaded(
        self,
        person_id: str,
        person_name: str,
        token: str,
        ok: int,
        total: int,
        err: Optional[str],
        prompt_glasses: bool,
    ) -> None:
        if ok == 0:
            self._show_error("顔登録", err or "登録に失敗しました。")
            return
        if ok == total:
            if total == 1:
                msg = f"{person_name} さんの顔を1枚登録しました。"
            else:
                msg = f"{person_name} さんの顔を{ok}枚登録しました。"
        else:
            reason = err or "通信エラー"
            msg = f"{person_name} さんの顔を {ok}/{total} 枚登録しました（{total - ok}枚は{reason}）。"
        self._show_info("登録完了", msg)
        if prompt_glasses and ok == total:
            self._prompt_glasses_extra(person_id, person_name, token)

    def _prompt_glasses_extra(self, person_id: str, person_name: str, token: str) -> None:
        from tkinter import messagebox

        if messagebox.askyesno(
            "追加撮影",
            "眼鏡をかけて撮影した場合、外した状態でもう1枚追加すると認識率が上がります。追加撮影しますか？",
            parent=self,
        ):
            self._token = token
            self._person_id = person_id
            self._person_name = person_name
            self._open_capture(burst_count=1)

    def _on_close(self) -> None:
        global _dialog_instance
        _dialog_instance = None
        try:
            self.destroy()
        except Exception:
            pass


def open_face_self_register_dialog(master=None, cfg: Optional[dict] = None) -> Optional[FaceSelfRegisterDialog]:
    global _dialog_instance
    from config_loader import is_feature_enabled, load_config

    if cfg is None:
        cfg = load_config()
    if not is_feature_enabled("face_registry_self", cfg):
        from tkinter import messagebox

        if master is not None:
            messagebox.showinfo(
                "自分の顔を登録",
                "設定で「自分の顔を登録」を ON にしてください。",
                parent=master,
            )
        return None
    if not (cfg.get("linko_server_url") or "").strip():
        from tkinter import messagebox

        if master is not None:
            messagebox.showerror("自分の顔を登録", "linko_server_url が未設定です。", parent=master)
        return None

    if _dialog_instance is not None:
        try:
            _dialog_instance.lift()
            return _dialog_instance
        except Exception:
            _dialog_instance = None
    _dialog_instance = FaceSelfRegisterDialog(master=master, cfg=cfg)
    return _dialog_instance
