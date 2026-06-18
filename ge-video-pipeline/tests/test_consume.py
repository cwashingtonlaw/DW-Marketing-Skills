from gevideo.queue import add_topic, promote_topic, consume_next_ready


def test_consume_returns_first_ready_and_marks_used():
    backlog = []
    a = add_topic(backlog, title="A")
    b = add_topic(backlog, title="B")
    promote_topic(backlog, a["id"])
    promote_topic(backlog, b["id"])

    taken = consume_next_ready(backlog)

    assert taken["id"] == a["id"]
    assert backlog[0]["status"] == "used"
    # b is still ready
    assert backlog[1]["status"] == "ready"


def test_consume_skips_proposed_and_used():
    backlog = []
    a = add_topic(backlog, title="A")            # proposed
    b = add_topic(backlog, title="B")
    promote_topic(backlog, b["id"])              # ready
    consume_next_ready(backlog)                  # takes b -> used
    assert consume_next_ready(backlog) is None   # only A (proposed) left


def test_consume_empty_returns_none():
    assert consume_next_ready([]) is None
