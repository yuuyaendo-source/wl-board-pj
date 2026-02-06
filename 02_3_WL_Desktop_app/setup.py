# -*- coding: utf-8 -*-
"""
Wonder Rinko Desktop App - cx_Freeze 用 setup（MSI ビルド）
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
}

# MSI 用オプション（会社ポリシーで exe 直接実行が不可なため MSI 配布用）
# initial_target_dir: [Personal] は解釈されず "\Wonder Rinko" がネットワークパスになる不具合があるため、
# [LocalAppDataFolder] を使用（C:\Users\<user>\AppData\Local\Wonder Rinko）
bdist_msi_options = {
    "add_to_path": False,
    "all_users": False,  # 現在のユーザーのみにインストール
    "initial_target_dir": "[LocalAppDataFolder]Wonder Rinko",
    "target_name": "WonderRinko.msi",
    "upgrade_code": "{B29E4C50-1A2B-4C3D-9E5F-6A7B8C9D0E1F}",
    "summary_data": {
        "author": "Wonder Rinko",
        "comments": "Personal Rinko Agent - 付箋お知らせ・パーソナルモード",
    },
}

executables = [
    Executable(
        "app.py",
        base="Win32GUI",
        target_name="WonderRinko.exe",
        shortcut_name="Wonder Rinko",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name="Wonder Rinko",
    version="0.1.0",
    description="Personal Rinko Agent - 付箋お知らせ・パーソナルモード",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
