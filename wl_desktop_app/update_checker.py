# -*- coding: utf-8 -*-
"""
自動更新: 更新チェック用 URL から JSON を取得し、バージョン比較・MSI ダウンロード・インストールを実行する。
JSON 形式: {"version": "1.0.1", "url": "https://.../WonderLinko.msi"}
"""
import os
import re
import sys
import tempfile
import threading

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
    if not check_url or not (check_url := check_url.strip()):
        return False, "", ""
    if not requests:
        return False, "", ""
    try:
        r = requests.get(check_url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        latest = (data.get("version") or "").strip()
        url = (data.get("url") or "").strip()
        if not latest or not url:
            return False, "", ""
        if is_newer(latest, current_version):
            return True, latest, url
        return False, latest, ""
    except Exception:
        return False, "", ""


def download_and_install(download_url: str, timeout: int = 120):
    """
    MSI をダウンロードし、インストーラーを起動する。
    戻り値: (success: bool, message: str)
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
            with os.fdopen(fd, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            # インストーラーを起動（既存のアプリはユーザーが終了するか、MSI が促す）
            os.startfile(path)
            return True, ""
        except Exception:
            try:
                os.unlink(path)
            except Exception:
                pass
            raise
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
