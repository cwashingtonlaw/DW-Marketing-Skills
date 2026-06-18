import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item,
)


def _scheduled_item(data_dir):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "Hook"})
    item["status"] = "scheduled"
    item["youtube_video_id"] = "abc123"
    item["publish_at"] = "2026-06-18T17:00:00Z"
    item["metadata"] = {"title": "Big title"}
    save_pipeline_item(data_dir, item)
    return item


class FakeKitClient:
    def __init__(self):
        self.body = None

    def create_broadcast(self, body):
        self.body = body
        return 777


def test_kit_broadcast_schedules_and_records_id(tmp_path, monkeypatch):
    _scheduled_item(tmp_path)
    fake = FakeKitClient()
    monkeypatch.setattr(cli.kit, "make_default_client", lambda key: fake)
    monkeypatch.setenv("KIT_API_KEY", "KEY")

    code = cli.main([
        "--data-dir", str(tmp_path), "kit-broadcast", "--date", "2026-06-18",
    ])
    assert code == 0
    # Broadcast scheduled for the video's go-live, links to the YouTube URL
    assert fake.body["send_at"] == "2026-06-18T17:00:00Z"
    assert "https://youtu.be/abc123" in fake.body["content"]
    assert "Big title" in fake.body["subject"]

    updated = load_pipeline_item(tmp_path, "2026-06-18")
    assert updated["kit_broadcast_id"] == 777


def test_kit_broadcast_requires_scheduled_video(tmp_path, monkeypatch):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)  # no youtube_video_id / publish_at
    monkeypatch.setenv("KIT_API_KEY", "KEY")

    code = cli.main([
        "--data-dir", str(tmp_path), "kit-broadcast", "--date", "2026-06-18",
    ])
    assert code == 1
