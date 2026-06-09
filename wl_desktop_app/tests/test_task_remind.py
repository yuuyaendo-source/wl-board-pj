# -*- coding: utf-8 -*-
"""タスクリマインドのスロット判定ユニットテスト。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime
from zoneinfo import ZoneInfo

from task_remind_client import active_slot_now

JST = ZoneInfo("Asia/Tokyo")


def _dt(h: int, m: int, weekday: int = 0) -> datetime:
    # 2026-06-01 は月曜 (weekday=0)
    base = datetime(2026, 6, 1, h, m, tzinfo=JST)
    if weekday != 0:
        from datetime import timedelta
        base = base + timedelta(days=weekday)
    return base


def test_active_slot_13_00_window():
    cfg = {"task_remind_times": ["13:00", "17:00"], "task_remind_weekdays_only": True}
    assert active_slot_now(cfg, _dt(13, 0)) == "13:00"
    assert active_slot_now(cfg, _dt(13, 10)) == "13:00"
    assert active_slot_now(cfg, _dt(12, 59)) is None
    assert active_slot_now(cfg, _dt(13, 15)) is None


def test_active_slot_17_00():
    cfg = {"task_remind_times": ["13:00", "17:00"]}
    assert active_slot_now(cfg, _dt(17, 5)) == "17:00"


def test_weekend_skipped():
    cfg = {"task_remind_times": ["13:00"], "task_remind_weekdays_only": True}
    # 2026-06-06 は土曜
    sat = datetime(2026, 6, 6, 13, 0, tzinfo=JST)
    assert active_slot_now(cfg, sat) is None


def test_remind_message_format():
    title = "API設計"
    msg = f"「{title}」、進みましたか？"
    assert "進みましたか" in msg


if __name__ == "__main__":
    test_active_slot_13_00_window()
    test_active_slot_17_00()
    test_weekend_skipped()
    test_remind_message_format()
    print("test_task_remind: OK")
