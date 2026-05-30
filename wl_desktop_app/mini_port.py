# -*- coding: utf-8 -*-
"""
Rinko Mini-Port: 常駐型フローティング入力ウィンドウ。
通常時はリン子ボタンと投稿ボタンのみ。「投稿」クリックで入力欄を表示し、送信ボタンで POST /sticky_notes に送信。
"""
from __future__ import annotations

import os
import re
import sys
import threading
import time
import webbrowser
from typing import Tuple

try:
    import requests
    import customtkinter as ctk
except ImportError as e:
    print("必要なパッケージがありません。以下を実行してください:")
    print("  pip install -r requirements.txt")
    print("エラー:", e)
    sys.exit(1)

from config_loader import load_config, save_config, get_board_system_personal_url, get_effective_board_system_url, get_app_base_dir
from theme import Theme, apply_window_transparency

# 画像表示用（PIL が無い環境ではリン子はテキストボタンのみ）
# CTkImage は内部で PIL.Image と PIL.ImageTk を参照するため、先に両方 import する
try:
    import PIL.Image  # noqa: F401
    import PIL.ImageTk  # noqa: F401
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# ホットキー用（別スレッドで動作）
try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False


def _sticky_note_api_url():
    """付箋ボードの REST API URL（POST /api/sticky_notes）。board URL から導出。"""
    cfg = load_config()
    board_url = (cfg.get("mini_port_api_url") or "https://wl-ai-board.internal.wonder-link.com/board/wl").rstrip("/")
    # https://wl-ai-board.../board/wl → https://wl-ai-board.../api/sticky_notes
    base = re.sub(r"/board/.*$", "", board_url).rstrip("/")
    return f"{base}/api/sticky_notes"


def _board_id():
    """送信先ボード ID（例: wl）。"""
    cfg = load_config()
    return (cfg.get("postit_board_id") or "wl").strip() or "wl"


def _taskboard_url():
    """ミニウィンドウのリン子クリックで開く Task ボードの URL。"""
    cfg = load_config()
    return (cfg.get("mini_port_taskboard_url") or "https://wl-ai-board.internal.wonder-link.com/boards/taskboard").strip()


def _prompt_email_and_resolve_personal(parent=None):
    """メール入力ダイアログを表示し、Board System API で user_id を解決して config に保存。成功時はパーソナルURLを返す。
    parent: ダイアログの親ウィンドウ（MiniPortWindow 等）。None のときは新規 Tk() を作成。"""
    from dialog_utils import ask_string_large
    cfg = load_config()
    board_url = get_effective_board_system_url(cfg)
    if not board_url:
        return None
    email = ask_string_large(
        "Wonder Linko - パーソナルボード",
        "各自のパーソナルボードを開くため、登録済みのメールアドレスを入力してください:",
        parent=parent,
    )
    if not email or not isinstance(email, str) or "@" not in email:
        return None
    email = email.strip()
    try:
        r = requests.get(f"{board_url}/users/by_email", params={"email": email}, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        user_id = data.get("id")
        if user_id is None:
            return None
        cfg["board_system_url"] = board_url
        cfg["board_system_personal_id"] = str(user_id)
        cfg["user_id"] = str(user_id)
        if (data.get("call_name") or data.get("name") or "").strip():
            cfg["display_name"] = (data.get("call_name") or data.get("name") or "").strip()
        save_config(cfg)
        return get_board_system_personal_url(cfg)
    except Exception:
        return None


def _send_content(text: str) -> Tuple[bool, str]:
    """付箋ボード API (POST /api/sticky_notes) に boardId + note 形式で送信。"""
    text = (text or "").strip()
    if not text:
        return False, "入力が空です"
    url = _sticky_note_api_url()
    board_id = _board_id()
    cfg = load_config()
    author = (cfg.get("display_name") or "").strip() or "Mini-Port"
    note_id = f"miniport-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
    note = {
        "id": note_id,
        "text": text,
        "x": 100,
        "y": 100,
        "color": "#fff59d",
        "pinned": False,
        "author": author,
        "createdAt": int(time.time() * 1000),
    }
    try:
        r = requests.post(url, json={"boardId": board_id, "note": note}, timeout=10)
        if r.status_code in (200, 201):
            return True, "送信しました"
        try:
            body = (r.text or "")[:120].strip()
            detail = f" {body}" if body else ""
        except Exception:
            detail = ""
        return False, f"エラー: {r.status_code}{detail}"
    except requests.exceptions.RequestException as e:
        return False, f"接続エラー: {str(e)[:80]}"


def _rinko_icon_path() -> str:
    base = get_app_base_dir()
    for candidate in (
        os.path.join(base, "assets", "toast_icon.png"),
        os.path.join(base, "toast_icon.png"),
    ):
        if os.path.isfile(candidate):
            return os.path.normpath(os.path.abspath(candidate))
    return os.path.normpath(os.path.abspath(os.path.join(base, "assets", "toast_icon.png")))


class MiniPortWindow(ctk.CTk):
    # 通常時サイズ。features.linko_avatar=True なら _init_avatar() 内で
    # 240x140 に拡大 (128px アバター + 縦並び 2 ボタン)。
    COMPACT_W = 180
    COMPACT_H = 56
    # 入力表示時サイズ
    EXPANDED_W = 360
    EXPANDED_H = 200

    def __init__(self, on_hide=None, on_notifications_toggle=None, get_notifications_enabled=None):
        super().__init__()
        self._on_hide = on_hide if callable(on_hide) else None
        self._on_notifications_toggle = on_notifications_toggle if callable(on_notifications_toggle) else None
        self._get_notifications_enabled = get_notifications_enabled if callable(get_notifications_enabled) else (lambda: True)
        self._feedback_job = None
        self._input_visible = False
        self._placeholder_visible = False
        self._drag_win_x = 0
        self._drag_win_y = 0
        self._last_compact_x = 0
        self._last_compact_y = 0
        self._configure_window()
        self._build_ui()
        self._setup_context_menu()
        self._position_bottom_right(compact=True)
        if HAS_PYNPUT:
            self._start_hotkey_listener()
        else:
            print("Rinko Mini-Port: pynput が未インストールです。pip install pynput で Ctrl+Shift+Space が有効になります。")

    # プレースホルダー用（CTkTextbox は placeholder 非対応のため自前で表示）
    PLACEHOLDER_TEXT = "付箋を投稿するコメントを入力"

    def _configure_window(self):
        self.title("Rinko Mini-Port")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        # 外枠の長方形を消すため、Windows では transparentcolor で角丸フレームだけを
        # 見せる。非 Windows は transparentcolor 非対応 (黒い四角が残る) のため、
        # ウィンドウ背景をサーフェス色にして角丸の外を馴染ませる。
        # いずれも -alpha で枠ごと軽く透過し、作業の邪魔になりにくくする。
        self._transparent_key = apply_window_transparency(self, fg_fallback=Theme.SURFACE)

    def _build_ui(self):
        # 角丸フレームのみを見せる (外側の長方形は Toplevel の transparentcolor で透過)。
        self.frame = ctk.CTkFrame(
            self,
            corner_radius=Theme.RADIUS_CARD,
            border_width=2,
            border_color=Theme.SURFACE_BORDER,
            fg_color=Theme.SURFACE,
        )
        self.frame.pack(fill="both", expand=True, padx=0, pady=0)

        # features.linko_avatar の値でレイアウトを分岐
        try:
            from config_loader import is_feature_enabled
            avatar_on = is_feature_enabled("linko_avatar")
        except Exception:
            avatar_on = False
        self._avatar_on = avatar_on

        # --- 通常時フレーム ---
        self.compact_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.compact_frame.pack(fill="both", expand=True, padx=8, pady=6)

        self._rinko_image = None  # 参照保持 (GC 防止)
        icon_path = _rinko_icon_path()
        use_icon = _HAS_PIL and os.path.isfile(icon_path)

        if avatar_on:
            # マスコット案: アバターを主役にカード上部へ大きく配置し、
            # その下に「投稿 (主) / ボード (副)」を横並びのピルで置く。
            self.COMPACT_W = 264
            self.COMPACT_H = 224
            avatar_size = 140
            self._avatar_size = (avatar_size, avatar_size)
            if use_icon:
                try:
                    self._rinko_image = ctk.CTkImage(
                        light_image=icon_path, dark_image=icon_path,
                        size=(avatar_size, avatar_size),
                    )
                except Exception:
                    use_icon = False
            # アバターは CTkLabel: クリック (吹き出し) とドラッグ (移動) を自前で両立。
            # 画像があるときは text を必ず空に (画像とテキストの重なり防止)。
            self.btn_rinko = ctk.CTkLabel(
                self.compact_frame,
                text="" if use_icon else "📷",
                image=self._rinko_image if use_icon else None,
                width=avatar_size,
                height=avatar_size,
            )
            self.btn_rinko.pack(side="top", pady=(2, 8))
            self._bind_avatar_click_drag(self.btn_rinko)

            # アバター下のボタン列 (横並び)。投稿=主アクション、ボード=副。
            self._button_frame = ctk.CTkFrame(self.compact_frame, fg_color="transparent")
            self._button_frame.pack(side="top", fill="x")
            self.btn_post = ctk.CTkButton(
                self._button_frame, text="📝 投稿", width=116, height=40,
                corner_radius=Theme.RADIUS_PILL, font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                text_color=Theme.PRIMARY_TEXT,
                command=self._show_input,
            )
            self.btn_post.pack(side="left", expand=True, fill="x", padx=(0, 5))
            self.btn_board = ctk.CTkButton(
                self._button_frame, text="📋 ボード", width=116, height=40,
                corner_radius=Theme.RADIUS_PILL, font=ctk.CTkFont(size=14),
                fg_color=Theme.SECONDARY, hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.SECONDARY_TEXT,
                border_width=1, border_color=Theme.SECONDARY_BORDER,
                command=self._open_taskboard,
            )
            self.btn_board.pack(side="left", expand=True, fill="x", padx=(5, 0))
        else:
            # 従来の軽量レイアウト (アイコン丸ボタン + 投稿)
            self.COMPACT_W = 180
            self.COMPACT_H = 56
            if use_icon:
                try:
                    self._rinko_image = ctk.CTkImage(
                        light_image=icon_path, dark_image=icon_path, size=(36, 36),
                    )
                    self.btn_rinko = ctk.CTkButton(
                        self.compact_frame, image=self._rinko_image, text="",
                        width=44, height=40, corner_radius=22,
                        fg_color=Theme.SECONDARY, hover_color=Theme.SECONDARY_HOVER,
                        command=self._open_taskboard,
                    )
                except Exception:
                    use_icon = False
            if not use_icon:
                self.btn_rinko = ctk.CTkButton(
                    self.compact_frame, text="ボード", width=56, height=40,
                    corner_radius=20, font=ctk.CTkFont(size=13),
                    fg_color=Theme.SECONDARY, hover_color=Theme.SECONDARY_HOVER,
                    text_color=Theme.SECONDARY_TEXT,
                    command=self._open_taskboard,
                )
            self.btn_rinko.pack(side="left", padx=(0, 8))
            self.btn_post = ctk.CTkButton(
                self.compact_frame, text="投稿", width=70, height=40,
                corner_radius=20, font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                text_color=Theme.PRIMARY_TEXT,
                command=self._show_input,
            )
            self.btn_post.pack(side="left")

        # Phase 2: アバター有効時の lipsync / 吹き出しを初期化
        self._init_avatar()

        # --- 入力表示時: テキストエリア + 閉じる + 送信 ---
        self.input_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        # 3行表示・スクロール・改行可（プレースホルダーは FocusIn/FocusOut で制御）
        self.textbox = ctk.CTkTextbox(
            self.input_frame,
            width=320,
            height=72,
            font=ctk.CTkFont(size=14),
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            wrap="word",
            fg_color=Theme.INPUT_FG,
            border_color=Theme.INPUT_BORDER,
        )
        self.textbox.pack(pady=(0, 6), fill="x")
        self.textbox.bind("<Control-Return>", self._on_send_shortcut)
        self.textbox.bind("<Escape>", lambda e: self._hide_input())
        self.textbox.bind("<FocusIn>", self._on_textbox_focus_in)
        self.textbox.bind("<FocusOut>", self._on_textbox_focus_out)
        self.textbox.bind("<KeyPress>", self._on_textbox_key, add="+")

        send_f = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        send_f.pack(fill="x")
        self.label_feedback = ctk.CTkLabel(
            send_f,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=Theme.FEEDBACK_INFO,
        )
        self.label_feedback.pack(side="left", padx=(0, 8))
        self.btn_close = ctk.CTkButton(
            send_f,
            text="閉じる",
            width=70,
            height=32,
            corner_radius=16,
            font=ctk.CTkFont(size=13),
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            border_width=1,
            border_color=Theme.SECONDARY_BORDER,
            command=self._hide_input,
        )
        self.btn_close.pack(side="right", padx=(0, 6))
        self.btn_send = ctk.CTkButton(
            send_f,
            text="送信",
            width=80,
            height=32,
            corner_radius=16,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color=Theme.PRIMARY_TEXT,
            command=self._on_send,
        )
        self.btn_send.pack(side="right")

        self._setup_drag()
        # 質感用の背景画像 (assets/card_bg.png) があれば角丸カードに敷く。
        # 無ければ単色サーフェスのまま (安全フォールバック)。マスコット表示時のみ。
        self._apply_card_background()

    def _apply_card_background(self) -> None:
        """assets/card_bg.png があればマスコットカードの背景に敷いて質感を上げる。

        - PNG は角丸 + 淡いグラデ + 柔らかい影込みで事前生成する (assets/build_card_bg.py)。
        - 画像が無い / PIL が無い / マスコット表示でない場合は何もしない (単色サーフェスのまま)。
        - 失敗してもアプリは従来通り動くよう、すべて best-effort。
        """
        self._card_bg_image = None
        self._card_bg_label = None
        try:
            if not getattr(self, "_avatar_on", False) or not _HAS_PIL:
                return
            assets_dir = os.path.join(get_app_base_dir(), "assets")
            light_path = os.path.join(assets_dir, "card_bg.png")
            dark_path = os.path.join(assets_dir, "card_bg_dark.png")
            if not os.path.isfile(light_path):
                return
            import PIL.Image
            light_src = PIL.Image.open(light_path).convert("RGBA")
            dark_src = PIL.Image.open(dark_path).convert("RGBA") if os.path.isfile(dark_path) else light_src
            w, h = int(self.COMPACT_W), int(self.COMPACT_H)
            self._card_bg_image = ctk.CTkImage(light_image=light_src, dark_image=dark_src, size=(w, h))
            # 角丸グラデ PNG をカード上部 (マスコット表示領域) に最背面で敷く。
            # PNG の角丸半径はフレームの border 半径と揃えてあるので、縁は二重にならず
            # きれいに重なる。コンテンツ (compact_frame / input_frame) は上に描かれる。
            self._card_bg_label = ctk.CTkLabel(self.frame, text="", image=self._card_bg_image)
            self._card_bg_label.place(x=0, y=0, anchor="nw")
            self._card_bg_label.lower()
        except Exception as e:
            print(f"[mini_port] card background skipped: {e}", flush=True)

    # --- Phase 2: 2D アバター + 吹き出し ------------------------------------
    def _init_avatar(self) -> None:
        """features.linko_avatar=True なら btn_rinko を 2D アバター表示に切替。

        - 128px アバターを左に配置 (btn_rinko は _build_ui で既に 128 サイズに作られている)
        - SpeechBubble を生成して linko_avatar に register
        - まばたきアイドルアニメを起動
        - COMPACT 窓サイズを 240x140 に拡大
        """
        self._avatar_enabled = False
        self._avatar_ctk_images: dict = {}
        self._speech_bubble = None
        try:
            if not getattr(self, "_avatar_on", False):
                return
            import linko_avatar
            # アバターのソース画像は 160px を優先して読む (140px 表示でも鮮明)。
            # 160px セットが無い環境では従来の 128px にフォールバック。
            if not linko_avatar.is_ready():
                if not (linko_avatar.init(160) or linko_avatar.init(128)):
                    print("[linko_avatar] init failed (画像が見つからない)", flush=True)
                    return
            self._avatar_enabled = True
            # _avatar_size は _build_ui で (120,120) に設定済み
            # 初期ポーズ
            self._set_avatar_pose("normal")
            # アバターポーズ変化時の UI 更新フックを登録
            linko_avatar.set_ui_callback(self._on_avatar_pose_change)
            # 吹き出し
            try:
                from speech_bubble import SpeechBubble
                self._speech_bubble = SpeechBubble(parent_window=self)
                linko_avatar.register_speech_bubble(self._speech_bubble)
            except Exception as e:
                print(f"[linko_avatar] speech bubble init failed: {e}", flush=True)
            # まばたき
            try:
                linko_avatar.start_idle_animation()
            except Exception as e:
                print(f"[linko_avatar] idle animation start failed: {e}", flush=True)
            # 「リン子を閉じる」ボタン: カードの右上角に小さく置く
            # (アバターの顔や下部のボタン列に被らない位置)
            try:
                self.btn_close_mini = ctk.CTkButton(
                    self.frame, text="✕", width=22, height=22, corner_radius=11,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color=Theme.CLOSE_FG, hover_color=Theme.CLOSE_HOVER,
                    text_color=Theme.CLOSE_TEXT,
                    command=self._on_close_clicked,
                )
                self.btn_close_mini.place(relx=1.0, rely=0.0, x=-8, y=8, anchor="ne")
            except Exception as e:
                print(f"[linko_avatar] close button failed: {e}", flush=True)
            # window 位置を更新サイズで取り直す
            try:
                self._position_bottom_right(compact=True)
            except Exception:
                pass
        except Exception as e:
            print(f"[linko_avatar] init exception: {e}", flush=True)

    def _on_close_clicked(self) -> None:
        """「リン子を閉じる」: ミニポートと吹き出しを隠す。再表示はトレイ / ショートカットから。"""
        try:
            if self._speech_bubble is not None:
                self._speech_bubble.hide()
        except Exception:
            pass
        if self._on_hide:
            self._on_hide()

    def _bind_avatar_click_drag(self, widget) -> None:
        """アバター Label に「クリック (吹き出し) と ドラッグ (移動)」を両立させる。

        移動量が閾値未満なら click、超えたら drag とみなす。
        """
        self._avatar_press_x = 0
        self._avatar_press_y = 0
        self._avatar_moved = False
        widget.bind("<Button-1>", self._on_avatar_press)
        widget.bind("<B1-Motion>", self._on_avatar_drag)
        widget.bind("<ButtonRelease-1>", self._on_avatar_release)

    def _on_avatar_press(self, event):
        self._avatar_press_x = event.x_root
        self._avatar_press_y = event.y_root
        self._avatar_moved = False
        self._drag_win_x = self.winfo_x()
        self._drag_win_y = self.winfo_y()
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root

    def _on_avatar_drag(self, event):
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        if abs(event.x_root - self._avatar_press_x) > 5 or abs(event.y_root - self._avatar_press_y) > 5:
            self._avatar_moved = True
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._drag_win_x += dx
        self._drag_win_y += dy
        self.geometry(f"+{self._drag_win_x}+{self._drag_win_y}")
        if not self._input_visible:
            self._last_compact_x = self._drag_win_x
            self._last_compact_y = self._drag_win_y

    def _on_avatar_release(self, event):
        if not self._avatar_moved:
            self._on_avatar_click()

    def _on_avatar_click(self) -> None:
        """アバターをクリック (移動なし) されたとき。

        Phase 2.1: 軽い挨拶を吹き出しに出す (口パクなし、音声なし、Clippy 回避の遊び心)
        Phase 5a: ここからチャット (ブレスト) を開く想定。
        """
        try:
            if self._avatar_enabled:
                import linko_avatar
                # duration_sec=None で吹き出しのみ (口パク・音声なし)
                linko_avatar.say("こんにちは、リン子です。何かあったら呼んでくださいね。", duration_sec=None)
                return
        except Exception:
            pass
        self._open_taskboard()

    def _on_avatar_pose_change(self, pose: str) -> None:
        """linko_avatar の lipsync スレッドから呼ばれる。Tk メインスレッドへ dispatch。"""
        try:
            self.after(0, lambda p=pose: self._set_avatar_pose(p))
        except Exception:
            pass

    def _set_avatar_pose(self, pose: str) -> None:
        if not getattr(self, "_avatar_enabled", False):
            return
        try:
            import linko_avatar
            img = linko_avatar.get_image(pose)
        except Exception as e:
            self._avatar_log(f"_set_avatar_pose get_image error: {e}")
            return
        if img is None:
            self._avatar_log(f"_set_avatar_pose: img None for '{pose}'")
            return
        if pose not in self._avatar_ctk_images:
            try:
                self._avatar_ctk_images[pose] = ctk.CTkImage(
                    light_image=img, dark_image=img, size=self._avatar_size,
                )
            except Exception as e:
                self._avatar_log(f"_set_avatar_pose CTkImage error: {e}")
                return
        try:
            self.btn_rinko.configure(image=self._avatar_ctk_images[pose], text="")
            self._rinko_image = self._avatar_ctk_images[pose]  # GC 防止のため参照保持
            if not getattr(self, "_pose_logged_once", False):
                self._avatar_log(f"_set_avatar_pose OK (first): pose={pose} size={self._avatar_size}")
                self._pose_logged_once = True
        except Exception as e:
            self._avatar_log(f"_set_avatar_pose configure error: {e}")

    def _avatar_log(self, msg: str) -> None:
        try:
            from app_log import log_info
            log_info("[mini_port] " + msg)
        except Exception:
            print("[mini_port] " + msg, flush=True)

    def _setup_context_menu(self):
        """右クリックで通知オン/オフ・設定・ミニポート非表示のメニューを表示。"""
        import tkinter as tk
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(label="", command=self._ctx_toggle_notifications)
        self._ctx_menu.add_command(label="設定...", command=self._ctx_open_settings)
        self._ctx_menu.add_command(label="ミニポートを非表示にする", command=self._ctx_hide_miniport)
        for widget in (self.frame, self.compact_frame):
            widget.bind("<Button-3>", self._on_right_click)
        if hasattr(self, "input_frame"):
            self.input_frame.bind("<Button-3>", self._on_right_click)

    def _on_right_click(self, event):
        """右クリックでコンテキストメニューを表示。"""
        enabled = self._get_notifications_enabled()
        self._ctx_menu.entryconfig(0, label="通知をオフにする" if enabled else "通知をオンにする")
        try:
            self._ctx_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._ctx_menu.grab_release()

    def _ctx_toggle_notifications(self):
        if self._on_notifications_toggle:
            self._on_notifications_toggle()

    def _ctx_open_settings(self):
        """右クリック「設定...」で設定ダイアログを開く。
        Tk メインスレッド (= ミニポート) から呼ばれるので after で再ディスパッチ不要。
        """
        try:
            from settings_dialog import open_settings_dialog
            open_settings_dialog(master=self)
        except Exception as e:
            print("settings open failed:", e, flush=True)

    def _ctx_hide_miniport(self):
        if self._on_hide:
            self._on_hide()

    def _setup_drag(self):
        """ウィンドウをマウス/タッチでドラッグ移動できるようにする。"""
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_win_x = 0
        self._drag_win_y = 0
        self.frame.bind("<Button-1>", self._on_drag_start)
        self.frame.bind("<B1-Motion>", self._on_drag_motion)
        self.compact_frame.bind("<Button-1>", self._on_drag_start)
        self.compact_frame.bind("<B1-Motion>", self._on_drag_motion)
        self.input_frame.bind("<Button-1>", self._on_drag_start)
        self.input_frame.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event):
        """ドラッグ開始。ボタン・テキストボックス上では開始しない。"""
        w = event.widget
        if w in (self.btn_rinko, self.btn_post, self.btn_send, self.btn_close, self.textbox):
            return
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._drag_win_x = self.winfo_x()
        self._drag_win_y = self.winfo_y()

    def _on_drag_motion(self, event):
        """ドラッグ中: ウィンドウを移動。"""
        w = event.widget
        if w in (self.btn_rinko, self.btn_post, self.btn_send, self.btn_close, self.textbox):
            return
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._drag_win_x += dx
        self._drag_win_y += dy
        self.geometry(f"+{self._drag_win_x}+{self._drag_win_y}")
        if not self._input_visible:
            self._last_compact_x = self._drag_win_x
            self._last_compact_y = self._drag_win_y

    def _show_input(self):
        if self._input_visible:
            return
        self._input_visible = True
        self.compact_frame.pack_forget()
        self.input_frame.pack(fill="both", expand=True, padx=12, pady=10)
        self._position_bottom_right(compact=False)
        self._show_placeholder()
        self.textbox.focus_set()

    def _hide_input(self):
        if not self._input_visible:
            return
        self._input_visible = False
        self.textbox.delete("1.0", "end")
        self._placeholder_visible = False
        self.input_frame.pack_forget()
        self.compact_frame.pack(fill="x", padx=10, pady=8)
        # 閉じる時は最後にドラッグしたコンパクト時の位置に戻す
        self.update_idletasks()
        x, y = self._last_compact_x, self._last_compact_y
        self.geometry(f"{self.COMPACT_W}x{self.COMPACT_H}+{x}+{y}")
        self._drag_win_x, self._drag_win_y = x, y

    def _show_placeholder(self):
        if self._placeholder_visible:
            return
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", self.PLACEHOLDER_TEXT)
        self.textbox.configure(text_color=Theme.PLACEHOLDER_TEXT)
        self._placeholder_visible = True

    def _remove_placeholder(self):
        if not self._placeholder_visible:
            return
        self._placeholder_visible = False
        self.textbox.delete("1.0", "end")
        self.textbox.configure(text_color=Theme.INPUT_TEXT)

    def _on_textbox_focus_in(self, event=None):
        if self._placeholder_visible:
            self._remove_placeholder()

    def _on_textbox_focus_out(self, event=None):
        try:
            t = self.textbox.get("1.0", "end").strip()
        except Exception:
            t = ""
        if not t and self._input_visible:
            self._show_placeholder()

    def _on_textbox_key(self, event=None):
        if self._placeholder_visible:
            self._remove_placeholder()

    def _open_taskboard(self):
        """「ボード」クリック: 各自の Board System パーソナルボードを開く。未設定時はメール入力で解決してから開く。"""
        cfg = load_config()
        personal_url = get_board_system_personal_url(cfg)
        if personal_url:
            webbrowser.open(personal_url)
            return
        board_url = get_effective_board_system_url(cfg)
        if board_url:
            # 親に self（ミニポート窓）を渡し、名前入力と取り違えないようにする
            url = _prompt_email_and_resolve_personal(parent=self)
            if url:
                webbrowser.open(url)
                return
        webbrowser.open(_taskboard_url())

    def _position_bottom_right(self, compact: bool = True):
        self.update_idletasks()
        w = self.COMPACT_W if compact else self.EXPANDED_W
        h = self.COMPACT_H if compact else self.EXPANDED_H
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        margin = 24
        taskbar_margin = 50
        x = sw - w - margin
        y = sh - h - taskbar_margin - margin
        self.geometry(f"{w}x{h}+{x}+{y}")
        self._drag_win_x = x
        self._drag_win_y = y
        if compact:
            self._last_compact_x = x
            self._last_compact_y = y

    def _on_send_shortcut(self, event=None):
        self._on_send()
        return "break"

    def _on_send(self):
        text = self.textbox.get("1.0", "end").strip()
        if not text or text == self.PLACEHOLDER_TEXT:
            return
        self.label_feedback.configure(text="送信中…", text_color=Theme.FEEDBACK_INFO)
        self.btn_send.configure(state="disabled")
        # 送信は別スレッドで実行し、結果を after で UI に反映（フリーズ防止・確実に完了）
        def do_send():
            result = _send_content(text)
            self.after(0, lambda: self._on_send_done(result))

        threading.Thread(target=do_send, daemon=True).start()

    def _on_send_done(self, result: Tuple[bool, str]):
        ok, msg = result
        self.btn_send.configure(state="normal")
        if ok:
            self.label_feedback.configure(
                text="✓ 送信しました（表示されない場合は付箋ボードを再読み込み）",
                text_color=Theme.FEEDBACK_OK,
            )
            self.textbox.delete("1.0", "end")
            if self._feedback_job:
                self.after_cancel(self._feedback_job)
            # 1.5秒後にフィードバックを消して元のサイズ（リン子+投稿のみ）に戻す
            self._feedback_job = self.after(1500, self._clear_feedback_and_hide)
        else:
            self.label_feedback.configure(text=msg[:60], text_color=Theme.FEEDBACK_ERROR)
            if self._feedback_job:
                self.after_cancel(self._feedback_job)
            self._feedback_job = self.after(3000, self._clear_feedback)

    def _clear_feedback_and_hide(self):
        self._feedback_job = None
        self.label_feedback.configure(text="", text_color=("gray30", "gray70"))
        self._hide_input()

    def _clear_feedback(self):
        self._feedback_job = None
        self.label_feedback.configure(text="", text_color=("gray30", "gray70"))

    def focus_and_raise(self):
        self.after(0, self._do_focus)

    def _do_focus(self):
        self.lift()
        self.attributes("-topmost", True)
        if self._input_visible:
            self.textbox.focus_set()
        else:
            self.btn_post.focus_set()

    def _start_hotkey_listener(self):
        def on_activate():
            self.focus_and_raise()

        def listen():
            with keyboard.GlobalHotKeys({"<ctrl>+<shift>+<space>": on_activate}) as h:
                h.join()

        t = threading.Thread(target=listen, daemon=True)
        t.start()


def main():
    ctk.set_appearance_mode("system")
    app = MiniPortWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
