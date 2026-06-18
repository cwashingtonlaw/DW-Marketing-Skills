from datetime import date

from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, scheduled_publish_dates,
)


def test_create_item_has_publish_date_field():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    assert item["publish_date"] is None


def test_collects_local_publish_dates(tmp_path):
    a = create_pipeline_item(date="2026-06-10", topic={"id": "t", "title": "x"})
    a["publish_date"] = "2026-06-20"
    save_pipeline_item(tmp_path, a)

    b = create_pipeline_item(date="2026-06-11", topic={"id": "t2", "title": "y"})
    # b has no publish_date -> not counted
    save_pipeline_item(tmp_path, b)

    assert scheduled_publish_dates(tmp_path) == {date(2026, 6, 20)}


def test_empty_when_no_pipeline_dir(tmp_path):
    assert scheduled_publish_dates(tmp_path) == set()
