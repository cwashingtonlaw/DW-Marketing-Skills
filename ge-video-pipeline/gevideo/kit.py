"""Kit (kit.com) v4 broadcast adapter — schedule a newsletter email.

The HTTP transport is injectable so tests run offline.
"""
from __future__ import annotations

BASE_URL = "https://api.kit.com"


def build_broadcast_body(*, subject: str, html_content: str, send_at: str,
                         description: str = "", preview_text: str = "",
                         public: bool = False,
                         subscriber_filter=None) -> dict:
    return {
        "subject": subject,
        "content": html_content,
        "description": description or subject,
        "preview_text": preview_text or subject,
        "public": public,
        "published_at": send_at,
        "send_at": send_at,
        "subscriber_filter": list(subscriber_filter) if subscriber_filter else [],
    }


def youtube_email_html(title: str, youtube_url: str) -> str:
    return (f"<p>New video: <strong>{title}</strong></p>"
            f'<p><a href="{youtube_url}">Watch it on YouTube</a></p>')


import json
import urllib.request


class KitError(Exception):
    """Raised when Kit returns an error response."""


class _UrllibHttp:
    def post_json(self, url: str, headers: dict, payload: dict) -> dict:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body, headers=headers,
                                     method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())


class KitClient:
    def __init__(self, api_key: str, http=None, base_url: str = BASE_URL):
        self._api_key = api_key
        self._http = http or _UrllibHttp()
        self._base = base_url

    def _headers(self) -> dict:
        return {"X-Kit-Api-Key": self._api_key,
                "Content-Type": "application/json"}

    def create_broadcast(self, body: dict) -> int:
        resp = self._http.post_json(
            f"{self._base}/v4/broadcasts", self._headers(), body)
        if "broadcast" not in resp:
            raise KitError(resp.get("errors", resp))
        return resp["broadcast"]["id"]


def make_default_client(api_key: str) -> KitClient:
    return KitClient(api_key)
