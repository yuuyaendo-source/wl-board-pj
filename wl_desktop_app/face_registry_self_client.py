# -*- coding: utf-8 -*-
"""linko-system 顔セルフ登録 API クライアント（一般社員 PC 用）。"""
from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

try:
    import requests
except ImportError:
    requests = None  # type: ignore


class FaceSelfRegisterError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def _api_root(cfg: dict) -> str:
    base = (cfg.get("linko_server_url") or "").strip().rstrip("/")
    if not base:
        raise FaceSelfRegisterError("linko_server_url が未設定です")
    return f"{base}/api/face_registry"


def _headers(token: Optional[str] = None) -> dict[str, str]:
    h = {"Accept": "application/json"}
    if token:
        h["X-Linko-Self-Register-Token"] = token
    return h


def _request(
    cfg: dict,
    method: str,
    path: str,
    *,
    json_body: Optional[dict] = None,
    token: Optional[str] = None,
    params: Optional[dict] = None,
    timeout: int = 30,
) -> Any:
    if requests is None:
        raise FaceSelfRegisterError("requests が利用できません")
    url = _api_root(cfg) + path
    try:
        from security import validate_http_url

        ok, err = validate_http_url(url, cfg, purpose="face_registry")
        if not ok:
            raise FaceSelfRegisterError(err or "URL が許可されていません")
    except FaceSelfRegisterError:
        raise
    except Exception as e:
        raise FaceSelfRegisterError(f"URL 検証エラー: {e}") from e

    headers = dict(_headers(token))
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    try:
        r = requests.request(
            method,
            url,
            headers=headers,
            json=json_body,
            params=params,
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise FaceSelfRegisterError(f"通信エラー: {e}") from e

    if r.status_code == 403:
        raise FaceSelfRegisterError(
            "アクセスが拒否されました（社内 LAN / VPN を確認）", 403
        )
    if r.status_code == 401:
        raise FaceSelfRegisterError(
            "認証の有効期限が切れました。最初からやり直してください。", 401
        )
    if r.status_code == 429:
        raise FaceSelfRegisterError(
            "確認コードの試行回数が上限に達しました。しばらく待って再試行してください。",
            429,
        )
    if r.status_code == 503:
        try:
            detail = (r.json() or {}).get("error") or r.text[:200]
        except Exception:
            detail = r.text[:200]
        raise FaceSelfRegisterError(detail or "サーバでセルフ登録が利用できません", 503)
    if r.status_code >= 400:
        try:
            data = r.json() or {}
            detail = data.get("error") or data.get("message") or r.text[:200]
        except Exception:
            detail = r.text[:200]
        raise FaceSelfRegisterError(detail or f"HTTP {r.status_code}", r.status_code)

    if not r.content:
        return {}
    try:
        return r.json()
    except Exception:
        return {}


def get_self_register_status(cfg: dict) -> dict:
    data = _request(cfg, "GET", "/self_register/status")
    return data if isinstance(data, dict) else {}


def start_self_register(cfg: dict, email: str) -> dict:
    data = _request(
        cfg, "POST", "/self_register/start", json_body={"email": email.strip()}
    )
    return data if isinstance(data, dict) else {}


def verify_self_register(cfg: dict, challenge_id: str, otp: str) -> dict:
    data = _request(
        cfg,
        "POST",
        "/self_register/verify",
        json_body={"challenge_id": challenge_id, "otp": otp.strip()},
    )
    return data if isinstance(data, dict) else {}


def get_self_profile(cfg: dict, person_id: str, token: str) -> dict:
    """本人の現在プロフィール（呼び名・敬称・読み）を取得。編集フォームのプリフィル用。"""
    data = _request(
        cfg,
        "GET",
        "/self_register/profile",
        token=token,
        params={"person_id": str(person_id)},
    )
    return data if isinstance(data, dict) else {}


def update_self_profile(
    cfg: dict,
    person_id: str,
    token: str,
    *,
    call_name: Optional[str] = None,
    honorific: Optional[str] = None,
    call_name_kana: Optional[str] = None,
) -> dict:
    """本人の呼び名・敬称・読みを更新。渡した項目だけ更新される。"""
    body: dict[str, str] = {"person_id": str(person_id)}
    if call_name is not None:
        body["call_name"] = call_name
    if honorific is not None:
        body["honorific"] = honorific
    if call_name_kana is not None:
        body["call_name_kana"] = call_name_kana
    data = _request(
        cfg,
        "POST",
        "/self_register/profile",
        json_body=body,
        token=token,
    )
    return data if isinstance(data, dict) else {}


def update_face_self(cfg: dict, person_id: str, token: str, face_data_url: str) -> dict:
    pid = quote(str(person_id), safe="")
    data = _request(
        cfg,
        "PUT",
        f"/{pid}",
        json_body={"faceData": face_data_url},
        token=token,
        params={"self_register": "1"},
    )
    return data if isinstance(data, dict) else {}


def upload_faces_self_serial(
    cfg: dict, person_id: str, token: str, face_data_urls: list[str]
) -> tuple[int, int, Optional[str]]:
    total = len(face_data_urls)
    ok = 0
    last_err: Optional[str] = None
    for url in face_data_urls:
        if not url:
            continue
        for attempt in range(2):
            try:
                update_face_self(cfg, person_id, token, url)
                ok += 1
                last_err = None
                break
            except FaceSelfRegisterError as e:
                last_err = str(e)
                if attempt == 0:
                    continue
                return ok, total, last_err
    return ok, total, last_err


def get_voice_challenges(cfg: dict, token: str) -> dict:
    data = _request(cfg, "GET", "/self_register/voice/challenges", token=token)
    return data if isinstance(data, dict) else {}


def update_voice_self(
    cfg: dict,
    person_id: str,
    token: str,
    enroll_session_id: str,
    challenge_id: str,
    voice_data_url: str,
) -> dict:
    pid = quote(str(person_id), safe="")
    data = _request(
        cfg,
        "PUT",
        f"/{pid}/voice",
        json_body={
            "voiceData": voice_data_url,
            "enroll_session_id": enroll_session_id,
            "challenge_id": challenge_id,
        },
        token=token,
        params={"self_register": "1"},
    )
    return data if isinstance(data, dict) else {}


def upload_voices_self_serial(
    cfg: dict,
    person_id: str,
    token: str,
    enroll_session_id: str,
    samples: list[tuple[str, str]],
) -> tuple[int, int, Optional[str]]:
    total = len(samples)
    ok = 0
    last_err: Optional[str] = None
    for challenge_id, data_url in samples:
        if not data_url or not challenge_id:
            continue
        for attempt in range(2):
            try:
                update_voice_self(
                    cfg, person_id, token, enroll_session_id, challenge_id, data_url
                )
                ok += 1
                last_err = None
                break
            except FaceSelfRegisterError as e:
                last_err = str(e)
                if attempt == 0:
                    continue
                return ok, total, last_err
    return ok, total, last_err
