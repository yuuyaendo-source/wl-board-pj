# -*- coding: utf-8 -*-
"""
自動更新: 更新チェック用 URL から JSON を取得し、バージョン比較・SHA-256 検証・MSI ダウンロード・インストールを実行する。
JSON 形式: {"version": "1.0.1", "url": "https://.../WonderLinko.msi", "sha256": "..."}

MSI は「ファイル使用中」を避けるため、msiexec でインストーラーを起動したら自プロセスを即終了する。
"""
import hashlib
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time

try:
    import requests
except ImportError:
    requests = None


def _log(msg: str):
    """ログに確実に残す（別スレッドから呼ばれるため app_log.log_info を使用）。"""
    try:
        from core.app_log import log_info

        log_info(msg)
    except Exception:
        pass


def _version_tuple(version_str: str) -> tuple:
    """バージョン文字列を比較用タプルに変換。例: "1.0.1" -> (1, 0, 1)。"""
    if not version_str or not isinstance(version_str, str):
        return (0, 0, 0)
    parts = re.sub(r"[^0-9.]", "", version_str).strip(".").split(".") or ["0"]
    try:
        return tuple(int(x) for x in parts[:4])
    except ValueError:
        return (0, 0, 0)


def is_newer(latest: str, current: str) -> bool:
    """latest が current より新しければ True。"""
    return _version_tuple(latest) > _version_tuple(current)


def check_for_update(current_version: str, check_url: str, timeout: int = 10):
    """
    更新チェック用 URL に GET し、新しいバージョンがあればその情報を返す。
    戻り値: (has_update: bool, latest_version: str, download_url: str, expected_sha256: str)
    """
    log = logging.getLogger("WonderLinko")
    if not check_url or not (check_url := check_url.strip()):
        log.info("更新チェック: URL が空のためスキップ")
        return False, "", "", ""
    if not requests:
        log.warning("更新チェック: requests が利用できないためスキップ")
        return False, "", "", ""
    try:
        from core.config_loader import load_config
        from core.security import validate_msi_download_url, validate_update_check_url

        cfg = load_config()
        ok, err = validate_update_check_url(check_url, cfg)
        if not ok:
            log.warning("更新チェック: URL 拒否: %s", err)
            _log(f"更新チェック URL 拒否: {err}")
            return False, "", "", ""
        _log(f"更新チェック GET 実行: {check_url}")
        log.info("更新チェック GET: %s", check_url)
        r = requests.get(check_url, timeout=timeout)
        log.info("更新チェック 応答: status=%s", r.status_code)
        r.raise_for_status()
        data = r.json()
        latest = (data.get("version") or "").strip()
        url = (data.get("url") or "").strip()
        expected_sha256 = (data.get("sha256") or "").strip().lower()

        if not latest or not url:
            log.info("更新チェック: version または url が空のためスキップ")
            return False, "", "", ""
        ok_dl, err_dl = validate_msi_download_url(url, cfg)
        if not ok_dl:
            log.warning("更新チェック: ダウンロード URL 拒否: %s", err_dl)
            _log(f"更新 DL URL 拒否: {err_dl}")
            return False, "", "", ""
        if is_newer(latest, current_version):
            log.info(
                "更新あり: 現在=%s 最新=%s url=%s sha256=%s",
                current_version,
                latest,
                url,
                expected_sha256,
            )
            return True, latest, url, expected_sha256
        log.info("更新なし: 現在=%s 最新=%s", current_version, latest)
        return False, latest, "", expected_sha256
    except Exception as e:
        log.exception("更新チェック エラー: %s", e)
        return False, "", "", ""


def _find_wonderlinko_product_codes():
    """レジストリの Uninstall キーから WonderLinko の ProductCode ({GUID}) を全部集める。"""
    codes = []
    try:
        import winreg
    except Exception:
        return codes
    roots = [
        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
    ]
    for root, path in roots:
        try:
            key = winreg.OpenKey(root, path)
        except OSError:
            continue
        try:
            count = winreg.QueryInfoKey(key)[0]
            for i in range(count):
                try:
                    sub = winreg.EnumKey(key, i)
                except OSError:
                    break
                if not sub.startswith("{"):
                    continue
                try:
                    sk = winreg.OpenKey(key, sub)
                    name = winreg.QueryValueEx(sk, "DisplayName")[0]
                    sk.Close()
                except OSError:
                    continue
                if name and ("WonderLinko" in name or "Wonder Linko" in name):
                    if sub not in codes:
                        codes.append(sub)
        finally:
            try:
                key.Close()
            except Exception:
                pass
    return codes


def download_and_install(
    download_url: str, expected_sha256: str = "", timeout: int = 120
):
    """
    MSI をダウンロードし、SHA-256 検証後に更新バッチ経由でインストール → アプリ再起動する。
    """
    if not download_url or not (download_url := download_url.strip()):
        return False, "URL が空です"
    if not requests:
        return False, "requests が利用できません"
    if sys.platform != "win32":
        return False, "Windows のみ対応しています"

    try:
        from core.config_loader import load_config
        from core.security import validate_msi_download_url

        cfg = load_config()
        ok, err = validate_msi_download_url(download_url, cfg)
        if not ok:
            return False, f"ダウンロード URL が許可されていません: {err}"
        _log(f"更新 DL 開始: {download_url}")
        r = requests.get(download_url, timeout=timeout, stream=True)
        r.raise_for_status()

        msi_path = os.path.join(
            tempfile.gettempdir(), f"WonderLinko_update_{int(time.time())}.msi"
        )
        hasher = hashlib.sha256()
        size = 0
        with open(msi_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    hasher.update(chunk)
                    size += len(chunk)

        _log(f"更新 DL 完了: {msi_path} ({size} bytes)")
        if size < 1_000_000:
            try:
                os.unlink(msi_path)
            except Exception:
                pass
            return False, f"ダウンロードした MSI が小さすぎます ({size} bytes)"

        # SHA-256 の整合性検証
        actual_sha256 = hasher.hexdigest().lower()
        if expected_sha256:
            if actual_sha256 != expected_sha256.lower():
                _log(
                    f"MSI ハッシュ不一致: expected={expected_sha256}, actual={actual_sha256}"
                )
                try:
                    os.unlink(msi_path)
                except Exception:
                    pass
                return False, "ファイルの完全性検証に失敗しました (SHA-256 不一致)"
            _log("MSI ハッシュ検証成功 (SHA-256 一致)")
        else:
            _log(
                "警告: latest.json に sha256 が定義されていないため、ハッシュ検証をスキップしました"
            )

        tmp = tempfile.gettempdir()
        install_log = os.path.join(tmp, "WonderLinko_install.log")
        trace_log = os.path.join(tmp, "WonderLinko_update_trace.log")
        exe = sys.executable
        pid = os.getpid()

        product_codes = _find_wonderlinko_product_codes()
        _log(f"既存製品 ProductCode: {product_codes}")
        if product_codes:
            uninstall_block = "\n".join(
                f'echo [update] uninstall {c} >> "{trace_log}"\n'
                f"start /wait msiexec /x {c} /qn /norestart"
                for c in product_codes
            )
        else:
            uninstall_block = (
                f'echo [update] no existing product found >> "{trace_log}"'
            )

        program_files_exe = os.path.join(
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            "WonderLink",
            "WonderLinko",
            "WonderLinko.exe",
        )

        bat_path = os.path.join(tmp, "wonderlinko_update.bat")
        bat = f"""@echo off
chcp 65001 >nul
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
echo [update] started %DATE% %TIME% >> "{trace_log}"
echo [update] waiting for PID {pid} >> "{trace_log}"
set WL_WAIT=0
:waitloop
tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul
if errorlevel 1 goto afterwait
set /a WL_WAIT+=1
if %WL_WAIT% GEQ 20 (
  echo [update] timeout - force killing PID {pid} >> "{trace_log}"
  taskkill /F /PID {pid} >nul 2>&1
  ping -n 3 127.0.0.1 >nul
  goto afterwait
)
ping -n 2 127.0.0.1 >nul
goto waitloop
:afterwait
echo [update] uninstalling old products >> "{trace_log}"
{uninstall_block}
echo [update] installing new msi >> "{trace_log}"
start /wait msiexec /i "{msi_path}" /passive /norestart /l*v "{install_log}"
echo [update] msiexec exit=%errorlevel% >> "{trace_log}"
echo [update] launching app >> "{trace_log}"
if exist "{program_files_exe}" (
  start "" "{program_files_exe}"
) else (
  start "" "{exe}"
)
echo [update] done >> "{trace_log}"
del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(bat)

        CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
        subprocess.Popen(
            ["cmd.exe", "/c", f'chcp 65001>nul & call "{bat_path}"'],
            creationflags=CREATE_NEW_CONSOLE,
            close_fds=True,
            cwd=tmp,
        )
        _log(
            f"更新バッチを起動: {bat_path} (trace: {trace_log}, install: {install_log})。アプリを終了します。"
        )
        time.sleep(0.5)
        os._exit(0)

    except requests.exceptions.RequestException as e:
        return False, f"ダウンロードに失敗しました: {str(e)[:80]}"
    except Exception as e:
        return False, str(e)[:80]


def check_and_notify(current_version: str, check_url: str, on_result):
    """
    バックグラウンドで更新チェックし、結果を on_result(has_update, latest_version, download_url, expected_sha256) でコールバックする。
    旧仕様の3引数コールバックに対しても後方互換でフォールバック呼び出しを行う。
    """

    def run():
        _log("更新チェック バックグラウンドスレッド開始")
        result = check_for_update(current_version, check_url)
        try:
            on_result(*result)
        except TypeError:
            # 3引数コールバック (has_update, latest, download_url) への後方互換対応
            try:
                on_result(result[0], result[1], result[2])
            except Exception:
                pass
        except Exception:
            pass

    t = threading.Thread(target=run, daemon=True)
    t.start()
