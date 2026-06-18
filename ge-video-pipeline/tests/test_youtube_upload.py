from gevideo.youtube import schedule_upload


class FakeUploader:
    def __init__(self, video_id="yt_vid"):
        self.video_id = video_id
        self.calls = []

    def insert(self, body, file_path):
        self.calls.append((body, file_path))
        return self.video_id


def test_schedule_upload_passes_body_and_returns_id():
    up = FakeUploader(video_id="abc123")
    vid = schedule_upload(
        up, file_path="/tmp/v.mp4", title="T", description="d",
        tags=["x"], publish_at="2026-06-20T17:00:00Z")

    assert vid == "abc123"
    body, file_path = up.calls[0]
    assert file_path == "/tmp/v.mp4"
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["publishAt"] == "2026-06-20T17:00:00Z"
    assert body["snippet"]["title"] == "T"


def test_make_default_uploader_is_callable():
    # Smoke check: the factory exists and is importable without google libs
    # being imported at module load (they're lazy). We don't call it (needs OAuth).
    from gevideo import youtube
    assert callable(youtube.make_default_uploader)
    assert callable(youtube.load_credentials)
    assert youtube.GoogleYouTubeUploader is not None
