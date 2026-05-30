"""ミニポート (マスコット表示) の角丸カード背景 PNG を生成する。

出力:
  assets/card_bg.png       (ライトモード用)
  assets/card_bg_dark.png  (ダークモード用)

質感:
  - 角丸 (Theme.RADIUS_CARD に合わせる)
  - 上→下の淡いグラデーション (ブランド緑をやや濃いめに)
  - 上端にごく薄いハイライト、外周に細い緑の縁

mini_port.py の _apply_card_background() がこの PNG を見つけると、単色サーフェスの
代わりに敷いて質感を上げる。PNG が無ければ従来の単色のまま (安全フォールバック)。

実行:
  cd wl_desktop_app && python assets/build_card_bg.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).resolve().parent

# mini_port.py のマスコットカードサイズ (COMPACT_W x COMPACT_H) に合わせる
CARD_W = 264
CARD_H = 224
RADIUS = 24  # Theme.RADIUS_CARD
SS = 4       # スーパーサンプリング倍率 (角丸を滑らかに)

# (top_rgb, bottom_rgb, border_rgb)
LIGHT = ((238, 246, 239), (211, 232, 213), (111, 181, 115))
DARK = ((40, 112, 46), (24, 80, 30), (61, 139, 64))


def _vertical_gradient(w: int, h: int, top, bottom) -> Image.Image:
    """上→下の縦グラデーション (RGBA, 不透明)。"""
    grad = Image.new("RGBA", (w, h))
    px = grad.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = round(top[0] + (bottom[0] - top[0]) * t)
        g = round(top[1] + (bottom[1] - top[1]) * t)
        b = round(top[2] + (bottom[2] - top[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b, 255)
    return grad


def _rounded_card(top, bottom, border) -> Image.Image:
    w, h, rad = CARD_W * SS, CARD_H * SS, RADIUS * SS

    # 角丸マスク
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=rad, fill=255)

    # グラデーション本体をマスクで角丸に切り抜く
    grad = _vertical_gradient(w, h, top, bottom)
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    card.paste(grad, (0, 0), mask)

    draw = ImageDraw.Draw(card)
    # 上端のごく薄いハイライト (内側に白を少し)
    draw.rounded_rectangle(
        [SS, SS, w - 1 - SS, h - 1 - SS], radius=rad - SS,
        outline=(255, 255, 255, 70), width=SS,
    )
    # 外周の細い緑の縁
    draw.rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=rad,
        outline=border + (255,), width=max(1, SS),
    )

    return card.resize((CARD_W, CARD_H), Image.LANCZOS)


def main() -> None:
    out_light = ASSETS_DIR / "card_bg.png"
    out_dark = ASSETS_DIR / "card_bg_dark.png"
    _rounded_card(*LIGHT).save(out_light, "PNG")
    _rounded_card(*DARK).save(out_dark, "PNG")
    print(f"wrote {out_light.name} / {out_dark.name} ({CARD_W}x{CARD_H})")


if __name__ == "__main__":
    main()
