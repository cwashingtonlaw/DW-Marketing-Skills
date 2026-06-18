from gevideo.queue import (
    add_topic, promote_topic, next_ready_topic, count_ready,
    load_backlog, save_backlog,
)


def test_add_topic_appends_proposed_with_id(tmp_path):
    backlog = []
    item = add_topic(backlog, title="Field sobriety myths", notes="LA angle")
    assert item["title"] == "Field sobriety myths"
    assert item["notes"] == "LA angle"
    assert item["status"] == "proposed"
    assert item["id"]
    assert backlog == [item]


def test_promote_topic_sets_ready(tmp_path):
    backlog = []
    item = add_topic(backlog, title="T", notes="")
    promote_topic(backlog, item["id"])
    assert backlog[0]["status"] == "ready"


def test_promote_unknown_id_raises(tmp_path):
    backlog = []
    add_topic(backlog, title="T", notes="")
    try:
        promote_topic(backlog, "does-not-exist")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_next_ready_returns_first_ready_in_order(tmp_path):
    backlog = []
    a = add_topic(backlog, title="A", notes="")
    b = add_topic(backlog, title="B", notes="")
    # a is proposed, b is ready -> next ready is b
    promote_topic(backlog, b["id"])
    assert next_ready_topic(backlog)["id"] == b["id"]
    # promote a too -> a is earlier in order, so it wins
    promote_topic(backlog, a["id"])
    assert next_ready_topic(backlog)["id"] == a["id"]


def test_next_ready_returns_none_when_no_ready(tmp_path):
    backlog = []
    add_topic(backlog, title="A", notes="")
    assert next_ready_topic(backlog) is None


def test_count_ready(tmp_path):
    backlog = []
    a = add_topic(backlog, title="A", notes="")
    b = add_topic(backlog, title="B", notes="")
    promote_topic(backlog, a["id"])
    assert count_ready(backlog) == 1


def test_save_and_load_backlog_roundtrip(tmp_path):
    backlog = []
    add_topic(backlog, title="A", notes="n")
    save_backlog(tmp_path, backlog)
    loaded = load_backlog(tmp_path)
    assert loaded == backlog


def test_load_backlog_missing_file_returns_empty(tmp_path):
    assert load_backlog(tmp_path) == []
