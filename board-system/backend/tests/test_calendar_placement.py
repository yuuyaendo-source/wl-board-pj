# -*- coding: utf-8 -*-
"""calendar_placement ユニットテスト。"""
from app.services.calendar_placement import (
    PLACEMENT_SOURCE_CALENDAR,
    PLACEMENT_SOURCE_CALENDAR_TIMED,
    include_in_task_remind,
    is_timed_event,
    is_working_location_event,
    placement_source_for_event,
    should_skip_calendar_sticky,
)


def test_working_location_skipped():
    ev = {"eventType": "workingLocation", "start": "2026-06-01"}
    assert is_working_location_event(ev)
    assert should_skip_calendar_sticky(ev)


def test_all_day_calendar_source():
    ev = {"eventType": "default", "start": "2026-06-01", "end": "2026-06-02"}
    assert not is_timed_event(ev)
    assert placement_source_for_event(ev) == PLACEMENT_SOURCE_CALENDAR
    assert include_in_task_remind(PLACEMENT_SOURCE_CALENDAR)


def test_timed_calendar_source_excluded_from_task_remind():
    ev = {"start": "2026-06-01T14:00:00+09:00"}
    assert is_timed_event(ev)
    assert placement_source_for_event(ev) == PLACEMENT_SOURCE_CALENDAR_TIMED
    assert not include_in_task_remind(PLACEMENT_SOURCE_CALENDAR_TIMED)


def test_manual_task_included():
    assert include_in_task_remind(None)


if __name__ == "__main__":
    test_working_location_skipped()
    test_all_day_calendar_source()
    test_timed_calendar_source_excluded_from_task_remind()
    test_manual_task_included()
    print("test_calendar_placement: OK")
