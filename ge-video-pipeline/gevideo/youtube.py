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


def load_credentials(token_file: str, client_secret: str, scopes=SCOPES):
    """Load saved YouTube OAuth credentials, refreshing or running the one-time
    consent flow as needed. Google imports are lazy."""
    import os
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret, scopes)
            creds = flow.run_local_server(port=0, access_type="offline",
                                          prompt="consent")
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return creds


class GoogleYouTubeUploader:
    """Real uploader backed by the YouTube Data API v3."""

    def __init__(self, creds):
        from googleapiclient.discovery import build
        self._yt = build("youtube", "v3", credentials=creds)

    def insert(self, body: dict, file_path: str) -> str:
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = self._yt.videos().insert(
            part=",".join(body.keys()), body=body, media_body=media)
        response = None
        while response is None:
            _status, response = request.next_chunk()
        return response["id"]


def make_default_uploader(*, token_file: str, client_secret: str,
                          scopes=SCOPES) -> GoogleYouTubeUploader:
    creds = load_credentials(token_file, client_secret, scopes)
    return GoogleYouTubeUploader(creds)
