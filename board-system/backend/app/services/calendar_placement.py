# -*- coding: utf-8 -*-
"""カレンダー由来 Today 付箋の placement_source とリマインド対象判定。"""
from __future__ import annotations

PLACEMENT_SOURCE_CALENDAR = "calendar"  # 終日予定
PLACEMENT_SOURCE_CALENDAR_TIMED = "calendar_timed"  # 時刻付き（N分前リマインドのみ）
CALENDAR_PLACEMENT_SOURCES = (PLACEMENT_SOURCE_CALENDAR, PLACEMENT_SOURCE_CALENDAR_TIMED)

EVENT_TYPE_WORKING_LOCATION = "workingLocation"


def is_working_location_event(event: dict) -> bool:
    return (event.get("eventType") or "").strip() == EVENT_TYPE_WORKING_LOCATION


def is_timed_event(event: dict) -> bool:
    start = (event.get("start") or "").strip()
    return bool(start and "T" in start)


def should_skip_calendar_sticky(event: dict) -> bool:
    """勤務場所は Today 付箋を作らない（events キャッシュ・カレンダー欄には残す）。"""
    return is_working_location_event(event)


def placement_source_for_event(event: dict) -> str:
    if is_timed_event(event):
        return PLACEMENT_SOURCE_CALENDAR_TIMED
    return PLACEMENT_SOURCE_CALENDAR


def is_calendar_placement_source(src: str | None) -> bool:
    return src in CALENDAR_PLACEMENT_SOURCES


def include_in_task_remind(placement_source: str | None) -> bool:
    """定時タスクリマインド（13:00/17:00）の対象か。時刻付き会議は除外。"""
    return placement_source != PLACEMENT_SOURCE_CALENDAR_TIMED
