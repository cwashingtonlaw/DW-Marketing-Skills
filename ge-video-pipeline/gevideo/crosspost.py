"""Generic webhook cross-post handoff.

POSTs the finished video's public URL + caption + schedule to a configurable
webhook (Zapier Catch Hook / Make / Buffer / Publer), which the user wires to
their social scheduler. Opus Clip's API cannot post an external finished video,
so this tool-agnostic handoff is the reliable path.
"""
from __future__ import annotations

import json
import urllib.request

DEFAULT_PLATFORMS = ["facebook_page", "instagram", "tiktok", "linkedin", "x"]


def build_crosspost_payload(*, video_url: str, title: str, description: str,
                            publish_at: str, platforms=None) -> dict:
    return {
        "video_url": video_url,
        "title": title,
        "description": description,
        "publish_at": publish_at,
        "platforms": list(platforms) if platforms else list(DEFAULT_PLATFORMS),
    }


class _UrllibPoster:
    def post(self, url: str, payload: dict) -> int:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req) as resp:
            return resp.status


def post_crosspost(webhook_url: str, payload: dict, http=None) -> int:
    http = http or _UrllibPoster()
    return http.post(webhook_url, payload)
