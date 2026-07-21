# -*- coding: utf-8 -*-
"""リン子カード・コレクション（PoC）への深いリンク。"""
from __future__ import annotations

from urllib.parse import quote_plus


def build_linko_cards_url(cfg: dict | None) -> str:
    """``{linko_server_url}/entrance/me/cards?employee_id=...`` を組み立てる。

    employee_id は face_registry_person_id → display_name の順で採用。
    """
    cfg = cfg or {}
    base = (cfg.get("linko_server_url") or "").strip().rstrip("/")
    if not base:
        base = (cfg.get("ai_board_url") or "http://127.0.0.1:5000").rstrip("/")
    path = "/entrance/me/cards"
    emp = (
        (cfg.get("face_registry_person_id") or "").strip()
        or (cfg.get("display_name") or "").strip()
    )
    if emp:
        return f"{base}{path}?employee_id={quote_plus(emp)}"
    return f"{base}{path}"
