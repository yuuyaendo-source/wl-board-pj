# -*- coding: utf-8 -*-
"""
Windows 起動時にアプリを自動起動するためのスタートアップ登録。
レジストリ HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run を使用する。
"""
import os
import sys

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Wonder Rinko"


def _get_startup_command():
    """
    ［スタートアップに登録するときの起動コマンド］を返す。
    - 凍結（exe）時: exe のフルパス
    - スクリプト時: pythonw.exe のフルパス + app.py のフルパス（スペースはクォート）
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_py = os.path.join(base_dir, "app.py")
    # pythonw.exe は python.exe と同じディレクトリにある想定
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.isfile(pythonw):
        pythonw = os.path.join(python_dir, "python.exe")
    # パスにスペースが含まれる場合はダブルクォート
    def quote(s):
        return f'"{s}"' if " " in s else s
    return f"{quote(pythonw)} {quote(app_py)}"


def is_startup_enabled():
    """スタートアップに登録されているか。"""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY_PATH,
            0,
            winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def set_startup_enabled(enabled):
    """
    スタートアップの有効/無効を設定する。
    enabled=True で登録、False で削除。成功したら True。
    """
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            if enabled:
                cmd = _get_startup_command()
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
            return True
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False
