from datetime import date, datetime, time, timezone

from gevideo.slots import compute_publish_at, to_rfc3339


def test_first_free_slot_is_from_date_when_unused():
    # 2026-06-18 is CDT (UTC-5); 12:00 local -> 17:00 UTC.
    dt = compute_publish_at(used_dates=set(), from_date=date(2026, 6, 18),
                            publish_time=time(12, 0), tz="America/Chicago")
    assert dt == datetime(2026, 6, 18, 17, 0, tzinfo=timezone.utc)


def test_skips_used_dates():
    dt = compute_publish_at(used_dates={date(2026, 6, 18), date(2026, 6, 19)},
                            from_date=date(2026, 6, 18),
                            publish_time=time(12, 0), tz="America/Chicago")
    assert dt == datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc)


def test_to_rfc3339_uses_z_suffix():
    dt = datetime(2026, 6, 18, 17, 0, tzinfo=timezone.utc)
    assert to_rfc3339(dt) == "2026-06-18T17:00:00Z"
