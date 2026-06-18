import gevideo.cli as cli
from gevideo.queue import (
    add_topic, promote_topic, save_backlog, load_backlog,
    load_pipeline_item,
)


def test_daily_start_creates_item_and_consumes_topic(tmp_path):
    backlog = []
    t = add_topic(backlog, title="Field sobriety myths")
    promote_topic(backlog, t["id"])
    save_backlog(tmp_path, backlog)

    code = cli.main(["--data-dir", str(tmp_path), "daily-start",
                     "--date", "2026-06-18"])
    assert code == 0

    item = load_pipeline_item(tmp_path, "2026-06-18")
    assert item["title"] == "Field sobriety myths"
    assert item["status"] == "generated"
    assert load_backlog(tmp_path)[0]["status"] == "used"


def test_daily_start_is_idempotent(tmp_path):
    backlog = []
    a = add_topic(backlog, title="A")
    b = add_topic(backlog, title="B")
    promote_topic(backlog, a["id"])
    promote_topic(backlog, b["id"])
    save_backlog(tmp_path, backlog)

    cli.main(["--data-dir", str(tmp_path), "daily-start", "--date", "2026-06-18"])
    cli.main(["--data-dir", str(tmp_path), "daily-start", "--date", "2026-06-18"])

    # Only ONE topic consumed despite two runs for the same date
    used = [t for t in load_backlog(tmp_path) if t["status"] == "used"]
    assert len(used) == 1
    assert load_pipeline_item(tmp_path, "2026-06-18")["title"] == "A"


def test_daily_start_empty_backlog_returns_2(tmp_path):
    save_backlog(tmp_path, [])  # no ready topics
    code = cli.main(["--data-dir", str(tmp_path), "daily-start",
                     "--date", "2026-06-18"])
    assert code == 2
    assert load_pipeline_item(tmp_path, "2026-06-18") is None
