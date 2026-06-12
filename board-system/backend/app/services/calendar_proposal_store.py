# -*- coding: utf-8 -*-
"""ブレスト経由のカレンダー登録案（確認待ち）をメモリ保持。TTL 5 分。"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

_TTL_SEC = 300
_lock = threading.Lock()
_store: dict[str, "CalendarProposal"] = {}


@dataclass
class CalendarProposal:
    proposal_id: str
    user_id: int
    draft: dict[str, Any]
    created_at: float = field(default_factory=time.time)

    def expired(self) -> bool:
        return (time.time() - self.created_at) > _TTL_SEC


def _purge_expired() -> None:
    now = time.time()
    dead = [k for k, v in _store.items() if (now - v.created_at) > _TTL_SEC]
    for k in dead:
        _store.pop(k, None)


def create_proposal(user_id: int, draft: dict[str, Any]) -> CalendarProposal:
    with _lock:
        _purge_expired()
        pid = str(uuid.uuid4())
        p = CalendarProposal(proposal_id=pid, user_id=user_id, draft=dict(draft))
        _store[pid] = p
        return p


def get_proposal(proposal_id: str, user_id: int | None = None) -> Optional[CalendarProposal]:
    with _lock:
        _purge_expired()
        p = _store.get(proposal_id)
        if p is None or p.expired():
            _store.pop(proposal_id, None)
            return None
        if user_id is not None and p.user_id != user_id:
            return None
        return p


def update_draft(proposal_id: str, user_id: int, draft: dict[str, Any]) -> Optional[CalendarProposal]:
    with _lock:
        p = _store.get(proposal_id)
        if p is None or p.expired() or p.user_id != user_id:
            return None
        p.draft = dict(draft)
        p.created_at = time.time()
        return p


def delete_proposal(proposal_id: str, user_id: int | None = None) -> bool:
    with _lock:
        p = _store.get(proposal_id)
        if p is None:
            return False
        if user_id is not None and p.user_id != user_id:
            return False
        _store.pop(proposal_id, None)
        return True
