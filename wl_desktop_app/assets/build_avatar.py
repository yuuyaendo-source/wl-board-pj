"""linko_v2.1_*.png から ミニポート用アバター画像セットを生成する。

入力:  assets/source/linko_v2.1_{normal,happy,sad,angry,funny,a,i,u,e,o}.png (1024x1024)
出力:
  assets/avatar/{pose}_{size}.png  (透過 PNG、サイズ別)

処理:
  1. 背景の薄水色を透過に置換 (Phase 1 build_icons と同じ手法)
  2. 透過 bbox でトリム + 正方形整形 + 余白少々
  3. アバター用各サイズ (96, 128, 160) に LANCZOS リサイズ
  4. 出力

これで linko_avatar.py が ``avatar/normal_96.png`` のような決まり切ったパスから
画像を読めるようになる。
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

ASSETS_DIR = Path(__file__).resolve().parent
SOURCE_DIR = ASSETS_DIR / "source"
OUT_DIR = ASSETS_DIR / "avatar"

POSES = ["normal", "happy", "sad", "angry", "funny", "a", "i", "u", "e", "o"]
SIZES = [48, 64, 96, 128, 160]


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
    """透過 bbox トリム + 正方形 + 余白 padding。"""
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
    OUT_DIR.mkdir(exist_ok=True)
    print(f"output dir: {OUT_DIR}")

    for pose in POSES:
        src_path = SOURCE_DIR / f"linko_v2.1_{pose}.png"
        if not src_path.is_file():
            print(f"skip {pose}: source not found ({src_path.name})")
            continue
        src = Image.open(src_path)
        transparent = remove_background(src.copy(), tolerance=25)
        trimmed = trim_transparent(transparent, padding_ratio=0.04)
        for size in SIZES:
            out = trimmed.resize((size, size), Image.LANCZOS)
            out_path = OUT_DIR / f"{pose}_{size}.png"
            out.save(out_path, "PNG")
        print(f"wrote {pose}_{{{','.join(str(s) for s in SIZES)}}}.png (trimmed={trimmed.size})")


if __name__ == "__main__":
    main()
