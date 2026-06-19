from gevideo.notify import build_approval_message


def _item():
    return {
        "date": "2026-06-18",
        "title": "DWI checkpoint rights",
        "status": "pending_approval",
        "video_path": "/data/pipeline/2026-06-18/video.mp4",
        "compliance_verdict": {"verdict": "CLEAR", "note": ""},
    }


def test_subject_has_date_and_title():
    msg = build_approval_message(_item())
    assert "2026-06-18" in msg["subject"]
    assert "DWI checkpoint rights" in msg["subject"]


def test_body_has_verdict_video_and_manual_reminder():
    body = build_approval_message(_item())["body"]
    assert "CLEAR" in body
    assert "/data/pipeline/2026-06-18/video.mp4" in body
    assert "approve today's video" in body
    # manual cross-post via Opus
    assert "Opus" in body
    assert "Facebook Page" in body
    # destinations no tool automates
    assert "Facebook personal" in body
    assert "Instagram personal" in body
    assert "Snapchat" in body


def test_handles_missing_verdict():
    item = _item()
    item["compliance_verdict"] = None
    body = build_approval_message(item)["body"]
    assert "Compliance:" in body  # does not crash on None
