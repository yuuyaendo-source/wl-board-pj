# -*- coding: utf-8 -*-
"""linko-system の face_registry 管理 API クライアント（管理者デスクトップ用）。"""
from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

try:
    import requests
except ImportError:
    requests = None  # type: ignore


class FaceRegistryError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def _api_root(cfg: dict) -> str:
    base = (cfg.get("linko_server_url") or "").strip().rstrip("/")
    if not base:
        raise FaceRegistryError("linko_server_url が未設定です")
    return f"{base}/api/face_registry"


def _admin_headers(cfg: dict) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    token = (cfg.get("linko_admin_token") or "").strip()
    if token:
        headers["X-Linko-Admin-Token"] = token
    return headers


def _request(
    cfg: dict,
    method: str,
    path: str = "",
    *,
    json_body: Optional[dict] = None,
    timeout: int = 30,
) -> Any:
    if requests is None:
        raise FaceRegistryError("requests が利用できません")
    url = _api_root(cfg) + path
    try:
        from security import validate_http_url

        ok, err = validate_http_url(url, cfg, purpose="face_registry")
        if not ok:
            raise FaceRegistryError(err or "URL が許可されていません")
    except FaceRegistryError:
        raise
    except Exception as e:
        raise FaceRegistryError(f"URL 検証エラー: {e}") from e

    try:
        r = requests.request(
            method,
            url,
            headers={**_admin_headers(cfg), "Content-Type": "application/json"} if json_body is not None else _admin_headers(cfg),
            json=json_body,
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise FaceRegistryError(f"通信エラー: {e}") from e

    if r.status_code == 401:
        raise FaceRegistryError("認証に失敗しました（linko_admin_token を確認）", 401)
    if r.status_code == 403:
        raise FaceRegistryError("アクセスが拒否されました（社内 LAN / VPN または管理者トークン）", 403)
    if r.status_code == 409:
        raise FaceRegistryError("メールアドレスが既に登録されています", 409)
    if r.status_code == 404:
        raise FaceRegistryError("対象が見つかりません", 404)
    if r.status_code >= 400:
        try:
            detail = (r.json() or {}).get("error") or r.text[:200]
        except Exception:
            detail = r.text[:200]
        raise FaceRegistryError(detail or f"HTTP {r.status_code}", r.status_code)

    if not r.content:
        return {}
    try:
        return r.json()
    except Exception:
        return {}


def list_registry(cfg: dict) -> dict:
    """一覧 + embeddings_key（照合データ表示用）。"""
    data = _request(cfg, "GET")
    if not isinstance(data, dict):
        return {"persons": [], "embeddings_key": "face_embeddings"}
    persons = data.get("persons")
    return {
        "persons": list(persons) if isinstance(persons, list) else [],
        "embeddings_key": str(data.get("embeddings_key") or "face_embeddings"),
    }


def list_persons(cfg: dict) -> list[dict]:
    return list_registry(cfg).get("persons") or []


def get_person(cfg: dict, person_id: str) -> dict:
    data = _request(cfg, "GET", f"/{quote(str(person_id), safe='')}")
    return data if isinstance(data, dict) else {}


def embedding_count_for_person(person: dict, embeddings_key: str) -> int:
    if embeddings_key == "face_embeddings_v2":
        return int(person.get("face_embeddings_v2_count") or 0)
    return int(person.get("face_embeddings_count") or 0)


def upload_faces_serial(cfg: dict, person_id: str, face_data_urls: list[str]) -> tuple[int, int, Optional[str]]:
    """data URL を直列で PUT。戻り値: (成功枚数, 合計, 失敗時メッセージ)。"""
    total = len(face_data_urls)
    ok = 0
    last_err: Optional[str] = None
    for url in face_data_urls:
        if not url:
            continue
        for attempt in range(2):
            try:
                update_face(cfg, person_id, url)
                ok += 1
                last_err = None
                break
            except FaceRegistryError as e:
                last_err = str(e)
                if attempt == 0:
                    continue
                return ok, total, last_err
    return ok, total, last_err


def create_person(
    cfg: dict,
    *,
    name: str,
    email: str,
    call_name: str = "",
    call_name_kana: str = "",
    department: str = "",
    is_staff: bool = True,
) -> dict:
    body = {
        "name": name.strip(),
        "email": email.strip(),
        "call_name": call_name.strip(),
        "call_name_kana": call_name_kana.strip(),
        "department": department.strip(),
        "is_staff": bool(is_staff),
    }
    return _request(cfg, "POST", json_body=body)


def update_person(
    cfg: dict,
    person_id: str,
    *,
    name: Optional[str] = None,
    email: Optional[str] = None,
    call_name: Optional[str] = None,
    call_name_kana: Optional[str] = None,
    department: Optional[str] = None,
    is_staff: Optional[bool] = None,
) -> dict:
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name.strip()
    if email is not None:
        body["email"] = email.strip()
    if call_name is not None:
        body["call_name"] = call_name.strip()
    if call_name_kana is not None:
        body["call_name_kana"] = call_name_kana.strip()
    if department is not None:
        body["department"] = department.strip()
    if is_staff is not None:
        body["is_staff"] = bool(is_staff)
    return _request(cfg, "PATCH", f"/{quote(str(person_id), safe='')}", json_body=body)


def update_face(cfg: dict, person_id: str, face_data_url: str) -> None:
    _request(
        cfg,
        "PUT",
        f"/{quote(str(person_id), safe='')}",
        json_body={"faceData": face_data_url},
        timeout=60,
    )


def delete_face(cfg: dict, person_id: str) -> None:
    _request(cfg, "DELETE", f"/{quote(str(person_id), safe='')}/face")


def delete_voice(cfg: dict, person_id: str) -> None:
    _request(cfg, "DELETE", f"/{quote(str(person_id), safe='')}/voice")


def fetch_face_image_bytes(cfg: dict, person_id: str) -> bytes:
    if requests is None:
        raise FaceRegistryError("requests が利用できません")
    url = face_image_url(cfg, person_id)
    try:
        from security import validate_http_url

        ok, err = validate_http_url(url, cfg, purpose="face_registry")
        if not ok:
            raise FaceRegistryError(err or "URL が許可されていません")
    except FaceRegistryError:
        raise
    except Exception as e:
        raise FaceRegistryError(f"URL 検証エラー: {e}") from e
    try:
        r = requests.get(url, headers=_admin_headers(cfg), timeout=30)
    except requests.RequestException as e:
        raise FaceRegistryError(f"通信エラー: {e}") from e
    if r.status_code == 404:
        raise FaceRegistryError("顔画像が登録されていません", 404)
    if r.status_code >= 400:
        raise FaceRegistryError(f"取得に失敗しました (HTTP {r.status_code})", r.status_code)
    return bytes(r.content)


def fetch_voice_audio_bytes(cfg: dict, person_id: str) -> bytes:
    if requests is None:
        raise FaceRegistryError("requests が利用できません")
    url = f"{_api_root(cfg)}/{quote(str(person_id), safe='')}/voice"
    try:
        from security import validate_http_url

        ok, err = validate_http_url(url, cfg, purpose="face_registry")
        if not ok:
            raise FaceRegistryError(err or "URL が許可されていません")
    except FaceRegistryError:
        raise
    except Exception as e:
        raise FaceRegistryError(f"URL 検証エラー: {e}") from e
    try:
        r = requests.get(url, headers=_admin_headers(cfg), timeout=30)
    except requests.RequestException as e:
        raise FaceRegistryError(f"通信エラー: {e}") from e
    if r.status_code == 404:
        raise FaceRegistryError("音声が登録されていません", 404)
    if r.status_code >= 400:
        raise FaceRegistryError(f"取得に失敗しました (HTTP {r.status_code})", r.status_code)
    return bytes(r.content)


def update_voice(cfg: dict, person_id: str, voice_data_url: str) -> None:
    """音声サンプル（WAV data URL）を登録。将来の話者照合用。"""
    _request(
        cfg,
        "PUT",
        f"/{quote(str(person_id), safe='')}/voice",
        json_body={"voiceData": voice_data_url},
        timeout=60,
    )


def delete_person(cfg: dict, person_id: str) -> None:
    _request(cfg, "DELETE", f"/{quote(str(person_id), safe='')}")


def face_image_url(cfg: dict, person_id: str) -> str:
    return f"{_api_root(cfg)}/{quote(str(person_id), safe='')}/face"


def workspace_directory_sync(cfg: dict) -> dict:
    base = (cfg.get("linko_server_url") or "").strip().rstrip("/")
    if not base:
        raise FaceRegistryError("linko_server_url が未設定です")
    url = f"{base}/api/workspace/directory_sync"
    if requests is None:
        raise FaceRegistryError("requests が利用できません")
    try:
        from security import validate_http_url

        ok, err = validate_http_url(url, cfg, purpose="workspace_sync")
        if not ok:
            raise FaceRegistryError(err or "URL が許可されていません")
    except FaceRegistryError:
        raise
    except Exception as e:
        raise FaceRegistryError(f"URL 検証エラー: {e}") from e
    try:
        r = requests.post(url, headers=_admin_headers(cfg), timeout=120)
    except requests.RequestException as e:
        raise FaceRegistryError(f"通信エラー: {e}") from e
    if r.status_code in (401, 403):
        raise FaceRegistryError("Workspace 同期の認証に失敗しました", r.status_code)
    try:
        return r.json() if r.content else {}
    except Exception:
        return {"ok": False, "error": r.text[:200]}


def is_admin_configured(cfg: dict) -> bool:
    """管理機能を使う最低条件（URL 設定済み）。"""
    return bool((cfg.get("linko_server_url") or "").strip())
