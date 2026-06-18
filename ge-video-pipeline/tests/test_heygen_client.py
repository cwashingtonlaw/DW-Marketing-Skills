import pytest

from gevideo.heygen import HeyGenClient, HeyGenError


class FakeHttp:
    """Records calls and returns queued responses."""
    def __init__(self, post_result=None, get_result=None, blob=b""):
        self.post_result = post_result
        self.get_result = get_result
        self.blob = blob
        self.calls = []

    def post_json(self, url, headers, payload):
        self.calls.append(("post", url, headers, payload))
        return self.post_result

    def get_json(self, url, headers):
        self.calls.append(("get", url, headers))
        return self.get_result

    def get_bytes(self, url):
        self.calls.append(("bytes", url))
        return self.blob


def test_create_video_returns_id_and_sends_api_key():
    http = FakeHttp(post_result={"error": None, "data": {"video_id": "vid123"}})
    client = HeyGenClient("KEY", http=http)

    video_id = client.create_video(script="hi", avatar_id="a", voice_id="v",
                                   title="t")

    assert video_id == "vid123"
    method, url, headers, payload = http.calls[0]
    assert url == "https://api.heygen.com/v2/video/generate"
    assert headers["X-Api-Key"] == "KEY"
    assert payload["video_inputs"][0]["voice"]["input_text"] == "hi"


def test_create_video_raises_on_error():
    http = FakeHttp(post_result={"error": {"message": "bad avatar"}, "data": None})
    client = HeyGenClient("KEY", http=http)
    with pytest.raises(HeyGenError):
        client.create_video(script="hi", avatar_id="a", voice_id="v", title="t")


def test_get_status_returns_data_dict():
    http = FakeHttp(get_result={"data": {"id": "vid123", "status": "processing",
                                         "video_url": "", "error": None}})
    client = HeyGenClient("KEY", http=http)

    data = client.get_status("vid123")

    assert data["status"] == "processing"
    method, url, headers = http.calls[0]
    assert url == "https://api.heygen.com/v1/video_status.get?video_id=vid123"
    assert headers["X-Api-Key"] == "KEY"


def test_download_writes_bytes(tmp_path):
    http = FakeHttp(blob=b"MP4DATA")
    client = HeyGenClient("KEY", http=http)
    dest = tmp_path / "video.mp4"

    client.download("https://signed.example/output.mp4", dest)

    assert dest.read_bytes() == b"MP4DATA"
    assert http.calls[-1] == ("bytes", "https://signed.example/output.mp4")
