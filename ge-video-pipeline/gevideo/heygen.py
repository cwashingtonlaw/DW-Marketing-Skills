"""HeyGen text-to-avatar video client (v2 generate / v1 status)."""
from __future__ import annotations

BASE_URL = "https://api.heygen.com"
MAX_INPUT_TEXT = 1500  # HeyGen v2 input_text hard limit


def build_generate_payload(*, script: str, avatar_id: str, voice_id: str,
                           title: str, width: int = 720, height: int = 1280,
                           speed: float = 1.0, test: bool = False,
                           background: str = "#FFFFFF") -> dict:
    if len(script) > MAX_INPUT_TEXT:
        raise ValueError(
            f"script is {len(script)} chars; HeyGen limit is {MAX_INPUT_TEXT}")
    return {
        "title": title,
        "caption": False,
        "test": test,
        "dimension": {"width": width, "height": height},
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                    "speed": speed,
                },
                "background": {"type": "color", "value": background},
            }
        ],
    }


import json
import time
import urllib.request
from pathlib import Path


class HeyGenError(Exception):
    """Raised when HeyGen returns an error or a failed render."""


class _UrllibHttp:
    """Default HTTP transport using the standard library."""

    def post_json(self, url: str, headers: dict, payload: dict) -> dict:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body, headers=headers,
                                     method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def get_json(self, url: str, headers: dict) -> dict:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def get_bytes(self, url: str) -> bytes:
        with urllib.request.urlopen(url) as resp:
            return resp.read()


class HeyGenClient:
    def __init__(self, api_key: str, http=None, base_url: str = BASE_URL):
        self._api_key = api_key
        self._http = http or _UrllibHttp()
        self._base = base_url

    def _json_headers(self) -> dict:
        return {"X-Api-Key": self._api_key, "Content-Type": "application/json"}

    def create_video(self, *, script: str, avatar_id: str, voice_id: str,
                     title: str, width: int = 720, height: int = 1280,
                     speed: float = 1.0, test: bool = False) -> str:
        payload = build_generate_payload(
            script=script, avatar_id=avatar_id, voice_id=voice_id, title=title,
            width=width, height=height, speed=speed, test=test)
        resp = self._http.post_json(
            f"{self._base}/v2/video/generate", self._json_headers(), payload)
        if resp.get("error"):
            raise HeyGenError(resp["error"])
        return resp["data"]["video_id"]

    def get_status(self, video_id: str) -> dict:
        resp = self._http.get_json(
            f"{self._base}/v1/video_status.get?video_id={video_id}",
            {"X-Api-Key": self._api_key})
        return resp["data"]

    def download(self, video_url: str, dest_path: Path | str) -> None:
        data = self._http.get_bytes(video_url)
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


class HeyGenTimeout(Exception):
    """Raised when a render does not complete within the timeout."""


def wait_for_completion(client, video_id: str, *, poll_interval: int = 10,
                        timeout: int = 1800, sleep=time.sleep,
                        now=time.monotonic) -> dict:
    deadline = now() + timeout
    first = True
    while True:
        if not first:
            if now() >= deadline:
                raise HeyGenTimeout(video_id)
            sleep(poll_interval)
        first = False
        data = client.get_status(video_id)
        status = data["status"]
        if status == "completed":
            return data
        if status == "failed":
            raise HeyGenError(data.get("error"))
        # pending / processing / waiting -> loop


def generate_to_file(client, *, script: str, avatar_id: str, voice_id: str,
                     title: str, dest_path, width: int = 720,
                     height: int = 1280, speed: float = 1.0,
                     poll_interval: int = 10, timeout: int = 1800,
                     sleep=time.sleep, now=time.monotonic) -> dict:
    video_id = client.create_video(
        script=script, avatar_id=avatar_id, voice_id=voice_id, title=title,
        width=width, height=height, speed=speed)
    data = wait_for_completion(client, video_id, poll_interval=poll_interval,
                               timeout=timeout, sleep=sleep, now=now)
    client.download(data["video_url"], dest_path)
    return {"video_id": video_id, "video_url": data["video_url"],
            "duration": data.get("duration")}
