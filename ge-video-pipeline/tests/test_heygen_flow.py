import pytest

from gevideo.heygen import (
    wait_for_completion, generate_to_file, HeyGenError, HeyGenTimeout,
)


class FakeClient:
    """Stub HeyGenClient for flow tests."""
    def __init__(self, statuses, video_id="vid123", blob=b"MP4"):
        self._statuses = list(statuses)
        self._video_id = video_id
        self._blob = blob
        self.created = None
        self.downloaded = None

    def create_video(self, **kwargs):
        self.created = kwargs
        return self._video_id

    def get_status(self, video_id):
        return self._statuses.pop(0)

    def download(self, video_url, dest_path):
        from pathlib import Path
        Path(dest_path).write_bytes(self._blob)
        self.downloaded = (video_url, str(dest_path))


def test_wait_returns_on_completed_after_polling():
    client = FakeClient(statuses=[
        {"status": "processing"},
        {"status": "waiting"},
        {"status": "completed", "video_url": "u", "duration": 30.0},
    ])
    slept = []
    data = wait_for_completion(client, "vid123", poll_interval=5,
                               sleep=slept.append, now=lambda: 0.0)
    assert data["status"] == "completed"
    assert slept == [5, 5]  # slept before each re-poll


def test_wait_raises_on_failed():
    client = FakeClient(statuses=[{"status": "failed",
                                   "error": {"message": "boom"}}])
    with pytest.raises(HeyGenError):
        wait_for_completion(client, "vid123", sleep=lambda s: None,
                            now=lambda: 0.0)


def test_wait_times_out():
    client = FakeClient(statuses=[{"status": "processing"}] * 100)
    ticks = iter([0.0, 10.0, 9999.0, 9999.0])
    with pytest.raises(HeyGenTimeout):
        wait_for_completion(client, "vid123", poll_interval=5, timeout=60,
                            sleep=lambda s: None, now=lambda: next(ticks))


def test_generate_to_file_runs_full_flow(tmp_path):
    client = FakeClient(statuses=[
        {"status": "completed", "video_url": "https://signed/x.mp4",
         "duration": 42.0}])
    dest = tmp_path / "video.mp4"

    result = generate_to_file(
        client, script="hi", avatar_id="a", voice_id="v", title="t",
        dest_path=dest, sleep=lambda s: None, now=lambda: 0.0)

    assert dest.read_bytes() == b"MP4"
    assert result["video_id"] == "vid123"
    assert result["duration"] == 42.0
    assert result["video_url"] == "https://signed/x.mp4"
    assert client.created["script"] == "hi"
    assert client.downloaded == ("https://signed/x.mp4", str(dest))
