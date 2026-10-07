# -*- coding: utf-8 -*-
"""時刻・日付処理の共通ユーティリティ。"""

from typing import Optional


def normalize_time(raw: str) -> Optional[str]:
    """'9:5' を '09:05' のように HH:MM 形式に正規化。不正な形式なら None。"""
    s = (raw or "").strip()
    if not s or ":" not in s:
        return None
    parts = s.split(":", 1)
    try:
        h, m = int(parts[0]), int(parts[1])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    except (ValueError, TypeError):
        pass
    return None