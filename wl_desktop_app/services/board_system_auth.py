# -*- coding: utf-8 -*-
"""Board System の認証・ユーザー解決を一元管理するモジュール。

app.py / ui/mini_port.py など複数個所で重複していた「メールアドレス →
user_id 解決 → config 保存」フローをここに集約する。
"""
from __future__ import annotations

from typing import Optional

import requests

from core.config_loader import (
    get_board_system_personal_url,
    get_effective_board_system_url,
    load_config,
    save_board_system_login,
)
from core.security import assert_http_url


class BoardSystemAuthError(Exception):
    """Board System 認証中に発生したエラー。"""


def resolve_user_by_email(
    email: str,
    board_url: str,
    cfg: dict,
    *,
    timeout: int = 10,
) -> dict:
    """メールアドレスから Board System のユーザー情報を取得する。

    Args:
        email:     登録済みメールアドレス。
        board_url: Board System の API ベース URL（末尾スラッシュなし）。
        cfg:       現在の設定 dict（セキュリティ検証に使用）。
        timeout:   HTTP タイムアウト秒数。

    Returns:
        ユーザー情報の dict（少なくとも ``id`` キーを持つ）。

    Raises:
        BoardSystemAuthError: ユーザーが見つからない・接続エラーの場合。
    """
    endpoint = f"{board_url}/users/by_email"
    try:
        assert_http_url(endpoint, cfg, purpose="users_by_email")
    except ValueError as e:
        raise BoardSystemAuthError(f"送信先が許可されていません: {e}") from e

    try:
        r = requests.get(endpoint, params={"email": email}, timeout=timeout)
    except requests.RequestException as e:
        raise BoardSystemAuthError(f"接続エラー: {str(e)[:80]}") from e

    if r.status_code == 404:
        raise BoardSystemAuthError(
            "このメールアドレスは未登録です。Board System でユーザーを登録してください。"
        )
    if r.status_code != 200:
        raise BoardSystemAuthError(
            f"ログインに失敗しました（HTTP {r.status_code}）。"
            "Board System の URL とネットワークを確認してください。"
        )

    try:
        data = r.json()
    except Exception as e:
        raise BoardSystemAuthError(f"レスポンスの解析に失敗しました: {e}") from e

    if not isinstance(data, dict) or data.get("id") is None:
        raise BoardSystemAuthError(
            "ログインに失敗しました。Board System の URL とネットワークを確認してください。"
        )

    return data


def login_with_email(
    email: str,
    cfg: Optional[dict] = None,
    *,
    timeout: int = 10,
) -> tuple[bool, str, Optional[str]]:
    """メールアドレスで Board System にログインし、config を更新する。

    Args:
        email:   登録済みメールアドレス。
        cfg:     現在の設定 dict。None の場合は load_config() を呼ぶ。
        timeout: HTTP タイムアウト秒数。

    Returns:
        ``(success, message, personal_url)`` のタプル。
        - success:      成功時 True。
        - message:      ユーザー向けメッセージ文字列。
        - personal_url: 成功時はパーソナルボードの URL（失敗時は None）。
    """
    if cfg is None:
        cfg = load_config()

    board_url = (get_effective_board_system_url(cfg) or "").rstrip("/")
    if not board_url:
        return (
            False,
            "Board System の URL が設定されていません。"
            "config.json の board_system_url または環境変数 BOARD_SYSTEM_URL を設定してください。",
            None,
        )

    if not email or "@" not in email:
        return False, "メールアドレスを入力してください。", None

    try:
        data = resolve_user_by_email(email.strip(), board_url, cfg, timeout=timeout)
    except BoardSystemAuthError as e:
        return False, str(e), None

    user_id = data["id"]
    save_board_system_login(
        cfg,
        board_url=board_url,
        user_id=user_id,
        user_data=data,
        login_email=email.strip(),
    )
    personal_url = get_board_system_personal_url(cfg)
    name = (data.get("call_name") or data.get("name") or "").strip()
    msg = f"ログインしました（{name}）。パーソナルボードを開きます。" if name else "ログインしました。"
    return True, msg, personal_url
