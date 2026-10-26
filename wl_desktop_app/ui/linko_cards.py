# -*- coding: utf-8 -*-
"""リン子カード・コレクション（PoC）への深いリンク。"""
from __future__ import annotations

from urllib.parse import quote_plus


def build_linko_cards_url(cfg: dict | None) -> str:
    """``{linko_server_url}/entrance/me/cards?email=...`` を組み立てる。

    個人キーは Board ログインのメール（``board_system_email``）を正とする。
    メールが無いときだけ互換で face_registry_person_id / display_name を使う。
    """
    cfg = cfg or {}
    base = (cfg.get("linko_server_url") or "").strip().rstrip("/")
    if not base:
        base = (cfg.get("ai_board_url") or "http://127.0.0.1:5000").rstrip("/")
    path = "/entrance/me/cards"
    email = (cfg.get("board_system_email") or "").strip()
    if email and "@" in email and " " not in email:
        return f"{base}{path}?email={quote_plus(email)}"
    emp = (cfg.get("face_registry_person_id") or "").strip() or (
        cfg.get("display_name") or ""
    ).strip()
    if emp:
        return f"{base}{path}?employee_id={quote_plus(emp)}"
    return f"{base}{path}"
