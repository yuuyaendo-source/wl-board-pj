# -*- coding: utf-8 -*-
"""ミニポート / 吹き出しのデザイントークン (色・角丸・サイズ) を一元管理。

これまで mini_port.py / speech_bubble.py に ``("#5a9e5c", "#1b5e20")`` のような
(ライトモード, ダークモード) のタプルがベタ書きされ、色を 1 つ変えるだけで
複数箇所の修正が必要だった。ここに集約することで、配色やサイズの調整を
1 ファイルで完結させる。

色はすべて ``(light, dark)`` のタプル。CustomTkinter の fg_color / text_color に
そのまま渡せる。

トーン: ブランドの緑を残しつつ「もう少し濃いめ」に寄せた配色。
"""
from __future__ import annotations

import sys

# プラットフォーム判定 (透過処理の分岐に使う)。
# -transparentcolor は Windows 専用のため、非 Windows では別処理にする。
IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"


class Theme:
    # --- ブランドグリーン (やや濃いめ) -------------------------------------
    # 主アクション (投稿など): 塗りつぶしの濃い緑
    PRIMARY = ("#3d8b40", "#1b5e20")
    PRIMARY_HOVER = ("#2f7a33", "#145214")
    PRIMARY_TEXT = ("#ffffff", "#ffffff")

    # 副アクション (ボードなど): 淡色地 + 緑枠 + 緑文字 (主より控えめ)
    SECONDARY = ("#dcefdd", "#22692a")
    SECONDARY_HOVER = ("#c8e6c9", "#2e7d32")
    SECONDARY_TEXT = ("#1b5e20", "#e8f5e9")
    SECONDARY_BORDER = ("#5a9e5c", "#4caf50")

    # --- カード (ミニポート本体) -------------------------------------------
    # もう少し濃いめの淡緑サーフェス (純白に寄せすぎない)
    SURFACE = ("#e3f1e4", "#1f5e22")
    SURFACE_BORDER = ("#6fb573", "#3d8b40")

    # --- 吹き出し ----------------------------------------------------------
    BUBBLE_FG = ("#ffffff", "#1b5e20")
    BUBBLE_BORDER = ("#5a9e5c", "#7bc47f")
    BUBBLE_TEXT = ("#1b5e20", "#e8f5e9")

    # --- 入力欄 ------------------------------------------------------------
    INPUT_FG = ("#ffffff", "#263238")
    INPUT_BORDER = ("#5a9e5c", "#2e7d32")
    INPUT_TEXT = ("#1a1a1a", "#e0e0e0")
    PLACEHOLDER_TEXT = ("#2e5c30", "#9ccc9e")

    # --- フィードバック文言 -------------------------------------------------
    FEEDBACK_INFO = ("#1b5e20", "#a5d6a7")
    FEEDBACK_OK = ("#2e7d32", "#81c784")
    FEEDBACK_ERROR = ("#c62828", "#ef5350")

    # --- ✕ (閉じる) ボタン --------------------------------------------------
    CLOSE_FG = ("#cfe8d0", "#3d8b40")
    CLOSE_HOVER = ("#f0a0a0", "#c0392b")
    CLOSE_TEXT = ("#1b5e20", "#ffffff")

    # --- 角丸 --------------------------------------------------------------
    RADIUS_CARD = 24
    RADIUS_BUBBLE = 18
    RADIUS_PILL = 21
    RADIUS_INPUT = 12

    # --- 透過 --------------------------------------------------------------
    # ほぼ黒。UI で使わない色を transparentcolor キーにする (Windows のみ有効)。
    TRANSPARENT_KEY = "#010101"
    WINDOW_ALPHA = 0.92


def apply_window_transparency(window, *, fg_fallback) -> str:
    """ウィンドウに透過設定を適用する (クロスプラットフォーム対応)。

    - Windows: ``-transparentcolor`` で外枠を透明化し、角丸フレームだけ見せる。
    - 非 Windows: transparentcolor が非対応 (黒い四角が残る) ため使わず、
      ウィンドウ背景をサーフェス色にして角丸の外を馴染ませる。

    戻り値: 透過キー色 (Windows で透過が効いたとき) か空文字 (非対応時)。
    呼び出し側はこの戻り値で吹き出しの尻尾背景などを切り替えられる。
    """
    try:
        window.attributes("-alpha", Theme.WINDOW_ALPHA)
    except Exception:
        pass
    if IS_WINDOWS:
        try:
            window.configure(fg_color=Theme.TRANSPARENT_KEY)
            window.attributes("-transparentcolor", Theme.TRANSPARENT_KEY)
            return Theme.TRANSPARENT_KEY
        except Exception:
            pass
    # 非 Windows もしくは transparentcolor 失敗時: 角の外をサーフェス色で馴染ませる
    try:
        window.configure(fg_color=fg_fallback)
    except Exception:
        pass
    return ""
