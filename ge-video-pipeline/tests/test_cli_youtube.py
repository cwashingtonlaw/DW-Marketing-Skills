import json

import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item, set_status,
)


def _approved_item(data_dir, tmp_path, item_date="2026-06-18"):
    item = create_pipeline_item(date=item_date, topic={"id": "t", "title": "Hook"})
    set_status(item, "pending_approval")
    set_status(item, "approved")
    video = tmp_path / f"video-{item_date}.mp4"
    video.write_bytes(b"MP4")
    item["video_path"] = str(video)
    item["metadata"] = {"title": "Big title", "description": "desc",
                        "tags": ["a", "b"]}
    save_pipeline_item(data_dir, item)
    return item


def _config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "avatar_id": "a", "voice_id": "v",
        "publish_time": "12:00", "timezone": "America/Chicago",
    }))
    return cfg


class FakeUploader:
    def __init__(self):
        self.body = None
        self.file = None

    def insert(self, body, file_path):
        self.body = body
        self.file = file_path
        return "yt_vid"


def test_youtube_schedule_uploads_and_updates_item(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    _approved_item(data_dir, tmp_path)
    cfg = _config(tmp_path)

    fake = FakeUploader()
    monkeypatch.setattr(cli.youtube, "make_default_uploader", lambda **kw: fake)

    code = cli.main([
        "--data-dir", str(data_dir), "youtube-schedule",
        "--date", "2026-06-18", "--config", str(cfg),
        "--publish-from", "2026-06-18",
        "--token-file", "tok.json", "--client-secret", "cs.json",
    ])

    assert code == 0
    updated = load_pipeline_item(data_dir, "2026-06-18")
    assert updated["status"] == "scheduled"
    assert updated["youtube_video_id"] == "yt_vid"
    assert updated["publish_at"] == "2026-06-18T17:00:00Z"   # 12:00 CDT -> 17:00Z
    assert updated["publish_date"] == "2026-06-18"
    assert fake.body["status"]["privacyStatus"] == "private"
    assert fake.body["status"]["publishAt"] == "2026-06-18T17:00:00Z"
    assert fake.body["snippet"]["title"] == "Big title"


def test_youtube_schedule_skips_already_used_date(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    # An item already scheduled for 2026-06-18
    taken = create_pipeline_item(date="2026-06-01", topic={"id": "x", "title": "z"})
    taken["publish_date"] = "2026-06-18"
    save_pipeline_item(data_dir, taken)
    # The approved item to schedule
    _approved_item(data_dir, tmp_path, item_date="2026-06-17")
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.youtube, "make_default_uploader",
                        lambda **kw: FakeUploader())

    code = cli.main([
        "--data-dir", str(data_dir), "youtube-schedule",
        "--date", "2026-06-17", "--config", str(cfg),
        "--publish-from", "2026-06-18",
        "--token-file", "tok.json", "--client-secret", "cs.json",
    ])
    assert code == 0
    updated = load_pipeline_item(data_dir, "2026-06-17")
    assert updated["publish_date"] == "2026-06-19"  # 18 taken -> next is 19
    assert updated["publish_at"] == "2026-06-19T17:00:00Z"


def test_youtube_schedule_requires_approved(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    item["video_path"] = str(tmp_path / "v.mp4")
    save_pipeline_item(data_dir, item)  # status still "generated"
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.youtube, "make_default_uploader",
                        lambda **kw: FakeUploader())

    code = cli.main([
        "--data-dir", str(data_dir), "youtube-schedule",
        "--date", "2026-06-18", "--config", str(cfg),
    ])
    assert code == 1
