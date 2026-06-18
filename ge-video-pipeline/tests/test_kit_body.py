from gevideo.kit import build_broadcast_body, youtube_email_html


def test_body_schedules_with_send_at_and_defaults_to_all_subscribers():
    body = build_broadcast_body(
        subject="New video", html_content="<p>hi</p>",
        send_at="2026-06-20T17:00:00Z")
    assert body["subject"] == "New video"
    assert body["content"] == "<p>hi</p>"
    assert body["send_at"] == "2026-06-20T17:00:00Z"
    assert body["published_at"] == "2026-06-20T17:00:00Z"
    assert body["public"] is False
    assert body["subscriber_filter"] == []   # all subscribers
    # required fields present and non-empty
    assert body["description"]
    assert body["preview_text"]


def test_explicit_description_and_preview_kept():
    body = build_broadcast_body(
        subject="S", html_content="x", send_at="2026-06-20T17:00:00Z",
        description="internal", preview_text="peek")
    assert body["description"] == "internal"
    assert body["preview_text"] == "peek"


def test_youtube_email_html_links_to_video():
    html = youtube_email_html("My Short", "https://youtu.be/abc123")
    assert "My Short" in html
    assert "https://youtu.be/abc123" in html
    assert "<a " in html
