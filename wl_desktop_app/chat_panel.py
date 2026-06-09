# -*- coding: utf-8 -*-
"""リン子とのブレスト用チャットパネル (Phase 5a)。

アバタークリックで開く。board-system の /brainstorm (SSE streaming) に会話履歴を
送り、応答を 1 トークンずつ表示する。会話履歴はパネルを開いている間メモリ保持。

将来 (次段階): 各リン子発言の横に「📝 付箋にする」ボタンを足して、ブレスト内容を
付箋ボードへ投稿できるようにする (_send_content を流用)。
"""
from __future__ import annotations

import json
import queue
import re
import threading
from typing import Optional

# 絵文字・絵記号 (音声合成に渡すと無音スタブ→リトライで時間を浪費するため除去)
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U0001F1E6-\U0001F1FF"
    "\U00002600-\U000027BF\U00002B00-\U00002BFF\U0000FE00-\U0000FE0F]+"
)
# 発話可能な文字 (英数・ひらがな・カタカナ・漢字・半角カナ)。1つも無ければ読み上げない。
_SPEAKABLE_RE = re.compile(
    "[0-9A-Za-z぀-ゟ゠-ヿ㐀-鿿ｦ-ﾟ]"
)


def _clean_for_tts(text: str) -> str:
    """TTS へ渡す前に絵文字を除去し、空白を整える。発話可能文字が無ければ空文字を返す。"""
    cleaned = _EMOJI_RE.sub("", text).strip()
    if not _SPEAKABLE_RE.search(cleaned):
        return ""
    return cleaned

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


def _tts_url() -> Optional[str]:
    """linko-system の TTS エンドポイント URL。
    linko_server_url (例 https://linko-board.internal.wonder-link.com) に /api/v2/tts を付ける。
    linko_server_url 未設定なら None (= 音声なし)。
    """
    cfg = load_config()
    base = (cfg.get("linko_server_url") or "").strip().rstrip("/")
    if not base:
        return None
    return base + "/api/v2/tts"


class ChatPanel(ctk.CTkToplevel):
    WIDTH = 420
    HEIGHT = 560
    _GAP = 8

    @staticmethod
    def _rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2) -> bool:
        return not (x1 + w1 <= x2 or x1 >= x2 + w2 or y1 + h1 <= y2 or y1 >= y2 + h2)

    def __init__(self, master=None):
        super().__init__(master)
        self.title("リン子とブレスト")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(360, 420)
        self._messages: list[dict] = []  # [{role, content}]
        self._streaming = False
        self._assistant_start_index = None  # streaming 中のリン子発言の挿入位置
        self._last_assistant_text = ""  # 直近のリン子回答 (付箋投稿用)
        self._pending_attachment = None  # {"name": str, "text": str} 添付資料 (次の送信に同梱)
        # 文単位ストリーミング TTS のパイプライン (voice 有効時のみ遅延起動)
        self._sentence_q: "queue.Queue[Optional[str]]" = queue.Queue()
        self._audio_q: "queue.Queue" = queue.Queue(maxsize=6)
        self._tts_workers_started = False
        self._tts_cancel = threading.Event()
        self._build_ui()
        self._position_near(master)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()
        # 開いた直後にあいさつ (LLM を使わず固定文)
        self._append_line("リン子", "こんにちは。何でも相談してくださいね。アイデア出しのお手伝いもしますよ。")

    def _position_near(self, master) -> None:
        """ミニポートと重ならない位置にパネルを置く。

        優先: ミニポートの真上（右端揃え）。上に入らなければ下、それでも無理なら左。
        """
        if master is None:
            return
        try:
            self.update_idletasks()
            master.update_idletasks()
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width() or 264
            mh = master.winfo_height() or 224
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            pw, ph = self.WIDTH, self.HEIGHT
            gap = self._GAP

            def clamp_x(x: int) -> int:
                return max(0, min(int(x), max(0, sw - pw - gap)))

            def clamp_y(y: int) -> int:
                return max(0, min(int(y), max(0, sh - ph - gap)))

            def fits(x: int, y: int) -> bool:
                return (
                    x >= 0 and y >= 0 and x + pw <= sw and y + ph <= sh
                    and not self._rects_overlap(x, y, pw, ph, mx, my, mw, mh)
                )

            candidates = [
                (mx + mw - pw, my - ph - gap),          # 上・右端揃え
                (mx, my - ph - gap),                     # 上・左端揃え
                (mx + mw - pw, my + mh + gap),           # 下・右端揃え
                (mx, my + mh + gap),                     # 下・左端揃え
                (mx - pw - gap, my),                     # 左・上揃え
                (mx - pw - gap, my + mh - ph),           # 左・下揃え
                (mx + mw + gap, my),                     # 右・上揃え
            ]

            x, y = candidates[0]
            for cx, cy in candidates:
                cx, cy = clamp_x(cx), clamp_y(cy)
                if fits(cx, cy):
                    x, y = cx, cy
                    break
            else:
                x, y = clamp_x(mx + mw - pw), clamp_y(my - ph - gap)

            self.geometry(f"{pw}x{ph}+{x}+{y}")
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

        # 添付資料の状態表示 + 添付ボタン (社内 LLM だけに渡る。外部送信なし)
        attach_row = ctk.CTkFrame(self, fg_color="transparent")
        attach_row.pack(fill="x", padx=10, pady=(0, 6))
        self._attach_label = ctk.CTkLabel(
            attach_row, text="📎 添付なし", anchor="w",
            text_color=("gray40", "gray60"), font=ctk.CTkFont(size=12),
        )
        self._attach_label.pack(side="left", fill="x", expand=True)
        self._attach_btn = ctk.CTkButton(
            attach_row, text="📎 資料を添付", width=110, height=28,
            command=self._on_attach,
            fg_color=("#dcefdd", "#22692a"), hover_color=("#c8e6c9", "#2e7d32"),
            text_color=("#1b5e20", "#e8f5e9"),
        )
        self._attach_btn.pack(side="right")

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

    # 添付資料は context window に収まるよう上限を設ける (超過分は末尾カット)
    MAX_ATTACH_CHARS = 12000

    def _on_attach(self) -> None:
        """ローカルファイルを選んでテキスト抽出し、次の送信に同梱する。
        抽出は端末内で行い、テキストは社内 LLM (board-system→Ollama) にのみ渡る。外部送信なし。
        """
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="リン子に読ませる資料を選択",
            filetypes=[
                ("対応ファイル", "*.txt *.md *.csv *.json *.log *.py *.pdf *.docx"),
                ("すべて", "*.*"),
            ],
        )
        if not path:
            return
        import os
        name = os.path.basename(path)
        text, err = _extract_text(path)
        if err:
            self._append_line("システム", f"資料の読み込みに失敗: {err}")
            return
        if not (text or "").strip():
            self._append_line("システム", "資料からテキストを抽出できませんでした (画像 PDF など)。")
            return
        truncated = False
        if len(text) > self.MAX_ATTACH_CHARS:
            text = text[: self.MAX_ATTACH_CHARS]
            truncated = True
        self._pending_attachment = {"name": name, "text": text}
        label = f"📎 {name} ({len(text)}字{'・以降省略' if truncated else ''})"
        self._attach_label.configure(text=label)
        self._append_line("システム", f"資料「{name}」を添付しました。質問を入力して送信してください。")

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

        # 添付資料があれば、LLM に渡す content の先頭に資料を前置 (表示はユーザ入力のみ)
        attach = self._pending_attachment
        if attach:
            llm_content = (
                f"【添付資料: {attach['name']}】\n{attach['text']}\n\n"
                f"【質問・指示】\n{text}"
            )
            self._append_line("あなた", f"[📎 {attach['name']}] {text}")
            self._pending_attachment = None
            self._attach_label.configure(text="📎 添付なし")
        else:
            llm_content = text
            self._append_line("あなた", text)

        self._messages.append({"role": "user", "content": llm_content})
        self._send_btn.configure(state="disabled")
        threading.Thread(target=self._stream_response, daemon=True).start()

    def _stream_response(self) -> None:
        self._streaming = True
        url = _brainstorm_url()
        # 音声予定の判定: features.brainstorm_voice 有効 かつ linko_server_url 設定済み
        # → True なら口パクは音声再生側 (play_linko_audio→say) に委ね、テキスト中は動かさない。
        #   False なら従来どおり最初のトークンでテキスト中の口パクを開始する (無音時の見栄え)。
        try:
            from config_loader import is_feature_enabled
            voice_planned = bool(is_feature_enabled("brainstorm_voice")) and bool(_tts_url())
        except Exception:
            voice_planned = False
        if voice_planned:
            self._ensure_tts_workers()
        # リン子の発言枠を開始 (口パクは最初のトークンが来てから = 実際に喋り出すタイミング)
        self.after(0, self._begin_assistant)
        lipsync_started = False
        sentence_buf = ""  # voice 時: 文区切りまでの未確定テキスト

        def _start_lipsync_once():
            try:
                import linko_avatar
                if linko_avatar.is_ready():
                    linko_avatar.start_lipsync(duration_sec=None, base_pose="normal")
            except Exception:
                pass

        acc = ""
        try:
            from security import assert_http_url
            assert_http_url(url, load_config(), purpose="brainstorm")
        except ValueError as e:
            self.after(0, lambda: self._append_assistant_token(f"[エラー: {str(e)[:80]}]"))
            self._messages.append({"role": "assistant", "content": ""})
            self._streaming = False
            self.after(0, self._end_assistant)
            return
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
                                if not voice_planned:
                                    _start_lipsync_once()  # 無音時のみテキスト中に口パク
                            acc += tok
                            self.after(0, lambda t=tok: self._append_assistant_token(t))
                            if voice_planned:
                                # 文が完成するたびに TTS パイプラインへ投入 (低レイテンシ)
                                sentence_buf = self._flush_sentences(sentence_buf + tok)
        except Exception as e:
            _log(f"[chat_panel] streaming エラー: {e}")
            self.after(0, lambda: self._append_assistant_token(f"[エラー: {str(e)[:80]}]"))
        finally:
            self._messages.append({"role": "assistant", "content": acc})
            self._last_assistant_text = acc
            self._streaming = False
            self.after(0, self._end_assistant)
            if not voice_planned:
                # テキスト中に動かした口パクを停止 (音声予定時は say() 側が制御)
                try:
                    import linko_avatar
                    if linko_avatar.is_ready():
                        linko_avatar.stop_lipsync(base_pose="normal")
                except Exception:
                    pass
            else:
                # 末尾の未確定テキスト (句点で終わらない最後の一文) を投入
                tail = _clean_for_tts(sentence_buf)
                if tail:
                    self._sentence_q.put(tail)

    # --- 文単位ストリーミング TTS -----------------------------------------
    _SENTENCE_ENDERS = "。．！？!?\n"

    def _flush_sentences(self, buf: str) -> str:
        """buf から完成した文 (句点等で終わる) を取り出し TTS キューへ。未確定の末尾を返す。
        絵文字・記号だけの断片は読み上げない (SoVITS の無音スタブ→リトライを避ける)。"""
        start = 0
        for i, ch in enumerate(buf):
            if ch in self._SENTENCE_ENDERS:
                seg = _clean_for_tts(buf[start:i + 1])
                if seg:
                    self._sentence_q.put(seg)
                start = i + 1
        return buf[start:]

    def _ensure_tts_workers(self) -> None:
        """fetch (TTS 生成) と play (順次再生) のワーカースレッドを一度だけ起動。"""
        if self._tts_workers_started:
            return
        self._tts_workers_started = True
        threading.Thread(target=self._tts_fetch_worker, daemon=True).start()
        threading.Thread(target=self._tts_play_worker, daemon=True).start()

    def _tts_fetch_worker(self) -> None:
        """文を 1 つずつ取り出し TTS 合成 + DL して audio_q へ (再生と並行して先読み)。"""
        while True:
            sentence = self._sentence_q.get()
            if sentence is None or self._tts_cancel.is_set():
                break
            item = self._fetch_sentence_audio(sentence)
            if item:
                self._audio_q.put(item)
        self._audio_q.put(None)  # play worker へ終了通知

    def _tts_play_worker(self) -> None:
        """audio_q の WAV を順番にブロッキング再生 (文同士が重ならない)。"""
        from audio_player import play_wav
        while True:
            item = self._audio_q.get()
            if item is None or self._tts_cancel.is_set():
                break
            path, text, duration = item
            try:
                play_wav(path, text=text, duration_sec=duration, blocking=True,
                         log_prefix="[chat_panel]")
            except Exception as e:
                _log(f"[chat_panel] 文音声 再生失敗: {e}")

    def _fetch_sentence_audio(self, text: str):
        """1 文を linko-system の TTS で合成し WAV をローカル DL。(path, text, duration) を返す。"""
        if requests is None or not text.strip():
            return None
        url = _tts_url()
        if not url:
            return None
        try:
            from security import assert_http_url
            assert_http_url(url, load_config(), purpose="brainstorm_tts")
        except ValueError as e:
            _log(f"[chat_panel] TTS URL 拒否: {e}")
            return None
        try:
            r = requests.post(url, json={"text": text}, timeout=(5, 60))
            if r.status_code == 503:
                # 受付保護の同時実行上限 or 一時的に合成不可。音声だけスキップ(テキストは残る)
                _log("[chat_panel] TTS 混雑のため音声スキップ (503)")
                return None
            if r.status_code != 200:
                _log(f"[chat_panel] TTS HTTP {r.status_code}")
                return None
            audio_url = (r.json() or {}).get("audio_url")
        except Exception as e:
            _log(f"[chat_panel] TTS 取得失敗: {e}")
            return None
        if not audio_url:
            return None
        try:
            from audio_player import download_linko_wav
            res = download_linko_wav(audio_url, log_prefix="[chat_panel]")
        except Exception as e:
            _log(f"[chat_panel] 音声DL失敗: {e}")
            return None
        if not res:
            return None
        path, duration = res
        return (path, text, duration)

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
        # TTS パイプラインを停止 (ワーカーをアンブロックして終了させる)
        self._tts_cancel.set()
        try:
            self._sentence_q.put_nowait(None)
        except Exception:
            pass
        try:
            self._audio_q.put_nowait(None)
        except Exception:
            pass
        try:
            import linko_avatar
            linko_avatar.stop_lipsync(base_pose="normal")
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


def _extract_text(path: str):
    """ローカルファイルからテキストを抽出する。戻り値: (text, error_message)。
    txt/md 系は標準で常に対応。pdf は pypdf、docx は python-docx (無ければエラー文)。
    すべて端末内処理 (外部送信なし)。
    """
    import os
    ext = os.path.splitext(path)[1].lower()
    text_exts = (".txt", ".md", ".csv", ".json", ".log", ".py", ".ini", ".yaml", ".yml", ".html", ".xml")
    try:
        if ext in text_exts or ext == "":
            for enc in ("utf-8", "utf-8-sig", "cp932"):
                try:
                    with open(path, "r", encoding=enc) as f:
                        return f.read(), None
                except UnicodeDecodeError:
                    continue
            return None, "文字コードを判別できませんでした"
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError:
                return None, "PDF 対応ライブラリ (pypdf) が無い環境です"
            reader = PdfReader(path)
            parts = []
            for page in reader.pages:
                try:
                    parts.append(page.extract_text() or "")
                except Exception:
                    continue
            return "\n".join(parts), None
        if ext == ".docx":
            try:
                import docx
            except ImportError:
                return None, "Word 対応ライブラリ (python-docx) が無い環境です"
            d = docx.Document(path)
            return "\n".join(p.text for p in d.paragraphs), None
        return None, f"未対応の形式です ({ext})"
    except Exception as e:
        return None, str(e)[:100]


def open_chat_panel(master=None) -> ChatPanel:
    """チャットパネルを開く (シングルトン)。既に開いていれば前面化。"""
    global _panel_instance
    if _panel_instance is not None:
        try:
            _panel_instance._position_near(master)
            _panel_instance.lift()
            _panel_instance.focus_force()
            return _panel_instance
        except Exception:
            _panel_instance = None
    _panel_instance = ChatPanel(master=master)
    return _panel_instance


def open_chat_panel_with_task(
    master=None,
    task_title: str = "",
    note_id: Optional[int] = None,
) -> ChatPanel:
    """タスクリマインドの「相談」から開く。タスク文脈を入れて自動送信する。"""
    panel = open_chat_panel(master=master)
    title = (task_title or "（無題）").strip()
    ctx = (
        f"Today のタスクについて相談したいです。\n"
        f"タスク: 『{title}』\n"
        f"進め方・優先度・次の一歩を一緒に整理してください。"
    )
    if note_id is not None:
        ctx += f"\n（Board note_id={note_id}）"
    try:
        panel._entry.delete("1.0", "end")
        panel._entry.insert("1.0", ctx)
        panel.after(300, panel._on_send)
    except Exception as e:
        _log(f"[chat_panel] task consult setup failed: {e}")
    return panel
