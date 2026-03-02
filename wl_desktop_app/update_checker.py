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

try:
    import requests
except ImportError:
    requests = None


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
    MSI をダウンロードし、msiexec でインストールを開始して、自プロセスを終了する。
    成功時は sys.exit(0) で即終了するため戻り値は返らない。失敗時のみ (False, message) を返す。
    """
    if not download_url or not (download_url := download_url.strip()):
        return False, "URL が空です"
    if not requests:
        return False, "requests が利用できません"
    if sys.platform != "win32":
        return False, "Windows のみ対応しています"

    try:
        r = requests.get(download_url, timeout=timeout, stream=True)
        r.raise_for_status()

        fd, path = tempfile.mkstemp(suffix=".msi")
        try:
            os.close(fd)
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
        except Exception:
            try:
                os.unlink(path)
            except Exception:
                pass
            raise

        # msiexec: /i インストール, /passive 進行状況のみで自動進行, /norestart 再起動しない
        cmd = ["msiexec.exe", "/i", path, "/passive", "/norestart"]
        subprocess.Popen(cmd)

        # ファイルロックを解放するため、自プロセスを即終了する
        sys.exit(0)

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
        result = check_for_update(current_version, check_url)
        try:
            on_result(*result)
        except Exception:
            pass

    t = threading.Thread(target=run, daemon=True)
    t.start()
