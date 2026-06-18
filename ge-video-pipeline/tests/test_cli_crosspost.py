import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item,
)


def _scheduled_item(data_dir):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "Hook"})
    item["status"] = "scheduled"
    item["youtube_video_id"] = "abc123"
    item["publish_at"] = "2026-06-18T17:00:00Z"
    item["metadata"] = {"title": "Big title", "description": "desc"}
    save_pipeline_item(data_dir, item)
    return item


def test_crosspost_posts_payload_and_records(tmp_path, monkeypatch):
    _scheduled_item(tmp_path)
    sent = {}
    monkeypatch.setattr(cli.crosspost, "post_crosspost",
                        lambda url, payload, **kw: sent.update(url=url, payload=payload) or 200)

    code = cli.main([
        "--data-dir", str(tmp_path), "crosspost", "--date", "2026-06-18",
        "--webhook-url", "https://hook",
    ])
    assert code == 0
    assert sent["url"] == "https://hook"
    assert sent["payload"]["video_url"] == "https://youtu.be/abc123"
    assert sent["payload"]["publish_at"] == "2026-06-18T17:00:00Z"
    assert sent["payload"]["title"] == "Big title"

    updated = load_pipeline_item(tmp_path, "2026-06-18")
    assert updated["crosspost"]["posted"] is True


def test_crosspost_custom_platforms(tmp_path, monkeypatch):
    _scheduled_item(tmp_path)
    sent = {}
    monkeypatch.setattr(cli.crosspost, "post_crosspost",
                        lambda url, payload, **kw: sent.update(payload=payload) or 200)

    cli.main([
        "--data-dir", str(tmp_path), "crosspost", "--date", "2026-06-18",
        "--webhook-url", "https://hook", "--platforms", "tiktok, x",
    ])
    assert sent["payload"]["platforms"] == ["tiktok", "x"]


def test_crosspost_requires_scheduled_video(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)
    code = cli.main([
        "--data-dir", str(tmp_path), "crosspost", "--date", "2026-06-18",
        "--webhook-url", "https://hook",
    ])
    assert code == 1
