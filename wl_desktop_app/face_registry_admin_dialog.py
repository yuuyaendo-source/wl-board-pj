# -*- coding: utf-8 -*-
"""社員・顔の管理ダイアログ（linko-system /manager 相当・管理者 PC 用）。"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import threading
import base64
from typing import Callable, List, Optional

try:
    import customtkinter as ctk
    import tkinter as tk
except ImportError as e:
    print("customtkinter が見つかりません。", e)
    raise

from config_loader import load_config

_dialog_instance: Optional["FaceRegistryAdminDialog"] = None
_capture_instance: Optional["FaceCaptureDialog"] = None
_voice_capture_instance: Optional["VoiceCaptureDialog"] = None


class FaceCaptureDialog(ctk.CTkToplevel):
    """Webカメラプレビューから顔画像を撮影する（連写対応）。"""

    PREVIEW_W = 520
    PREVIEW_H = 293
    _BURST_GUIDES = (
        "正面を向いてください。顔を枠の中央に",
        "少しだけ左を向いてください",
        "少しだけ右を向いてください",
    )
    _COUNTDOWN_STEP_MS = 400
    _SHOT_INTERVAL_MS = 900

    def __init__(
        self,
        master=None,
        *,
        person_name: str = "",
        burst_count: int = 3,
        on_captured: Optional[Callable[[List[str]], None]] = None,
    ):
        super().__init__(master)
        self._on_captured = on_captured
        self._burst_count = max(1, int(burst_count))
        self._burst_shots: List[str] = []
        self._burst_index = 0
        self._burst_active = False
        self._cap = None
        self._preview_job: Optional[str] = None
        self._pil_ref = None
        self._ctk_img = None

        title_suffix = "（追加1枚）" if self._burst_count == 1 else f"（連写{self._burst_count}枚）"
        self.title(f"顔を撮影 — {person_name or '社員'}{title_suffix}")
        win_w = self.PREVIEW_W + 48
        win_h = 520
        self.geometry(f"{win_w}x{win_h}")
        self.minsize(400, 420)
        self.resizable(True, True)
        self.attributes("-topmost", True)

        pad = 12
        # 高 DPI でもボタンが隠れないよう、先に下部を確保する
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=pad, pady=(0, pad))
        self._btn_capture = ctk.CTkButton(btn_row, text="撮影して登録", command=self._on_capture, state="disabled")
        self._btn_capture.pack(side="left")
        self._btn_file = ctk.CTkButton(
            btn_row,
            text="画像ファイルを選択",
            command=self._on_pick_file,
            fg_color="transparent",
            border_width=1,
        )
        self._btn_file.pack(side="left", padx=(8, 0))
        ctk.CTkButton(btn_row, text="キャンセル", command=self._on_close, fg_color="transparent", border_width=1).pack(
            side="right"
        )

        self._preview = ctk.CTkLabel(
            self,
            text="",
            width=self.PREVIEW_W,
            height=self.PREVIEW_H,
            fg_color=("#222", "#111"),
        )
        self._preview.pack(fill="both", expand=True, padx=pad, pady=(4, 4))

        self._status = ctk.CTkLabel(self, text="カメラを起動しています…", anchor="w", wraplength=self.PREVIEW_W)
        self._status.pack(side="top", fill="x", padx=pad, pady=(pad, 4))

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._start_camera)

    def _start_camera(self) -> None:
        from webcam_capture import is_available, open_camera

        if not is_available():
            self._status.configure(
                text="Webカメラが使えません。「画像ファイルを選択」から登録するか、opencv-python / Pillow を確認してください。"
            )
            return
        self._cap = open_camera()
        if self._cap is None:
            self._status.configure(
                text="カメラを開けませんでした。他アプリの使用を終了するか、「画像ファイルを選択」で登録してください。"
            )
            return
        if self._burst_count > 1:
            hint = (
                f"「撮影して登録」で自動連写{self._burst_count}枚します。"
                "各枚の前にカウントダウンがあります。顔を枠の中央に合わせてください。"
            )
        else:
            hint = "顔を正面に向けて「撮影して登録」を押してください。"
        self._status.configure(text=hint)
        self._btn_capture.configure(state="normal")
        self._tick_preview()

    def _on_pick_file(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            parent=self,
            title="顔画像を選択",
            filetypes=[("画像", "*.jpg *.jpeg *.png *.webp"), ("すべて", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "rb") as f:
                raw = f.read()
            if not raw:
                self._status.configure(text="画像ファイルが空です。")
                return
            ext = os.path.splitext(path)[1].lower()
            mime = "image/jpeg"
            if ext == ".png":
                mime = "image/png"
            elif ext == ".webp":
                mime = "image/webp"
            b64 = base64.b64encode(raw).decode("ascii")
            data_url = f"data:{mime};base64,{b64}"
        except Exception as e:
            self._status.configure(text=f"画像の読み込みに失敗: {e}")
            return
        if self._on_captured:
            self._on_captured([data_url])
        self._on_close()

    def _tick_preview(self) -> None:
        if not self.winfo_exists():
            return
        from webcam_capture import bgr_to_pil_image, read_bgr_frame

        frame = read_bgr_frame(self._cap)
        if frame is not None:
            pil = bgr_to_pil_image(frame, max_width=self.PREVIEW_W)
            if pil is not None:
                self._pil_ref = pil
                self._ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=pil.size)
                self._preview.configure(image=self._ctk_img, text="")
        self._preview_job = self.after(66, self._tick_preview)

    def _set_capture_buttons(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._btn_capture.configure(state=state)
        self._btn_file.configure(state=state)

    def _on_capture(self) -> None:
        if self._burst_active:
            return
        self._set_capture_buttons(False)
        self._burst_shots = []
        self._burst_index = 0
        self._burst_active = True
        self._run_burst_countdown(3)

    def _guide_text(self) -> str:
        idx = min(self._burst_index, len(self._BURST_GUIDES) - 1)
        return self._BURST_GUIDES[idx]

    def _run_burst_countdown(self, countdown: int) -> None:
        if not self.winfo_exists():
            return
        if countdown > 0:
            self._status.configure(text=f"{self._guide_text()} … {countdown}")
            self.after(self._COUNTDOWN_STEP_MS, lambda: self._run_burst_countdown(countdown - 1))
            return
        self._status.configure(text=self._guide_text())
        self.after(150, self._capture_one_burst_shot)

    def _capture_one_burst_shot(self) -> None:
        from webcam_capture import capture_jpeg_data_url

        if not self.winfo_exists():
            return
        data_url = capture_jpeg_data_url(self._cap)
        if not data_url:
            self._status.configure(text="撮影に失敗しました。もう一度お試しください。")
            self._burst_active = False
            self._set_capture_buttons(True)
            return
        self._burst_shots.append(data_url)
        self._burst_index += 1
        if self._burst_index >= self._burst_count:
            self._finish_burst()
            return
        self._status.configure(
            text=f"{self._burst_index}/{self._burst_count} 枚撮影しました。次のポーズへ…"
        )
        self.after(self._SHOT_INTERVAL_MS, lambda: self._run_burst_countdown(3))

    def _finish_burst(self) -> None:
        self._burst_active = False
        urls = list(self._burst_shots)
        if self._on_captured and urls:
            self._on_captured(urls)
        self._on_close()

    def _on_close(self) -> None:
        global _capture_instance
        if self._preview_job:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
            self._preview_job = None
        from webcam_capture import release_camera

        release_camera(self._cap)
        self._cap = None
        _capture_instance = None
        try:
            self.destroy()
        except Exception:
            pass


class VoiceCaptureDialog(ctk.CTkToplevel):
    """マイクから音声サンプルを録音する（将来の話者照合用）。"""

    def __init__(self, master=None, *, person_name: str = "", on_captured: Optional[Callable[[str], None]] = None):
        super().__init__(master)
        self._on_captured = on_captured
        self._recording = False

        self.title(f"音声を録音 — {person_name or '社員'}")
        self.geometry("480x220")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        pad = 12
        self._status = ctk.CTkLabel(
            self,
            text="マイクの準備を確認しています…",
            anchor="w",
            wraplength=440,
            justify="left",
        )
        self._status.pack(fill="x", padx=pad, pady=(pad, 8))
        ctk.CTkLabel(
            self,
            text="例: 「おはようございます、○○です」のように、普段の声で話してください。",
            text_color=("gray40", "gray60"),
            wraplength=440,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=pad, pady=(0, 12))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=pad, pady=(0, pad))
        self._btn_record = ctk.CTkButton(btn_row, text="録音して登録（約4秒）", command=self._on_record, state="disabled")
        self._btn_record.pack(side="left")
        ctk.CTkButton(btn_row, text="キャンセル", command=self._on_close, fg_color="transparent", border_width=1).pack(
            side="right"
        )

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._check_mic)

    def _check_mic(self) -> None:
        from voice_capture import is_available

        if not is_available():
            self._status.configure(
                text="マイク録音が使えません。Windows で sounddevice / numpy をインストールし、マイクを許可してください。"
            )
            return
        self._status.configure(text="準備できました。「録音して登録」を押すと約4秒間録音します。")
        self._btn_record.configure(state="normal")

    def _on_record(self) -> None:
        if self._recording:
            return
        self._recording = True
        self._btn_record.configure(state="disabled")
        self._status.configure(text="録音中… 普段の声で話してください。")

        def work() -> None:
            from voice_capture import record_wav_data_url

            data_url = record_wav_data_url()
            self.after(0, lambda: self._finish_record(data_url))

        threading.Thread(target=work, daemon=True).start()

    def _finish_record(self, data_url: Optional[str]) -> None:
        self._recording = False
        if not data_url:
            self._status.configure(text="録音に失敗しました。マイク設定を確認して再試行してください。")
            self._btn_record.configure(state="normal")
            return
        if self._on_captured:
            self._on_captured(data_url)
        self._on_close()

    def _on_close(self) -> None:
        global _voice_capture_instance
        _voice_capture_instance = None
        try:
            self.destroy()
        except Exception:
            pass


class FaceRegistryAdminDialog(ctk.CTkToplevel):
    WIDTH = 760
    HEIGHT = 720

    def __init__(self, master=None, cfg: Optional[dict] = None):
        super().__init__(master)
        self.title("社員・顔・音声の管理")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(640, 500)
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            ico = os.path.join(base, "assets", "linko.ico")
            if os.path.isfile(ico) and sys.platform.startswith("win"):
                self.iconbitmap(ico)
        except Exception:
            pass

        self._cfg = dict(cfg) if cfg is not None else load_config()
        self._persons: list[dict] = []
        self._embeddings_key = "face_embeddings"
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()
        self.after(100, self._reload_list)

    def _build_ui(self) -> None:
        pad = 12
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=pad, pady=(pad, 4))
        ctk.CTkLabel(top, text="社員・顔・音声の管理", font=("", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(
            top,
            text=(
                "linko-system の名簿（/manager と同じデータ）。顔は撮影1回で連写3枚登録。"
                "照合データは最大5件（古いものから入れ替え）。表示写真は最新。音声は将来の話者照合用。"
                "要: linko_admin_token。"
            ),
            text_color=("gray40", "gray60"),
            wraplength=self.WIDTH - 40,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        add = ctk.CTkFrame(self)
        add.pack(fill="x", padx=pad, pady=(4, 8))
        ctk.CTkLabel(add, text="新規社員", font=("", 13, "bold")).pack(anchor="w", padx=10, pady=(8, 4))
        grid = ctk.CTkFrame(add, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(0, 8))
        self._new_name = ctk.CTkEntry(grid, placeholder_text="表示名")
        self._new_name.grid(row=0, column=0, padx=(0, 6), pady=3, sticky="ew")
        self._new_email = ctk.CTkEntry(grid, placeholder_text="メールアドレス")
        self._new_email.grid(row=0, column=1, padx=(0, 6), pady=3, sticky="ew")
        self._new_call = ctk.CTkEntry(grid, placeholder_text="呼び名（苗字など）")
        self._new_call.grid(row=1, column=0, padx=(0, 6), pady=3, sticky="ew")
        self._new_kana = ctk.CTkEntry(grid, placeholder_text="呼び名の読み（ひらがな）")
        self._new_kana.grid(row=1, column=1, padx=(0, 6), pady=3, sticky="ew")
        self._new_dept = ctk.CTkEntry(grid, placeholder_text="部署")
        self._new_dept.grid(row=2, column=0, padx=(0, 6), pady=3, sticky="ew")
        self._new_staff = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(grid, text="社員", variable=self._new_staff).grid(row=2, column=1, sticky="w", pady=3)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        row_btns = ctk.CTkFrame(add, fg_color="transparent")
        row_btns.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(row_btns, text="追加", width=100, command=self._on_add).pack(side="left")
        ctk.CTkButton(row_btns, text="Workspace 同期", width=140, command=self._on_workspace_sync).pack(side="left", padx=(8, 0))

        self._list_scroll = ctk.CTkScrollableFrame(self, label_text="登録一覧")
        self._list_scroll.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=pad, pady=(0, pad))
        ctk.CTkButton(bottom, text="閉じる", command=self._on_close).pack(side="right")
        ctk.CTkButton(bottom, text="一覧を更新", command=self._reload_list).pack(side="right", padx=(0, 8))

    def _show_error(self, title: str, msg: str, parent=None) -> None:
        from tkinter import messagebox

        messagebox.showerror(title, msg, parent=parent or self)

    def _show_info(self, title: str, msg: str) -> None:
        from tkinter import messagebox

        messagebox.showinfo(title, msg, parent=self)

    def _reload_list(self) -> None:
        from face_registry_client import FaceRegistryError, list_registry

        self._cfg = load_config()
        for w in self._list_scroll.winfo_children():
            w.destroy()
        try:
            reg = list_registry(self._cfg)
            self._persons = reg.get("persons") or []
            self._embeddings_key = str(reg.get("embeddings_key") or "face_embeddings")
        except FaceRegistryError as e:
            ctk.CTkLabel(self._list_scroll, text=f"読み込み失敗: {e}", text_color="#c66").pack(anchor="w", pady=8)
            return
        if not self._persons:
            ctk.CTkLabel(
                self._list_scroll,
                text="登録がありません。上のフォームから社員を追加し、顔・音声を登録してください。",
                text_color=("gray40", "gray60"),
                wraplength=self.WIDTH - 60,
                justify="left",
            ).pack(anchor="w", pady=8)
            return
        for p in self._persons:
            self._render_person_row(p)

    def _render_person_row(self, p: dict) -> None:
        pid = str(p.get("id") or "")
        frame = ctk.CTkFrame(self._list_scroll)
        frame.pack(fill="x", pady=4)

        name = (p.get("name") or "").strip() or "(無名)"
        email = (p.get("email") or "").strip()
        call_name = (p.get("call_name") or "").strip()
        kana = (p.get("call_name_kana") or "").strip()
        dept = (p.get("department") or "").strip()
        is_staff = p.get("is_staff", True)
        has_face = bool(p.get("hasFace"))
        has_voice = bool(p.get("hasVoice"))
        from face_registry_client import embedding_count_for_person

        emb_n = embedding_count_for_person(p, self._embeddings_key) if has_face else 0

        head = ctk.CTkFrame(frame, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(head, text=name, font=("", 14, "bold")).pack(side="left")
        badges = ctk.CTkFrame(head, fg_color="transparent")
        badges.pack(side="right")
        face_badge = f"顔登録済み（照合データ {emb_n}/5）" if has_face else "顔なし"
        ctk.CTkLabel(
            badges,
            text=face_badge,
            text_color=("#1b6b3a", "#8fdfb0") if has_face else ("gray50", "gray60"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            badges,
            text="音あり" if has_voice else "音なし",
            text_color=("#1b4a6b", "#8fcfdf") if has_voice else ("gray50", "gray60"),
        ).pack(side="left")

        meta_parts = []
        if is_staff:
            meta_parts.append("社員")
        if email:
            meta_parts.append(email)
        if call_name:
            meta_parts.append(f"呼び名: {call_name}" + (f"（{kana}）" if kana else ""))
        if dept:
            meta_parts.append(f"部署: {dept}")
        ctk.CTkLabel(
            frame,
            text="　".join(meta_parts) if meta_parts else "（情報なし）",
            text_color=("gray40", "gray60"),
            wraplength=self.WIDTH - 80,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 6))

        btns1 = ctk.CTkFrame(frame, fg_color="transparent")
        btns1.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkButton(
            btns1,
            text="顔を撮影" if not has_face else "顔を追加",
            width=88,
            command=lambda i=pid, n=name: self._open_capture(i, n),
        ).pack(side="left")
        ctk.CTkButton(
            btns1,
            text="顔を確認",
            width=80,
            state="normal" if has_face else "disabled",
            command=lambda i=pid, n=name: self._view_face(i, n),
        ).pack(side="left", padx=(6, 0))
        ctk.CTkButton(
            btns1,
            text="顔を削除",
            width=80,
            state="normal" if has_face else "disabled",
            fg_color=("#4a3030", "#3a2525"),
            hover_color=("#5a3838", "#4a3030"),
            command=lambda i=pid, n=name: self._delete_face(i, n),
        ).pack(side="left", padx=(6, 0))
        ctk.CTkButton(
            btns1,
            text="音声を録音" if not has_voice else "音声を変更",
            width=88,
            command=lambda i=pid, n=name: self._open_voice_capture(i, n),
        ).pack(side="left", padx=(12, 0))
        ctk.CTkButton(
            btns1,
            text="音声を確認",
            width=80,
            state="normal" if has_voice else "disabled",
            command=lambda i=pid, n=name: self._play_voice(i, n),
        ).pack(side="left", padx=(6, 0))
        ctk.CTkButton(
            btns1,
            text="音声を削除",
            width=80,
            state="normal" if has_voice else "disabled",
            fg_color=("#4a3030", "#3a2525"),
            hover_color=("#5a3838", "#4a3030"),
            command=lambda i=pid, n=name: self._delete_voice(i, n),
        ).pack(side="left", padx=(6, 0))

        btns2 = ctk.CTkFrame(frame, fg_color="transparent")
        btns2.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkButton(btns2, text="情報を編集", width=90, command=lambda i=pid: self._open_edit(i)).pack(side="left")
        ctk.CTkButton(
            btns2,
            text="社員を削除",
            width=88,
            fg_color=("#5a2a2a", "#3d1f1f"),
            hover_color=("#7a3535", "#552828"),
            command=lambda i=pid, n=name: self._on_delete(i, n),
        ).pack(side="right")

    def _open_capture(self, person_id: str, person_name: str, *, burst_count: int = 3) -> None:
        global _capture_instance
        if _capture_instance is not None:
            try:
                _capture_instance.lift()
                return
            except Exception:
                _capture_instance = None

        def _upload(data_urls: List[str]) -> None:
            def work() -> None:
                from face_registry_client import FaceRegistryError, upload_faces_serial

                self._cfg = load_config()
                try:
                    ok, total, err = upload_faces_serial(self._cfg, person_id, data_urls)
                except FaceRegistryError as e:
                    self.after(0, lambda: self._show_error("顔登録", str(e)))
                    return
                prompt_glasses = burst_count >= 3 and ok == total and total >= 3
                self.after(
                    0,
                    lambda: self._on_faces_uploaded(
                        person_id, person_name, ok, total, err, prompt_glasses=prompt_glasses
                    ),
                )

            threading.Thread(target=work, daemon=True).start()

        _capture_instance = FaceCaptureDialog(
            self, person_name=person_name, burst_count=burst_count, on_captured=_upload
        )

    def _on_faces_uploaded(
        self,
        person_id: str,
        person_name: str,
        ok: int,
        total: int,
        err: Optional[str],
        *,
        prompt_glasses: bool,
    ) -> None:
        if ok == 0:
            self._show_error("顔登録", err or "登録に失敗しました。")
        elif ok == total:
            if total == 1:
                msg = f"{person_name} の顔を1枚登録しました。\n「顔を確認」で画像を表示できます。"
            else:
                msg = f"{person_name} の顔を{ok}枚登録しました。\n「顔を確認」で画像を表示できます。"
            self._show_info("顔登録", msg)
        else:
            reason = err or "通信エラー"
            self._show_info(
                "顔登録",
                f"{person_name} の顔を {ok}/{total} 枚登録しました（{total - ok}枚は{reason}）。",
            )
        self._reload_list()
        if prompt_glasses and ok == total:
            self._prompt_glasses_extra(person_id, person_name)

    def _prompt_glasses_extra(self, person_id: str, person_name: str) -> None:
        from tkinter import messagebox

        if messagebox.askyesno(
            "追加撮影",
            "眼鏡をかけて撮影した場合、外した状態でもう1枚追加すると認識率が上がります。追加撮影しますか？",
            parent=self,
        ):
            self._open_capture(person_id, person_name, burst_count=1)

    def _open_voice_capture(self, person_id: str, person_name: str) -> None:
        global _voice_capture_instance
        if _voice_capture_instance is not None:
            try:
                _voice_capture_instance.lift()
                return
            except Exception:
                _voice_capture_instance = None

        def _upload(data_url: str) -> None:
            from face_registry_client import FaceRegistryError, update_voice

            self._cfg = load_config()
            try:
                update_voice(self._cfg, person_id, data_url)
            except FaceRegistryError as e:
                self.after(0, lambda: self._show_error("音声登録", str(e)))
                return
            self.after(
                0,
                lambda: self._show_info(
                    "音声登録",
                    f"{person_name} の音声を登録しました。\n「音声を確認」で再生できます。",
                ),
            )
            self.after(0, self._reload_list)

        _voice_capture_instance = VoiceCaptureDialog(self, person_name=person_name, on_captured=_upload)

    def _data_url_to_pil(self, data_url: str):
        from PIL import Image

        if not data_url or "," not in data_url:
            return None
        try:
            raw = base64.b64decode(data_url.split(",", 1)[1])
            return Image.open(io.BytesIO(raw))
        except Exception:
            return None

    def _view_face(self, person_id: str, person_name: str) -> None:
        from face_registry_client import FaceRegistryError, embedding_count_for_person, get_person

        try:
            from PIL import Image
        except ImportError:
            self._show_error("顔を確認", "Pillow が利用できません。")
            return
        self._cfg = load_config()
        try:
            detail = get_person(self._cfg, person_id)
        except FaceRegistryError as e:
            self._show_error("顔を確認", str(e))
            return

        emb_n = embedding_count_for_person(detail, self._embeddings_key)
        items: list[tuple[str, str]] = []
        face_data = detail.get("faceData")
        if isinstance(face_data, str) and face_data.strip():
            items.append(("現在", face_data.strip()))
        gallery = detail.get("face_gallery")
        if isinstance(gallery, list):
            for i, entry in enumerate(gallery):
                if not isinstance(entry, dict):
                    continue
                url = entry.get("dataUrl") or entry.get("data_url")
                if isinstance(url, str) and url.strip():
                    items.append((f"履歴 {i + 1}", url.strip()))

        if not items:
            self._show_error("顔を確認", "登録画像がありません。")
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"登録画像（{len(items)}枚）・照合データ {emb_n}/5 — {person_name}")
        dlg.geometry("560x520")
        dlg.minsize(400, 320)
        dlg.attributes("-topmost", True)

        pad = 12
        scroll = ctk.CTkScrollableFrame(dlg, label_text="サムネイル")
        scroll.pack(fill="both", expand=True, padx=pad, pady=(pad, 4))

        thumb_max = 200
        refs: list = []
        for label, data_url in items:
            pil = self._data_url_to_pil(data_url)
            if pil is None:
                continue
            w, h = pil.size
            if w > thumb_max:
                h = int(h * thumb_max / w)
                w = thumb_max
                pil = pil.resize((w, h), Image.Resampling.LANCZOS)
            ctk.CTkLabel(scroll, text=label, anchor="w").pack(anchor="w", pady=(8, 2))
            img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(w, h))
            refs.append(img)
            lbl = ctk.CTkLabel(scroll, text="", image=img)
            lbl.pack(anchor="w", pady=(0, 4))

        ctk.CTkButton(dlg, text="閉じる", command=dlg.destroy).pack(pady=(0, pad))

    def _play_voice(self, person_id: str, person_name: str) -> None:
        from face_registry_client import FaceRegistryError, fetch_voice_audio_bytes

        if sys.platform != "win32":
            self._show_error("音声を確認", "Windows でのみ再生できます。")
            return
        self._cfg = load_config()
        try:
            raw = fetch_voice_audio_bytes(self._cfg, person_id)
        except FaceRegistryError as e:
            self._show_error("音声を確認", str(e))
            return
        path = None
        try:
            import winsound

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(raw)
                path = f.name
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            self._show_info("音声を確認", f"{person_name} の登録音声を再生しています。")
        except Exception as e:
            self._show_error("音声を確認", f"再生に失敗: {e}")
        finally:
            if path:
                try:
                    self.after(8000, lambda p=path: os.path.exists(p) and os.remove(p))
                except Exception:
                    pass

    def _delete_face(self, person_id: str, person_name: str) -> None:
        from tkinter import messagebox

        if not messagebox.askyesno("顔を削除", f"「{person_name}」の顔画像を削除しますか？", parent=self):
            return
        from face_registry_client import FaceRegistryError, delete_face

        self._cfg = load_config()
        try:
            delete_face(self._cfg, person_id)
        except FaceRegistryError as e:
            self._show_error("顔を削除", str(e))
            return
        self._show_info("顔を削除", f"{person_name} の顔画像を削除しました。")
        self._reload_list()

    def _delete_voice(self, person_id: str, person_name: str) -> None:
        from tkinter import messagebox

        if not messagebox.askyesno("音声を削除", f"「{person_name}」の音声サンプルを削除しますか？", parent=self):
            return
        from face_registry_client import FaceRegistryError, delete_voice

        self._cfg = load_config()
        try:
            delete_voice(self._cfg, person_id)
        except FaceRegistryError as e:
            self._show_error("音声を削除", str(e))
            return
        self._show_info("音声を削除", f"{person_name} の音声を削除しました。")
        self._reload_list()

    def _open_edit(self, person_id: str) -> None:
        person = next((x for x in self._persons if str(x.get("id")) == person_id), None)
        if not person:
            return
        dlg = ctk.CTkToplevel(self)
        dlg.title("社員情報を編集")
        dlg.geometry("440x460")
        dlg.minsize(440, 400)
        dlg.attributes("-topmost", True)
        pad = 12

        body = ctk.CTkFrame(dlg, fg_color="transparent")
        body.pack(fill="both", expand=True)
        scroll = ctk.CTkScrollableFrame(body, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=pad, pady=(pad, 0))

        def field(parent, label: str, initial: str = "") -> ctk.CTkEntry:
            ctk.CTkLabel(parent, text=label, anchor="w").pack(fill="x", pady=(6, 0))
            e = ctk.CTkEntry(parent)
            e.pack(fill="x", pady=(2, 0))
            e.insert(0, initial)
            return e

        e_name = field(scroll, "表示名", person.get("name") or "")
        e_email = field(scroll, "メール", person.get("email") or "")
        e_call = field(scroll, "呼び名", person.get("call_name") or "")
        e_kana = field(scroll, "呼び名の読み", person.get("call_name_kana") or "")
        e_dept = field(scroll, "部署", person.get("department") or "")
        staff_var = tk.BooleanVar(value=bool(person.get("is_staff", True)))
        ctk.CTkCheckBox(scroll, text="社員", variable=staff_var).pack(anchor="w", pady=(10, 0))

        def save() -> None:
            from face_registry_client import FaceRegistryError, update_person

            self._cfg = load_config()
            try:
                update_person(
                    self._cfg,
                    person_id,
                    name=e_name.get().strip(),
                    email=e_email.get().strip(),
                    call_name=e_call.get().strip(),
                    call_name_kana=e_kana.get().strip(),
                    department=e_dept.get().strip(),
                    is_staff=bool(staff_var.get()),
                )
            except FaceRegistryError as e:
                self._show_error("更新", str(e), parent=dlg)
                return
            dlg.destroy()
            self._show_info("更新", "社員情報を保存しました。")
            self._reload_list()

        footer = ctk.CTkFrame(dlg, fg_color="transparent")
        footer.pack(fill="x", padx=pad, pady=pad)
        ctk.CTkButton(footer, text="保存", width=100, command=save).pack(side="right")
        ctk.CTkButton(footer, text="キャンセル", width=100, command=dlg.destroy, fg_color="transparent", border_width=1).pack(
            side="right", padx=(0, 8)
        )

    def _on_add(self) -> None:
        from face_registry_client import FaceRegistryError, create_person

        name = self._new_name.get().strip()
        email = self._new_email.get().strip()
        if not name:
            self._show_error("追加", "表示名を入力してください。")
            return
        if not email or "@" not in email:
            self._show_error("追加", "有効なメールアドレスを入力してください。")
            return
        self._cfg = load_config()
        try:
            create_person(
                self._cfg,
                name=name,
                email=email,
                call_name=self._new_call.get().strip(),
                call_name_kana=self._new_kana.get().strip(),
                department=self._new_dept.get().strip(),
                is_staff=bool(self._new_staff.get()),
            )
        except FaceRegistryError as e:
            self._show_error("追加", str(e))
            return
        self._new_name.delete(0, "end")
        self._new_email.delete(0, "end")
        self._new_call.delete(0, "end")
        self._new_kana.delete(0, "end")
        self._new_dept.delete(0, "end")
        self._reload_list()

    def _on_delete(self, person_id: str, name: str) -> None:
        from tkinter import messagebox

        if not messagebox.askyesno("削除", f"「{name}」を削除しますか？", parent=self):
            return
        from face_registry_client import FaceRegistryError, delete_person

        self._cfg = load_config()
        try:
            delete_person(self._cfg, person_id)
        except FaceRegistryError as e:
            self._show_error("削除", str(e))
            return
        self._reload_list()

    def _on_workspace_sync(self) -> None:
        from face_registry_client import FaceRegistryError, workspace_directory_sync

        self._cfg = load_config()

        def work() -> None:
            try:
                result = workspace_directory_sync(self._cfg)
            except FaceRegistryError as e:
                self.after(0, lambda: self._show_error("Workspace 同期", str(e)))
                return
            if not result.get("ok"):
                err = result.get("error") or "不明なエラー"
                self.after(0, lambda: self._show_error("Workspace 同期", str(err)))
                return
            msg = (
                f"同期完了: 新規 {result.get('created', 0)} / "
                f"更新 {result.get('updated', 0)} / 対象 {result.get('total', 0)}"
            )
            self.after(0, lambda: self._show_info("Workspace 同期", msg))
            self.after(0, self._reload_list)

        threading.Thread(target=work, daemon=True).start()

    def _on_close(self) -> None:
        global _dialog_instance
        _dialog_instance = None
        try:
            self.destroy()
        except Exception:
            pass


def open_face_registry_admin_dialog(master=None, cfg: Optional[dict] = None) -> Optional[FaceRegistryAdminDialog]:
    """社員・顔の管理ダイアログを開く（シングルトン）。"""
    global _dialog_instance
    from face_registry_client import is_admin_configured
    from config_loader import is_feature_enabled, load_config

    if cfg is None:
        cfg = load_config()
    if not is_feature_enabled("face_registry_manage", cfg):
        from tkinter import messagebox

        if master is not None:
            messagebox.showinfo(
                "社員・顔の管理",
                "設定で「社員・顔の管理 (管理者)」を ON にしてください。",
                parent=master,
            )
        return None
    if not is_admin_configured(cfg):
        from tkinter import messagebox

        if master is not None:
            messagebox.showerror("社員・顔の管理", "linko_server_url が未設定です。", parent=master)
        return None
    if not (cfg.get("linko_admin_token") or "").strip():
        from tkinter import messagebox

        if master is not None:
            messagebox.showerror(
                "社員・顔の管理",
                "linko_admin_token が未設定です。管理者 PC の config.json に設定してください。",
                parent=master,
            )
        return None

    if _dialog_instance is not None:
        try:
            _dialog_instance.lift()
            _dialog_instance.focus_force()
            return _dialog_instance
        except Exception:
            _dialog_instance = None
    _dialog_instance = FaceRegistryAdminDialog(master=master, cfg=cfg)
    return _dialog_instance
