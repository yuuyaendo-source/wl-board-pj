"""Linko_ver1.png から各種アイコンを生成するスクリプト。

入力:  assets/source/Linko_ver1.png (1024x1024 RGBA)
出力:
  assets/linko.ico         16/24/32/48/64/128/256 マルチサイズ Windows アイコン
  assets/linko_256.png     256x256 透過 PNG
  assets/linko_128.png     128x128 透過 PNG
  assets/linko_64.png      64x64 透過 PNG
  assets/toast_icon.png    256x256 透過 PNG (既存トースト通知用と互換)
  assets/tray_icon.png     32x32 透過 PNG (システムトレイ用)

処理:
  1. 背景の単色 (薄水色) を透過に置換
  2. 顔を含む正方形にクロップ
  3. 各サイズへリサイズ (LANCZOS)
  4. .ico マルチサイズ生成
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

ASSETS_DIR = Path(__file__).resolve().parent
SOURCE = ASSETS_DIR / "source" / "Linko_ver1.png"


def remove_background(img: Image.Image, tolerance: int = 25) -> Image.Image:
    """四隅の中央値を背景色とみなし、近い色のピクセルを透過化する。"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    samples = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    rs = sorted(s[0] for s in samples)
    gs = sorted(s[1] for s in samples)
    bs = sorted(s[2] for s in samples)
    br, bg, bb = rs[len(rs) // 2], gs[len(gs) // 2], bs[len(bs) // 2]
    print(f"detected bg color: rgb({br}, {bg}, {bb})")

    data = img.getdata()
    new_data = []
    for r, g, b, a in data:
        if abs(r - br) <= tolerance and abs(g - bg) <= tolerance and abs(b - bb) <= tolerance:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img


def trim_transparent(img: Image.Image, padding_ratio: float = 0.04) -> Image.Image:
    """透過部分を bbox でトリム + 正方形に整形 + 余白 padding。"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    bbox = img.getbbox()
    if bbox is None:
        return img
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    side = max(cw, ch)
    padding = int(side * padding_ratio)
    canvas_side = side + padding * 2
    canvas = Image.new("RGBA", (canvas_side, canvas_side), (0, 0, 0, 0))
    canvas.paste(cropped, ((canvas_side - cw) // 2, (canvas_side - ch) // 2))
    return canvas


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"source not found: {SOURCE}")

    src = Image.open(SOURCE)
    print(f"source: {SOURCE.name} size={src.size} mode={src.mode}")

    transparent = remove_background(src.copy(), tolerance=25)
    trimmed = trim_transparent(transparent, padding_ratio=0.04)
    print(f"trimmed size: {trimmed.size}")

    for size in (256, 128, 64):
        out = trimmed.resize((size, size), Image.LANCZOS)
        out.save(ASSETS_DIR / f"linko_{size}.png", "PNG")
        print(f"wrote linko_{size}.png")

    toast = trimmed.resize((256, 256), Image.LANCZOS)
    toast.save(ASSETS_DIR / "toast_icon.png", "PNG")
    print("wrote toast_icon.png")

    tray = trimmed.resize((32, 32), Image.LANCZOS)
    tray.save(ASSETS_DIR / "tray_icon.png", "PNG")
    print("wrote tray_icon.png")

    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path = ASSETS_DIR / "linko.ico"
    trimmed.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"wrote linko.ico (multi-size {ico_sizes})")


if __name__ == "__main__":
    main()
