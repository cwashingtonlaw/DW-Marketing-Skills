"""YouTube Data API v3 distribution adapter (upload + scheduled publish).

Google client libraries are imported lazily inside the Google-specific
functions, so importing this module (and the test suite) needs no Google
dependencies or network.
"""
from __future__ import annotations

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
DEFAULT_CATEGORY_ID = "22"  # People & Blogs


def build_video_body(*, title: str, description: str, tags, publish_at: str,
                     category_id: str = DEFAULT_CATEGORY_ID,
                     made_for_kids: bool = False) -> dict:
    return {
        "snippet": {
            "title": title,
            "description": description,
            "tags": list(tags),
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "private",   # REQUIRED for publishAt scheduling
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }


def schedule_upload(uploader, *, file_path: str, title: str, description: str,
                    tags, publish_at: str,
                    category_id: str = DEFAULT_CATEGORY_ID,
                    made_for_kids: bool = False) -> str:
    body = build_video_body(
        title=title, description=description, tags=tags, publish_at=publish_at,
        category_id=category_id, made_for_kids=made_for_kids)
    return uploader.insert(body, file_path)
