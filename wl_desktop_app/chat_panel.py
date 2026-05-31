# -*- coding: utf-8 -*-
"""リン子とのブレスト用チャットパネル (Phase 5a)。

アバタークリックで開く。board-system の /brainstorm (SSE streaming) に会話履歴を
送り、応答を 1 トークンずつ表示する。会話履歴はパネルを開いている間メモリ保持。

将来 (次段階): 各リン子発言の横に「📝 付箋にする」ボタンを足して、ブレスト内容を
付箋ボードへ投稿できるようにする (_send_content を流用)。
"""
from __future__ import annotations

import json
import threading
from typing import Optional

try:
    import customtkinter as ctk
except ImportError as e:
    print("customtkinter が見つかりません。", e)
    raise

try:
    import requests
except ImportError:
    requests = None

from config_loader import load_config

try:
    from app_log import log_info as _log
except Exception:
    def _log(msg: str) -> None:
        print(msg, flush=True)


_panel_instance: Optional["ChatPanel"] = None


def _brainstorm_url() -> str:
    """board-system の /brainstorm エンドポイント URL。
    board_system_url (例 https://.../api/bs) に /brainstorm を付ける。
    """
    cfg = load_config()
    base = (cfg.get("board_system_url") or "").strip().rstrip("/")
    if not base:
        # フォールバック: linko_server_url からは引けないので board の既定
        base = "https://wl-ai-board.internal.wonder-link.com/api/bs"
    return base + "/brainstorm"


class ChatPanel(ctk.CTkToplevel):
    WIDTH = 420
    HEIGHT = 560

    def __init__(self, master=None):
        super().__init__(master)
        self.title("リン子とブレスト")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(360, 420)
        self._messages: list[dict] = []  # [{role, content}]
        self._streaming = False
        self._assistant_start_index = None  # streaming 中のリン子発言の挿入位置
        self._last_assistant_text = ""  # 直近のリン子回答 (付箋投稿用)
        self._build_ui()
        self._position_near(master)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()
        # 開いた直後にあいさつ (LLM を使わず固定文)
        self._append_line("リン子", "こんにちは。何でも相談してくださいね。アイデア出しのお手伝いもしますよ。")

    def _position_near(self, master) -> None:
        """ミニポートの近くにパネルを配置する (カーソル移動を減らす)。
        既定はミニポートの左隣。画面外にはみ出る場合は右・上へ寄せる。
        """
        if master is None:
            return
        try:
            self.update_idletasks()
            master.update_idletasks()
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width() or 264
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            pw, ph = self.WIDTH, self.HEIGHT
            # まずミニポートの左隣
            x = mx - pw - 8
            if x < 0:
                # 左に入らなければ右隣
                x = mx + mw + 8
                if x + pw > sw:
                    # それも無理なら画面右端に寄せる
                    x = max(0, sw - pw - 8)
            # 縦はミニポートの下端に合わせる (パネル下端をミニポート下端付近に)
            y = my - ph + (master.winfo_height() or 224)
            if y < 0:
                y = 8
            if y + ph > sh:
                y = max(0, sh - ph - 8)
            self.geometry(f"{pw}x{ph}+{int(x)}+{int(y)}")
        except Exception:
            pass

    # --- UI ----------------------------------------------------------------
    def _build_ui(self) -> None:
        # 会話表示 (read-only textbox)
        self._chat = ctk.CTkTextbox(self, wrap="word", font=ctk.CTkFont(size=13))
        self._chat.pack(fill="both", expand=True, padx=10, pady=(10, 6))
        self._chat.configure(state="disabled")

        # 直前のリン子回答を付箋ボードへ投稿するボタン
        self._note_btn = ctk.CTkButton(
            self, text="📝 リン子の回答を付箋にする", height=32,
            command=self._on_make_note, state="disabled",
            fg_color=("#dcefdd", "#22692a"), hover_color=("#c8e6c9", "#2e7d32"),
            text_color=("#1b5e20", "#e8f5e9"),
        )
        self._note_btn.pack(fill="x", padx=10, pady=(0, 6))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        self._entry = ctk.CTkTextbox(bottom, height=60, wrap="word", font=ctk.CTkFont(size=13))
        self._entry.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._entry.bind("<Control-Return>", self._on_send_shortcut)
        self._send_btn = ctk.CTkButton(
            bottom, text="送信", width=64, command=self._on_send,
            fg_color=("#3d8b40", "#1b5e20"), hover_color=("#2f7a33", "#145214"),
        )
        self._send_btn.pack(side="right")

    # --- 送信 / streaming --------------------------------------------------
    def _on_send_shortcut(self, event=None):
        self._on_send()
        return "break"

    def _on_send(self) -> None:
        if self._streaming:
            return
        text = self._entry.get("1.0", "end").strip()
        if not text:
            return
        if requests is None:
            self._append_line("システム", "requests が利用できないため送信できません。")
            return
        self._entry.delete("1.0", "end")
        self._append_line("あなた", text)
        self._messages.append({"role": "user", "content": text})
        self._send_btn.configure(state="disabled")
        threading.Thread(target=self._stream_response, daemon=True).start()

    def _stream_response(self) -> None:
        self._streaming = True
        url = _brainstorm_url()
        # リン子の発言枠を開始 (口パクは最初のトークンが来てから = 実際に喋り出すタイミング)
        self.after(0, self._begin_assistant)
        lipsync_started = False

        def _start_lipsync_once():
            try:
                import linko_avatar
                if linko_avatar.is_ready():
                    linko_avatar.start_lipsync(duration_sec=None, base_pose="normal")
            except Exception:
                pass

        acc = ""
        try:
            with requests.post(
                url, json={"messages": self._messages}, stream=True, timeout=(10, 120)
            ) as r:
                if r.status_code != 200:
                    self.after(0, lambda: self._append_assistant_token(f"[エラー: HTTP {r.status_code}]"))
                else:
                    for line in r.iter_lines(decode_unicode=True):
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                        except Exception:
                            continue
                        if obj.get("error"):
                            self.after(0, lambda m=obj["error"]: self._append_assistant_token(f"[エラー: {m}]"))
                            continue
                        tok = obj.get("token")
                        if tok:
                            if not lipsync_started:
                                lipsync_started = True
                                _start_lipsync_once()  # 最初のトークンで口パク開始
                            acc += tok
                            self.after(0, lambda t=tok: self._append_assistant_token(t))
        except Exception as e:
            _log(f"[chat_panel] streaming エラー: {e}")
            self.after(0, lambda: self._append_assistant_token(f"[エラー: {str(e)[:80]}]"))
        finally:
            self._messages.append({"role": "assistant", "content": acc})
            self._last_assistant_text = acc
            self._streaming = False
            self.after(0, self._end_assistant)
            try:
                import linko_avatar
                if linko_avatar.is_ready():
                    linko_avatar.stop_lipsync(base_pose="normal")
            except Exception:
                pass

    # --- テキスト表示ヘルパ (すべてメインスレッドで) ------------------------
    def _append_line(self, speaker: str, text: str) -> None:
        self._chat.configure(state="normal")
        if self._chat.get("1.0", "end").strip():
            self._chat.insert("end", "\n\n")
        self._chat.insert("end", f"{speaker}: {text}")
        self._chat.see("end")
        self._chat.configure(state="disabled")

    def _begin_assistant(self) -> None:
        self._chat.configure(state="normal")
        if self._chat.get("1.0", "end").strip():
            self._chat.insert("end", "\n\n")
        self._chat.insert("end", "リン子: ")
        self._chat.see("end")
        self._chat.configure(state="disabled")

    def _append_assistant_token(self, token: str) -> None:
        self._chat.configure(state="normal")
        self._chat.insert("end", token)
        self._chat.see("end")
        self._chat.configure(state="disabled")

    def _end_assistant(self) -> None:
        try:
            self._send_btn.configure(state="normal")
            if (self._last_assistant_text or "").strip():
                self._note_btn.configure(state="normal")
        except Exception:
            pass

    def _on_make_note(self) -> None:
        """直前のリン子の回答を付箋ボードへ投稿する。既存の _send_content を流用。"""
        text = (self._last_assistant_text or "").strip()
        if not text:
            return
        self._note_btn.configure(state="disabled", text="📝 投稿中…")

        def do_post():
            ok, msg = (False, "送信処理が見つかりません")
            try:
                from mini_port import _send_content  # 遅延 import (循環回避)
                ok, msg = _send_content(text)
            except Exception as e:
                ok, msg = False, str(e)[:80]
            self.after(0, lambda: self._on_note_done(ok, msg))

        threading.Thread(target=do_post, daemon=True).start()

    def _on_note_done(self, ok: bool, msg: str) -> None:
        self._append_line("システム", "付箋に投稿しました。" if ok else f"付箋投稿に失敗: {msg}")
        try:
            self._note_btn.configure(
                state="normal", text="📝 リン子の回答を付箋にする"
            )
        except Exception:
            pass

    def _on_close(self) -> None:
        global _panel_instance
        _panel_instance = None
        try:
            import linko_avatar
            linko_avatar.stop_lipsync(base_pose="normal")
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


def open_chat_panel(master=None) -> ChatPanel:
    """チャットパネルを開く (シングルトン)。既に開いていれば前面化。"""
    global _panel_instance
    if _panel_instance is not None:
        try:
            _panel_instance.lift()
            _panel_instance.focus_force()
            return _panel_instance
        except Exception:
            _panel_instance = None
    _panel_instance = ChatPanel(master=master)
    return _panel_instance
