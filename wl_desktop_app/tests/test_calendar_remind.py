# -*- coding: utf-8 -*-
"""カレンダー・タスクのスケジュールリマインド設定パースのテスト。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config_loader import (  # noqa: E402
    parse_calendar_remind_minutes_from_text,
    parse_calendar_remind_minutes_list,
    parse_task_remind_times_from_text,
)


def test_calendar_list_from_legacy_single():
    cfg = {"calendar_remind_minutes_before": 5}
    assert parse_calendar_remind_minutes_list(cfg) == [5]


def test_calendar_list_from_list():
    cfg = {"calendar_remind_minutes_before_list": [5, 15, 5]}
    assert parse_calendar_remind_minutes_list(cfg) == [15, 5]


def test_calendar_list_from_text():
    assert parse_calendar_remind_minutes_from_text("15, 5") == [15, 5]
    assert parse_calendar_remind_minutes_from_text("5、15") == [15, 5]
    assert parse_calendar_remind_minutes_from_text("") == [15]


def test_task_times_from_text():
    assert parse_task_remind_times_from_text("13:00, 17:00") == ["13:00", "17:00"]
    assert parse_task_remind_times_from_text("9:00、9:00") == ["09:00"]


if __name__ == "__main__":
    test_calendar_list_from_legacy_single()
    test_calendar_list_from_list()
    test_calendar_list_from_text()
    test_task_times_from_text()
    print("test_calendar_remind: OK")
