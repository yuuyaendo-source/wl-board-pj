# -*- coding: utf-8 -*-
"""
Wonder Linko Desktop App - cx_Freeze 用 setup（MSI ビルド）
実行: python setup.py bdist_msi  または  .\build_msi.ps1
"""
import os
from cx_Freeze import Executable, setup

# 同梱するデータファイル（ビルド時に存在するものだけ）
include_files = []
if os.path.exists("config.json"):
    include_files.append(("config.json", "config.json"))
if os.path.exists("toast_icon.png"):
    include_files.append(("toast_icon.png", "toast_icon.png"))

build_exe_options = {
    "excludes": ["tkinter", "unittest"],
    "include_files": include_files,
    # トレイアイコン用。cx_Freeze が自動検出しないため明示的に含める
    "includes": ["pystray", "PIL", "PIL.Image", "winotify", "win10toast", "win10toast_click", "requests"],
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
        base="Win32GUI",
        target_name="WonderLinko.exe",
        shortcut_name="Wonder Linko",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name="WonderLinkoDesktop",
    version="1.0.0",
    description="Wonder Linko Agent",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
