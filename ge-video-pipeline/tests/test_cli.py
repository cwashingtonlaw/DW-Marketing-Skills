from gevideo.cli import main
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, set_status,
    load_pipeline_item, load_backlog,
)


def test_backlog_add_then_list(tmp_path, capsys):
    code = main(["--data-dir", str(tmp_path), "backlog-add",
                 "--title", "DWI checkpoints", "--notes", "LA"])
    assert code == 0
    backlog = load_backlog(tmp_path)
    assert backlog[0]["title"] == "DWI checkpoints"
    assert backlog[0]["status"] == "proposed"

    main(["--data-dir", str(tmp_path), "backlog-list"])
    out = capsys.readouterr().out
    assert "DWI checkpoints" in out
    assert "proposed" in out


def test_backlog_promote(tmp_path):
    main(["--data-dir", str(tmp_path), "backlog-add", "--title", "T", "--notes", ""])
    topic_id = load_backlog(tmp_path)[0]["id"]
    code = main(["--data-dir", str(tmp_path), "backlog-promote", "--id", topic_id])
    assert code == 0
    assert load_backlog(tmp_path)[0]["status"] == "ready"


def test_approve_moves_pending_to_approved(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    set_status(item, "pending_approval")
    save_pipeline_item(tmp_path, item)

    code = main(["--data-dir", str(tmp_path), "approve", "--date", "2026-06-18"])
    assert code == 0
    assert load_pipeline_item(tmp_path, "2026-06-18")["status"] == "approved"


def test_reject_moves_pending_to_hold(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    set_status(item, "pending_approval")
    save_pipeline_item(tmp_path, item)

    code = main(["--data-dir", str(tmp_path), "reject", "--date", "2026-06-18"])
    assert code == 0
    assert load_pipeline_item(tmp_path, "2026-06-18")["status"] == "hold"


def test_approve_missing_item_returns_nonzero(tmp_path):
    code = main(["--data-dir", str(tmp_path), "approve", "--date", "2099-01-01"])
    assert code == 1
