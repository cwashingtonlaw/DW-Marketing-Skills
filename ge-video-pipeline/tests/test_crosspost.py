from gevideo.crosspost import (
    build_crosspost_payload, post_crosspost, DEFAULT_PLATFORMS,
)


class FakePoster:
    def __init__(self):
        self.calls = []

    def post(self, url, payload):
        self.calls.append((url, payload))
        return 200


def test_payload_defaults_to_all_platforms():
    p = build_crosspost_payload(
        video_url="https://youtu.be/abc", title="T", description="d",
        publish_at="2026-06-20T17:00:00Z")
    assert p["video_url"] == "https://youtu.be/abc"
    assert p["title"] == "T"
    assert p["description"] == "d"
    assert p["publish_at"] == "2026-06-20T17:00:00Z"
    assert p["platforms"] == list(DEFAULT_PLATFORMS)


def test_payload_platforms_overridable_and_copied():
    plats = ["tiktok"]
    p = build_crosspost_payload(
        video_url="u", title="T", description="d",
        publish_at="2026-06-20T17:00:00Z", platforms=plats)
    plats.append("x")
    assert p["platforms"] == ["tiktok"]


def test_post_crosspost_sends_payload():
    poster = FakePoster()
    payload = {"video_url": "u"}
    status = post_crosspost("https://hook", payload, http=poster)
    assert status == 200
    assert poster.calls[0] == ("https://hook", payload)
