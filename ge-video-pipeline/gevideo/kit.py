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
