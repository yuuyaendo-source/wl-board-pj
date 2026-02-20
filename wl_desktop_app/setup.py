# -*- coding: utf-8 -*-
"""
Wonder Linko Desktop App - cx_Freeze 用 setup（MSI ビルド）
実行: python setup.py bdist_msi  または  .\build_msi.ps1

根本方針: PIL は cx_Freeze の自動収集に頼らず、lib/PIL に全ファイルを明示コピーする。
実行時は app.py 先頭で sys.path に lib を追加し、PIL を lib/PIL から読み込む。
"""
import os
import sys
from cx_Freeze import Executable, setup

include_files = []
if os.path.exists("config.json"):
    include_files.append(("config.json", "config.json"))
if os.path.exists("toast_icon.png"):
    include_files.append(("toast_icon.png", "toast_icon.png"))
if os.path.exists("docs/Windows通知がオフになった場合.md"):
    include_files.append(("docs/Windows通知がオフになった場合.md", "docs/Windows通知がオフになった場合.md"))
if os.path.exists("docs/通知設定をリセットする.ps1"):
    include_files.append(("docs/通知設定をリセットする.ps1", "docs/通知設定をリセットする.ps1"))

# PIL を library.zip に入れず、lib/PIL に全ファイル（.py + .pyd 等）を明示的にコピー
# excludes で PIL を除外し、ここでだけ同梱する。.pyd が無いと MSI インストール後に起動エラーになる
# 重要: 同梱する _imaging*.pyd は「この Python のバージョン」と一致している必要がある（cp312=3.12, cp314=3.14）
_pil_imaging_pyd_count = 0
_expected_suffix = f".cp{sys.version_info.major}{sys.version_info.minor}-"
try:
    import PIL
    pil_root = os.path.abspath(PIL.__file__)
    if os.path.isfile(pil_root):
        pil_root = os.path.dirname(pil_root)
    for dirpath, _dirnames, filenames in os.walk(pil_root):
        for name in filenames:
            if name.startswith("."):
                continue
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, pil_root)
            dest = os.path.join("lib", "PIL", rel).replace("\\", "/")
            include_files.append((src, dest))
            if "_imaging" in name and name.endswith(".pyd"):
                _pil_imaging_pyd_count += 1
except Exception:
    pass
if _pil_imaging_pyd_count == 0:
    raise SystemExit(
        "PIL の _imaging*.pyd が 1 つも見つかりません。"
        " pip install Pillow で Pillow を入れ直してからビルドしてください。"
    )
# この Python バージョン用の _imaging が含まれているか確認（cp312/cp314 等の一致）
_has_matching_pyd = any(_expected_suffix in d[0] for d in include_files if "_imaging" in d[0] and d[0].endswith(".pyd"))
if not _has_matching_pyd:
    raise SystemExit(
        f"PIL の _imaging が「この Python ({sys.version_info.major}.{sys.version_info.minor})」用ではありません。"
        " pip install --force-reinstall Pillow を実行してからビルドしてください。"
    )

build_exe_options = {
    "excludes": ["unittest", "PIL"],
    "include_files": include_files,
    "includes": [
        "pystray", "winotify", "win10toast", "win10toast_click", "requests",
        "customtkinter", "pynput",
    ],
    "packages": ["customtkinter", "pynput"],
    "zip_exclude_packages": ["*"],
}

# MSI 用オプション（ユーザー領域にインストール・管理者不要）
# all_users=False で per-user（cx_Freeze が ALLUSERS を適切に設定）。インストール先は C:\Users\<user>\AppData\Local\WonderLink\WonderLinko
bdist_msi_options = {
    "add_to_path": False,
    "all_users": False,
    "initial_target_dir": r"[LocalAppDataFolder]\WonderLink\WonderLinko",
    "target_name": "WonderLinko.msi",
    "upgrade_code": "{B29E4C50-1A2B-4C3D-9E5F-6A7B8C9D0E1F}",
    "summary_data": {
        "author": "Wonder Linko",
        "comments": "Personal Linko Agent - 付箋お知らせ・パーソナルモード",
    },
}

executables = [
    Executable(
        "app.py",
        base="gui",  # cx_Freeze 8 では "gui"（コンソール非表示）。旧 "Win32GUI" は "gui" に変更済み
        target_name="WonderLinko.exe",
        shortcut_name="Wonder Linko",
        shortcut_dir="DesktopFolder",
    )
]

# バージョンは version.py で一元管理
from version import __version__

setup(
    name="WonderLinkoDesktop",
    version=__version__,
    description="Wonder Linko Agent",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
