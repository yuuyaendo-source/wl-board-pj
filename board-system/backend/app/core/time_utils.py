"""Common UTC and Japan time helpers."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def utc_now_naive() -> datetime:
    """Return UTC now as naive datetime for existing timezone-naive DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def now_jst() -> datetime:
    """Return current timezone-aware Japan time."""
    return datetime.now(JST)


def get_timezone(name: str | None = None) -> ZoneInfo:
    """Resolve a configured timezone, falling back to Japan time for invalid names."""
    try:
        return ZoneInfo(name or "Asia/Tokyo")
    except (KeyError, ValueError):
        return JST
