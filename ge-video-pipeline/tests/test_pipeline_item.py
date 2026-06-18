import pytest

from gevideo.queue import (
    create_pipeline_item, set_status, load_pipeline_item, save_pipeline_item,
    InvalidTransition,
)


def test_create_pipeline_item_starts_generated():
    item = create_pipeline_item(date="2026-06-18",
                                topic={"id": "t1", "title": "Hello"})
    assert item["date"] == "2026-06-18"
    assert item["topic_id"] == "t1"
    assert item["title"] == "Hello"
    assert item["status"] == "generated"


def test_legal_transition_generated_to_pending():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    set_status(item, "pending_approval")
    assert item["status"] == "pending_approval"


def test_full_happy_path():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    for nxt in ["pending_approval", "approved", "scheduled", "published"]:
        set_status(item, nxt)
    assert item["status"] == "published"


def test_illegal_transition_raises():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    with pytest.raises(InvalidTransition):
        set_status(item, "published")  # cannot jump generated -> published


def test_hold_can_return_to_pending():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    set_status(item, "pending_approval")
    set_status(item, "hold")
    set_status(item, "pending_approval")
    assert item["status"] == "pending_approval"


def test_published_is_terminal():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    for nxt in ["pending_approval", "approved", "scheduled", "published"]:
        set_status(item, nxt)
    with pytest.raises(InvalidTransition):
        set_status(item, "error")


def test_save_and_load_pipeline_item_roundtrip(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)
    loaded = load_pipeline_item(tmp_path, "2026-06-18")
    assert loaded == item


def test_load_missing_pipeline_item_returns_none(tmp_path):
    assert load_pipeline_item(tmp_path, "2026-01-01") is None
