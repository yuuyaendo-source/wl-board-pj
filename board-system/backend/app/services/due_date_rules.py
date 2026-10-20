# -*- coding: utf-8 -*-
"""期限日ルールによるレーン自動振り分け判定サービス。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def should_move_to_today(due_date: Optional[date], today: Optional[date] = None) -> bool:
    """
    期限日に基づき、Personal ボードの TODAY レーンへ配置すべきかを判定する。
    - 期限日なし: False（INBOX）
    - 期限当日または超過 (days <= 0): True
    - 1ヶ月未満 (0 < days < 30): 残り日数が 1, 2, 3, 4, 5, 10, 20 日なら True
    - 1ヶ月以上 (days >= 30): 30の倍数日 (days % 30 == 0) なら True
    """
    if not due_date:
        return False
    if today is None:
        today = datetime.now(JST).date()

    days = (due_date - today).days
    if days <= 0:
        return True
    elif days < 30:
        return days in (1, 2, 3, 4, 5, 10, 20)
    else:
        return days % 30 == 0
