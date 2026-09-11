# -*- coding: utf-8 -*-
"""
Windows 起動時にアプリを自動起動するためのスタートアップ登録。
セキュリティソフトの誤検知を回避するため、レジストリ操作 (winreg) を全廃し、
Windows のスタートアップフォルダ (shell:startup) へのショートカット (.lnk) 配置・削除を行う。
"""
import os
import sys

LNK_NAME = "Wonder Linko.lnk"
_STARTUP_APPROVED_KEY = (
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"
)


def _get_startup_dir() -> str:
    """Windows のスタートアップフォルダのパスを返す。"""
    appdata = os.environ.get("APPDATA")
    if appdata:
        d = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
        if os.path.isdir(d):
            return d
    try:
        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")
        return shell.SpecialFolders("Startup")
    except Exception:
        pass
    # フォールバック
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return os.path.join(
        home, r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
    )


def _get_shortcut_path() -> str:
    """スタートアップ内のショートカットのフルパスを返す。"""
    return os.path.join(_get_startup_dir(), LNK_NAME)


def is_disabled_by_task_manager() -> bool:
    """タスクマネージャーの「スタートアップ」タブで明示的に無効化されているかを判定する。
    無効化されている場合は True、有効または未設定（キー・値なし）の場合は False を返す。
    """
    if sys.platform != "win32":
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _STARTUP_APPROVED_KEY, 0, winreg.KEY_READ
        ) as key:
            val, _ = winreg.QueryValueEx(key, LNK_NAME)
            # REG_BINARY: 先頭バイトが 0x02 なら有効、0x03 など非2 はタスクマネージャーで無効化
            if isinstance(val, bytes) and len(val) > 0:
                return val[0] != 2
    except (FileNotFoundError, OSError):
        pass
    except Exception as e:
        try:
            from app_log import log_info

            log_info(f"StartupApproved 読み取りスキップ: {e}")
        except Exception:
            pass
    return False


def is_startup_enabled() -> bool:
    """スタートアップに登録（ショートカットが存在し、かつタスクマネージャーで無効化されていない）されているか。"""
    if sys.platform != "win32":
        return False
    try:
        lnk_path = _get_shortcut_path()
        if not os.path.isfile(lnk_path):
            return False
        # ショートカットがあってもタスクマネージャーで無効化されていれば False
        if is_disabled_by_task_manager():
            return False
        return True
    except Exception:
        return False


def set_startup_enabled(enabled: bool) -> bool:
    """
    スタートアップの有効/無効を設定する。
    enabled=True でショートカットを作成（およびタスクマネージャー制限解除）、False で削除。成功したら True。
    """
    if sys.platform != "win32":
        return False

    lnk_path = _get_shortcut_path()
    try:
        if enabled:
            # タスクマネージャーによる無効化ブロックを解除 (該当エントリがあれば削除して初期有効状態に戻す)
            try:
                import winreg

                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    _STARTUP_APPROVED_KEY,
                    0,
                    winreg.KEY_SET_VALUE,
                ) as key:
                    winreg.DeleteValue(key, LNK_NAME)
            except (FileNotFoundError, OSError):
                pass
            except Exception as e:
                try:
                    from app_log import log_info

                    log_info(f"StartupApproved 制限解除スキップ: {e}")
                except Exception:
                    pass
            # ターゲット情報取得
            if getattr(sys, "frozen", False):
                target_path = sys.executable
                arguments = ""
                working_dir = os.path.dirname(sys.executable)
                icon_location = f"{sys.executable},0"
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                app_py = os.path.join(base_dir, "app.py")
                python_dir = os.path.dirname(sys.executable)
                pythonw = os.path.join(python_dir, "pythonw.exe")
                if not os.path.isfile(pythonw):
                    pythonw = os.path.join(python_dir, "python.exe")
                target_path = pythonw
                arguments = f'"{app_py}"'
                working_dir = base_dir
                icon_location = ""

            os.makedirs(os.path.dirname(lnk_path), exist_ok=True)

            import win32com.client

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(lnk_path)
            shortcut.TargetPath = target_path
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = working_dir
            if icon_location:
                shortcut.IconLocation = icon_location
            shortcut.Save()
            return True
        else:
            if os.path.isfile(lnk_path):
                try:
                    os.remove(lnk_path)
                except Exception as e:
                    try:
                        from app_log import log_error

                        log_error(f"スタートアップショートカット削除失敗: {e}")
                    except Exception:
                        pass
                    return False
            return True
    except Exception as e:
        try:
            from app_log import log_error

            log_error(f"スタートアップ設定失敗: {e}")
        except Exception:
            pass
        return False
