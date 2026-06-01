# -*- coding: utf-8 -*-
"""外向き URL の検証（許可ホスト・スキーム）と安全なブラウザ起動。

config.json の改ざんや Socket.IO 由来の click_url により、社外へデータや
ブラウザを誘導されないよう、HTTP(S) 先をホワイトリストで制限する。

無効化 (開発のみ): 環境変数 ``WLINKO_DISABLE_URL_ALLOWLIST=1``
追加ホスト: ``WLINKO_EXTRA_ALLOWED_HOSTS=172.16.1.251,dev.example.com``
または config.json の ``security.allowed_hosts`` / ``security.allowed_host_suffixes``
"""
from __future__ import annotations

import ipaddress
import os
import re
import webbrowser
from typing import Optional, Tuple
from urllib.parse import urlparse

# 本番デフォルト: 社内 FQDN サフィックス + ローカル開発
_DEFAULT_HOST_SUFFIXES = (
    ".internal.wonder-link.com",
)
_DEFAULT_EXACT_HOSTS = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
})

# load_config / save_config で検証する URL 系キー
URL_CONFIG_KEYS = (
    "ai_board_url",
    "postit_board_url",
    "mini_port_api_url",
    "mini_port_taskboard_url",
    "update_check_url",
    "board_system_url",
    "linko_server_url",
)

_ALLOWLIST_DISABLED = os.environ.get("WLINKO_DISABLE_URL_ALLOWLIST", "").strip().lower() in (
    "1", "true", "yes",
)


def allowlist_enabled() -> bool:
    return not _ALLOWLIST_DISABLED


def _security_section(cfg: Optional[dict]) -> dict:
    if not cfg:
        return {}
    sec = cfg.get("security")
    return sec if isinstance(sec, dict) else {}


def _extra_hosts_from_env() -> frozenset[str]:
    raw = (os.environ.get("WLINKO_EXTRA_ALLOWED_HOSTS") or "").strip()
    if not raw:
        return frozenset()
    return frozenset(h.strip().lower() for h in raw.split(",") if h.strip())


def allowed_host_suffixes(cfg: Optional[dict] = None) -> Tuple[str, ...]:
    sec = _security_section(cfg)
    custom = sec.get("allowed_host_suffixes")
    if isinstance(custom, list) and custom:
        return tuple(str(s).strip() for s in custom if str(s).strip())
    return _DEFAULT_HOST_SUFFIXES


def allowed_exact_hosts(cfg: Optional[dict] = None) -> frozenset[str]:
    sec = _security_section(cfg)
    hosts = set(h.lower() for h in _DEFAULT_EXACT_HOSTS)
    hosts |= _extra_hosts_from_env()
    custom = sec.get("allowed_hosts")
    if isinstance(custom, list):
        for h in custom:
            if str(h).strip():
                hosts.add(str(h).strip().lower())
    return frozenset(hosts)


def allow_private_ips(cfg: Optional[dict] = None) -> bool:
    sec = _security_section(cfg)
    if sec.get("allow_private_ips") is True:
        return True
    return os.environ.get("WLINKO_ALLOW_PRIVATE_IPS", "").strip().lower() in (
        "1", "true", "yes",
    )


def _is_loopback(hostname: str) -> bool:
    h = hostname.lower()
    if h in ("localhost", "::1"):
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def _is_private_ip(hostname: str) -> bool:
    try:
        addr = ipaddress.ip_address(hostname)
        return addr.is_private or addr.is_link_local
    except ValueError:
        return False


def is_host_allowed(hostname: str, cfg: Optional[dict] = None) -> bool:
    """ホスト名が許可リストに含まれるか。"""
    if not allowlist_enabled():
        return True
    if not hostname:
        return False
    h = hostname.lower().rstrip(".")
    if h in allowed_exact_hosts(cfg):
        return True
    for suffix in allowed_host_suffixes(cfg):
        s = suffix.lower()
        if not s.startswith("."):
            s = "." + s
        if h == s[1:] or h.endswith(s):
            return True
    if allow_private_ips(cfg) and _is_private_ip(h):
        return True
    if _is_loopback(h):
        return True
    return False


def validate_http_url(
    url: str,
    cfg: Optional[dict] = None,
    *,
    require_https: bool = False,
    purpose: str = "request",
) -> Tuple[bool, str]:
    """HTTP(S) URL を検証。戻り値: (ok, error_message)。"""
    if not url or not isinstance(url, str):
        return False, "URL が空です"
    url = url.strip()
    if not allowlist_enabled():
        return True, ""

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "URL の解析に失敗しました"

    if parsed.scheme not in ("http", "https"):
        return False, f"許可されていないスキームです: {parsed.scheme!r}"

    if parsed.username or parsed.password:
        return False, "認証情報付き URL は許可されていません"

    hostname = (parsed.hostname or "").strip()
    if not hostname:
        return False, "ホスト名がありません"

    if require_https and parsed.scheme != "https" and not _is_loopback(hostname):
        return False, "HTTPS が必要です"

    if parsed.scheme == "http" and not _is_loopback(hostname) and not allow_private_ips(cfg):
        # 社外・社内ホスト名への平文 HTTP は禁止 (ループバックと明示的 private 許可時のみ http 可)
        if not _is_private_ip(hostname):
            return False, "HTTP は localhost のみ許可されています (HTTPS を使用してください)"

    if not is_host_allowed(hostname, cfg):
        return False, (
            f"許可されていないホストです: {hostname!r} "
            f"(purpose={purpose})"
        )

    return True, ""


def validate_update_check_url(url: str, cfg: Optional[dict] = None) -> Tuple[bool, str]:
    ok, err = validate_http_url(url, cfg, require_https=True, purpose="update_check")
    if not ok:
        return ok, err
    path = (urlparse(url).path or "").lower()
    if not path.endswith(".json"):
        return False, "更新チェック URL は .json を指す必要があります"
    return True, ""


def validate_msi_download_url(url: str, cfg: Optional[dict] = None) -> Tuple[bool, str]:
    ok, err = validate_http_url(url, cfg, require_https=True, purpose="msi_download")
    if not ok:
        return ok, err
    path = (urlparse(url).path or "").lower()
    if not path.endswith(".msi"):
        return False, "更新ダウンロード URL は .msi を指す必要があります"
    return True, ""


def validate_personal_board_id(personal_id: str) -> bool:
    """パーソナル board ID の path インジェクション防止。"""
    if not personal_id:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{1,128}", personal_id))


def sanitize_config_urls(cfg: dict, defaults: dict) -> dict:
    """設定内の URL を検証し、不正なら defaults に戻す。cfg をその場で更新。"""
    if not allowlist_enabled():
        return cfg
    for key in URL_CONFIG_KEYS:
        val = cfg.get(key)
        if not val or not isinstance(val, str):
            continue
        require_https = key in ("update_check_url",)
        ok, err = validate_http_url(
            val.strip(),
            cfg,
            require_https=require_https,
            purpose=f"config:{key}",
        )
        if not ok:
            fallback = defaults.get(key, "")
            try:
                from app_log import log_warn
                log_warn(f"[security] config {key} を拒否: {err} → デフォルトに復元")
            except Exception:
                print(f"[security] config {key} rejected: {err}", flush=True)
            cfg[key] = fallback
    return cfg


def assert_http_url(url: str, cfg: Optional[dict] = None, **kwargs) -> None:
    """検証失敗時に ValueError。"""
    ok, err = validate_http_url(url, cfg, **kwargs)
    if not ok:
        raise ValueError(err)


def safe_webbrowser_open(url: str, cfg: Optional[dict] = None) -> bool:
    """許可された URL のみ既定ブラウザで開く。戻り値: 開いたら True。"""
    if not url:
        return False
    ok, err = validate_http_url(url, cfg, purpose="browser")
    if not ok:
        try:
            from app_log import log_warn
            log_warn(f"[security] ブラウザ起動を拒否: {err} url={url[:120]!r}")
        except Exception:
            print(f"[security] browser blocked: {err}", flush=True)
        return False
    webbrowser.open(url)
    return True


def filter_allowed_url(url: Optional[str], cfg: Optional[dict] = None, **kwargs) -> Optional[str]:
    """許可された URL ならそのまま返し、否则 None。"""
    if not url:
        return None
    ok, _ = validate_http_url(url, cfg, **kwargs)
    return url if ok else None
