import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item,
)


def test_stage_clear_moves_to_pending_and_records_metadata(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)

    code = cli.main([
        "--data-dir", str(tmp_path), "stage", "--date", "2026-06-18",
        "--verdict", "CLEAR", "--note", "ok",
        "--title", "Real title", "--description", "desc", "--tags", "a, b ,c",
    ])
    assert code == 0
    updated = load_pipeline_item(tmp_path, "2026-06-18")
    assert updated["status"] == "pending_approval"
    assert updated["compliance_verdict"] == {"verdict": "CLEAR", "note": "ok"}
    assert updated["metadata"]["title"] == "Real title"
    assert updated["metadata"]["description"] == "desc"
    assert updated["metadata"]["tags"] == ["a", "b", "c"]


def test_stage_hold_moves_to_hold(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)

    code = cli.main([
        "--data-dir", str(tmp_path), "stage", "--date", "2026-06-18",
        "--verdict", "HOLD", "--note", "banned phrase",
    ])
    assert code == 0
    updated = load_pipeline_item(tmp_path, "2026-06-18")
    assert updated["status"] == "hold"
    assert updated["compliance_verdict"]["verdict"] == "HOLD"


def test_stage_missing_item_returns_1(tmp_path):
    code = cli.main([
        "--data-dir", str(tmp_path), "stage", "--date", "2099-01-01",
        "--verdict", "CLEAR",
    ])
    assert code == 1
