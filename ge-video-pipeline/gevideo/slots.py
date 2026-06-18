"""Compute the next free daily publish slot as a UTC timestamp."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def compute_publish_at(used_dates: set[date], from_date: date,
                       publish_time: time, tz: str) -> datetime:
    day = from_date
    while day in used_dates:
        day += timedelta(days=1)
    local = datetime.combine(day, publish_time, tzinfo=ZoneInfo(tz))
    return local.astimezone(timezone.utc)


def to_rfc3339(dt: datetime) -> str:
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")
