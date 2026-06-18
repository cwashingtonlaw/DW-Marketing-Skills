import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, set_status,
)


def test_notify_chat_text_posts_raw(tmp_path, monkeypatch):
    sent = {}
    monkeypatch.setattr(cli.notify, "post_chat_webhook",
                        lambda url, text, **kw: sent.update(url=url, text=text) or 200)

    code = cli.main([
        "--data-dir", str(tmp_path), "notify-chat",
        "--text", "backlog empty", "--webhook-url", "https://hook",
    ])
    assert code == 0
    assert sent["url"] == "https://hook"
    assert sent["text"] == "backlog empty"


def test_notify_chat_date_posts_approval_message(tmp_path, monkeypatch):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "Hook"})
    set_status(item, "pending_approval")
    item["video_path"] = "/v.mp4"
    item["compliance_verdict"] = {"verdict": "CLEAR", "note": ""}
    save_pipeline_item(tmp_path, item)

    sent = {}
    monkeypatch.setattr(cli.notify, "post_chat_webhook",
                        lambda url, text, **kw: sent.update(text=text) or 200)

    code = cli.main([
        "--data-dir", str(tmp_path), "notify-chat",
        "--date", "2026-06-18", "--webhook-url", "https://hook",
    ])
    assert code == 0
    assert "Hook" in sent["text"]
    assert "Facebook personal" in sent["text"]


def test_notify_chat_requires_text_or_date(tmp_path):
    code = cli.main([
        "--data-dir", str(tmp_path), "notify-chat", "--webhook-url", "https://hook",
    ])
    assert code == 1
