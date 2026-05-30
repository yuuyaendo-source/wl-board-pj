# -*- coding: utf-8 -*-
"""
自動更新: 更新チェック用 URL から JSON を取得し、バージョン比較・MSI ダウンロード・インストールを実行する。
JSON 形式: {"version": "1.0.1", "url": "https://.../WonderLinko.msi"}

MSI は「ファイル使用中」を避けるため、msiexec でインストーラーを起動したら自プロセスを即終了する。
"""
import logging
import os
import re
import sys
import tempfile
import threading
import subprocess
import time

try:
    import requests
except ImportError:
    requests = None


def _log(msg: str):
    """ログに確実に残す（別スレッドから呼ばれるため app_log.log_info を使用）。"""
    try:
        from app_log import log_info
        log_info(msg)
    except Exception:
        pass


def wait_for_network(host: str, interval_sec: int = 5, max_wait_sec: int = 180) -> bool:
    """
    Ping が通るまで待つ。ネットワーク確立後の更新チェック用。
    戻り値: 成功で True、タイムアウトで False。
    """
    if not host or not (host := host.strip()):
        return True
    deadline = time.monotonic() + max_wait_sec
    while time.monotonic() < deadline:
        try:
            if sys.platform == "win32":
                r = subprocess.run(["ping", "-n", "1", host], timeout=5, capture_output=True)
            else:
                r = subprocess.run(["ping", "-c", "1", "-W", "3", host], timeout=5, capture_output=True)
            if r.returncode == 0:
                _log(f"ネットワーク確立: {host} へ Ping 成功")
                return True
        except Exception:
            pass
        time.sleep(interval_sec)
    _log(f"ネットワーク待機タイムアウト: {host} へ {max_wait_sec}秒以内に Ping 不通")
    return False


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
    戻り値: (has_update: bool, latest_version: str, download_url: str)
    """
    log = logging.getLogger("WonderLinko")
    if not check_url or not (check_url := check_url.strip()):
        log.info("更新チェック: URL が空のためスキップ")
        return False, "", ""
    if not requests:
        log.warning("更新チェック: requests が利用できないためスキップ")
        return False, "", ""
    try:
        _log(f"更新チェック GET 実行: {check_url}")
        log.info("更新チェック GET: %s", check_url)
        r = requests.get(check_url, timeout=timeout)
        log.info("更新チェック 応答: status=%s", r.status_code)
        r.raise_for_status()
        data = r.json()
        latest = (data.get("version") or "").strip()
        url = (data.get("url") or "").strip()
        if not latest or not url:
            log.info("更新チェック: version または url が空のためスキップ")
            return False, "", ""
        if is_newer(latest, current_version):
            log.info("更新あり: 現在=%s 最新=%s url=%s", current_version, latest, url)
            return True, latest, url
        log.info("更新なし: 現在=%s 最新=%s", current_version, latest)
        return False, latest, ""
    except Exception as e:
        log.exception("更新チェック エラー: %s", e)
        return False, "", ""


def download_and_install(download_url: str, timeout: int = 120):
    """
    MSI をダウンロードし、更新バッチ経由でインストール → アプリ再起動する。

    旧実装は「自 exe が起動中のまま msiexec を起動」していたため、exe の
    ファイルロックでインストールが完了せず、バージョンが上がらない問題があった。
    本実装は **バッチ経由** で:
      1. 自プロセス (PID) の完全終了を待つ
      2. 旧バージョンを UpgradeCode で検出してサイレントアンインストール
         (cx_Freeze MSI のメジャーアップグレードが効かず製品が並存するのを防ぐ)
      3. 新 MSI をインストール (/l*v で詳細ログを %TEMP% に出力)
      4. 新 exe を起動
    することで確実に上書き更新する。
    成功時は sys.exit(0) で終了。失敗時のみ (False, message) を返す。
    """
    if not download_url or not (download_url := download_url.strip()):
        return False, "URL が空です"
    if not requests:
        return False, "requests が利用できません"
    if sys.platform != "win32":
        return False, "Windows のみ対応しています"

    try:
        _log(f"更新 DL 開始: {download_url}")
        r = requests.get(download_url, timeout=timeout, stream=True)
        r.raise_for_status()

        msi_path = os.path.join(
            tempfile.gettempdir(), f"WonderLinko_update_{int(time.time())}.msi"
        )
        size = 0
        with open(msi_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
        _log(f"更新 DL 完了: {msi_path} ({size} bytes)")
        if size < 1_000_000:
            return False, f"ダウンロードした MSI が小さすぎます ({size} bytes)"

        tmp = tempfile.gettempdir()
        install_log = os.path.join(tmp, "WonderLinko_install.log")
        trace_log = os.path.join(tmp, "WonderLinko_update_trace.log")
        exe = sys.executable
        pid = os.getpid()
        # UpgradeCode (setup.py の bdist_msi_options と一致させること)
        upgrade_code = "{B29E4C50-1A2B-4C3D-9E5F-6A7B8C9D0E1F}"

        bat_path = os.path.join(tmp, "wonderlinko_update.bat")
        # ASCII のみ (日本語は chcp 依存で文字化け・失敗の原因)。各ステップを trace_log に追記。
        bat = f"""@echo off
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
echo [update] uninstalling old (UpgradeCode) >> "{trace_log}"
msiexec /x {upgrade_code} /qn /norestart
echo [update] installing new msi >> "{trace_log}"
msiexec /i "{msi_path}" /passive /norestart /l*v "{install_log}"
echo [update] msiexec exit=%errorlevel% >> "{trace_log}"
echo [update] launching app >> "{trace_log}"
start "" "{exe}"
echo [update] done >> "{trace_log}"
del "%~f0"
"""
        with open(bat_path, "w", encoding="ascii", errors="replace") as f:
            f.write(bat)

        # DETACHED_PROCESS のみ (CREATE_NO_WINDOW と併用すると起動しないことがある)。
        # 親 (このアプリ) が終了してもバッチは独立して走り続ける。
        DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=DETACHED_PROCESS,
            close_fds=True,
            cwd=tmp,
        )
        _log(f"更新バッチを起動: {bat_path} (trace: {trace_log}, install: {install_log})。アプリを終了します。")
        # バッチが waitloop に入る猶予を与えてから終了。
        # 重要: sys.exit(0) は SystemExit を投げるが、Tk / pystray のイベント
        # コールバック内 (設定パネルのボタン・トレイメニュー) では握りつぶされ、
        # プロセスが終了しない → バッチが PID 待ちループから抜けられず更新が止まる。
        # os._exit(0) は例外を投げず即座にプロセスを終了するので確実。
        time.sleep(0.5)
        os._exit(0)

    except requests.exceptions.RequestException as e:
        return False, f"ダウンロードに失敗しました: {str(e)[:80]}"
    except Exception as e:
        return False, str(e)[:80]


def check_and_notify(current_version: str, check_url: str, on_result):
    """
    バックグラウンドで更新チェックし、結果を on_result(has_update, latest_version, download_url) でコールバックする。
    on_result はメインスレッドから呼びたい場合は、呼び出し側で after 等でラップすること。
    """
    def run():
        _log("更新チェック バックグラウンドスレッド開始")
        result = check_for_update(current_version, check_url)
        try:
            on_result(*result)
        except Exception:
            pass

    t = threading.Thread(target=run, daemon=True)
    t.start()
