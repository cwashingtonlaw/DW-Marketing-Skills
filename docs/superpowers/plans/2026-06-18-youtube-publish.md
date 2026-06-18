# YouTube Publish Implementation Plan (Plan 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the YouTube distribution adapter to `ge-video-pipeline`: upload the day's rendered MP4 via the YouTube Data API v3 as **private with a future `publishAt`** (so YouTube auto-publishes it at the scheduled slot), record the video id + schedule on the pipeline item, advance it `approved → scheduled`, plus the `ge-distribute` skill and a `youtube-schedule` CLI command.

**Architecture:** `gevideo/youtube.py` keeps pure logic (`build_video_body`, `schedule_upload`) separate from Google-specific code (`load_credentials`, `GoogleYouTubeUploader`, `make_default_uploader`). All Google imports are **lazy (inside functions/methods)** so importing the module — and the whole test suite — needs no Google libraries or network. `schedule_upload` takes an **injectable uploader**; tests pass a fake. The `youtube-schedule` CLI computes the publish slot via the existing `gevideo.slots`, using a new `queue.scheduled_publish_dates` helper to avoid double-booking a day.

**Tech Stack:** Python 3.11+, pytest, and (live-use only, lazy-imported) `google-api-python-client`, `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`.

**Verified YouTube Data API v3 (2026):**
- Scope `https://www.googleapis.com/auth/youtube.upload` covers `videos.insert` **and** setting `publishAt`.
- Schedule: `status.privacyStatus="private"` + `status.publishAt` = future RFC3339 UTC (`YYYY-MM-DDTHH:MM:SSZ`) → auto-publishes then. `publishAt` only works on a never-published private video.
- `part="snippet,status"`; resumable `MediaFileUpload(path, chunksize=-1, resumable=True)`, loop `next_chunk()`; new id at `response["id"]`.
- Shorts = vertical (9:16) ≤ 3 min; **no Shorts API field**.
- `videos.insert` = 1600 quota units (~6 uploads/day on the default 10,000).
- **Pitfall:** uploads from an *unverified* Cloud project are force-locked to private until the project passes API audit; testing-mode refresh tokens can expire ~7 days. Documented in the skill/README.

**Independently shippable:** at the end, an approved pipeline item with a rendered `video.mp4` can be uploaded + scheduled via `youtube-schedule` (with a verified OAuth project + token), and all logic is covered by network-free tests.

---

### Task 1: Add Google client libraries as an optional dependency

**Files:**
- Modify: `ge-video-pipeline/pyproject.toml`

- [ ] **Step 1: Add the optional dependency group**

In `ge-video-pipeline/pyproject.toml`, add a `youtube` extra under `[project.optional-dependencies]` (next to the existing `dev` entry):
```toml
[project.optional-dependencies]
dev = ["pytest>=8"]
youtube = [
    "google-api-python-client>=2",
    "google-auth>=2",
    "google-auth-oauthlib>=1",
    "google-auth-httplib2>=0.2",
]
```

- [ ] **Step 2: Install the extras**

Run: `cd ~/DW-Marketing-Skills/ge-video-pipeline && .venv/bin/pip install -q -e ".[dev,youtube]"`
Expected: installs the Google libraries with no errors.

- [ ] **Step 3: Verify the import works**

Run: `.venv/bin/python -c "import googleapiclient.discovery, google_auth_oauthlib.flow, google.oauth2.credentials; print('google libs OK')"`
Expected: `google libs OK`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "build: add optional youtube (google api) dependencies"
```

---

### Task 2: YouTube request-body builder

**Files:**
- Create: `ge-video-pipeline/gevideo/youtube.py`
- Test: `ge-video-pipeline/tests/test_youtube_body.py`

`build_video_body` produces the verified `videos.insert` body, hard-coding `privacyStatus="private"` so scheduling always works.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_youtube_body.py`:
```python
from gevideo.youtube import build_video_body, DEFAULT_CATEGORY_ID


def test_body_structure_schedules_as_private():
    body = build_video_body(
        title="My Short", description="desc", tags=["a", "b"],
        publish_at="2026-06-20T17:00:00Z",
    )
    assert body["snippet"]["title"] == "My Short"
    assert body["snippet"]["description"] == "desc"
    assert body["snippet"]["tags"] == ["a", "b"]
    assert body["snippet"]["categoryId"] == DEFAULT_CATEGORY_ID
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["publishAt"] == "2026-06-20T17:00:00Z"
    assert body["status"]["selfDeclaredMadeForKids"] is False


def test_category_and_kids_overridable():
    body = build_video_body(
        title="t", description="", tags=[], publish_at="2026-06-20T17:00:00Z",
        category_id="25", made_for_kids=True,
    )
    assert body["snippet"]["categoryId"] == "25"
    assert body["status"]["selfDeclaredMadeForKids"] is True


def test_tags_are_copied_not_aliased():
    tags = ["a"]
    body = build_video_body(title="t", description="", tags=tags,
                            publish_at="2026-06-20T17:00:00Z")
    tags.append("b")
    assert body["snippet"]["tags"] == ["a"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_youtube_body.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.youtube'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/youtube.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_youtube_body.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/youtube.py tests/test_youtube_body.py
git commit -m "feat: add YouTube videos.insert body builder"
```

---

### Task 3: schedule_upload flow + Google uploader

**Files:**
- Modify: `ge-video-pipeline/gevideo/youtube.py` (append the Google-specific code)
- Test: `ge-video-pipeline/tests/test_youtube_upload.py`

`schedule_upload` (already added in Task 2) is tested here with a fake uploader. The Google-specific `load_credentials`, `GoogleYouTubeUploader`, and `make_default_uploader` are added with lazy imports; they are exercised live (not unit-tested) since they need OAuth + network.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_youtube_upload.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_youtube_upload.py -q`
Expected: FAIL — `test_make_default_uploader_is_callable` errors with `AttributeError: module 'gevideo.youtube' has no attribute 'make_default_uploader'` (the `schedule_upload` test already passes from Task 2).

- [ ] **Step 3: Append the Google-specific code to `youtube.py`**

Add to the end of `ge-video-pipeline/gevideo/youtube.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_youtube_upload.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/youtube.py tests/test_youtube_upload.py
git commit -m "feat: add YouTube uploader (lazy google libs) + schedule_upload flow"
```

---

### Task 4: `scheduled_publish_dates` queue helper + `publish_date` field

**Files:**
- Modify: `ge-video-pipeline/gevideo/queue.py` (add `publish_date` to the item; add `scheduled_publish_dates`)
- Test: `ge-video-pipeline/tests/test_scheduled_dates.py`

`scheduled_publish_dates(data_dir)` scans pipeline items and returns the set of **local publish dates** already taken, so the slot computer never double-books a day. The item gains a `publish_date` field (the local calendar date of its slot).

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_scheduled_dates.py`:
```python
from datetime import date

from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, scheduled_publish_dates,
)


def test_create_item_has_publish_date_field():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    assert item["publish_date"] is None


def test_collects_local_publish_dates(tmp_path):
    a = create_pipeline_item(date="2026-06-10", topic={"id": "t", "title": "x"})
    a["publish_date"] = "2026-06-20"
    save_pipeline_item(tmp_path, a)

    b = create_pipeline_item(date="2026-06-11", topic={"id": "t2", "title": "y"})
    # b has no publish_date -> not counted
    save_pipeline_item(tmp_path, b)

    assert scheduled_publish_dates(tmp_path) == {date(2026, 6, 20)}


def test_empty_when_no_pipeline_dir(tmp_path):
    assert scheduled_publish_dates(tmp_path) == set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_scheduled_dates.py -q`
Expected: FAIL — `test_create_item_has_publish_date_field` (`KeyError: 'publish_date'`) and `ImportError: cannot import name 'scheduled_publish_dates'`.

- [ ] **Step 3: Implement**

In `ge-video-pipeline/gevideo/queue.py`, add `"publish_date": None,` to the dict returned by `create_pipeline_item` (immediately after the `"publish_at": None,` line):
```python
        "publish_at": None,      # RFC3339 string set at scheduling time
        "publish_date": None,    # local calendar date (YYYY-MM-DD) of the slot
```

Add this function at the end of `queue.py` (it needs `from datetime import date` — add that import at the top of the file):
```python
def scheduled_publish_dates(data_dir: Path | str) -> set:
    base = Path(data_dir) / "pipeline"
    result: set = set()
    if not base.exists():
        return result
    for child in base.iterdir():
        meta = child / "metadata.json"
        if not meta.exists():
            continue
        item = json.loads(meta.read_text())
        pd = item.get("publish_date")
        if pd:
            result.add(date.fromisoformat(pd))
    return result
```

Add the import near the top of `queue.py` (with the existing imports):
```python
from datetime import date
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_scheduled_dates.py -q`
Expected: 3 passed.

- [ ] **Step 5: Run the full suite (item-shape change is backward compatible)**

Run: `.venv/bin/pytest -q`
Expected: all prior tests still pass (the new field is additive; the roundtrip test compares saved-vs-loaded so it stays green).

- [ ] **Step 6: Commit**

```bash
git add gevideo/queue.py tests/test_scheduled_dates.py
git commit -m "feat: add scheduled_publish_dates helper and publish_date field"
```

---

### Task 5: `youtube-schedule` CLI command

**Files:**
- Modify: `ge-video-pipeline/gevideo/cli.py`
- Test: `ge-video-pipeline/tests/test_cli_youtube.py`

The command requires an `approved` item with a `video_path`, computes the next free publish slot from config + already-scheduled dates, uploads+schedules, and advances the item to `scheduled` with `youtube_video_id`, `publish_at`, and `publish_date` recorded. It calls `youtube.make_default_uploader` (monkeypatched in tests) and the real `youtube.schedule_upload`.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_cli_youtube.py`:
```python
import json

import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item, set_status,
)


def _approved_item(data_dir, tmp_path, item_date="2026-06-18"):
    item = create_pipeline_item(date=item_date, topic={"id": "t", "title": "Hook"})
    set_status(item, "pending_approval")
    set_status(item, "approved")
    video = tmp_path / f"video-{item_date}.mp4"
    video.write_bytes(b"MP4")
    item["video_path"] = str(video)
    item["metadata"] = {"title": "Big title", "description": "desc",
                        "tags": ["a", "b"]}
    save_pipeline_item(data_dir, item)
    return item


def _config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "avatar_id": "a", "voice_id": "v",
        "publish_time": "12:00", "timezone": "America/Chicago",
    }))
    return cfg


class FakeUploader:
    def __init__(self):
        self.body = None
        self.file = None

    def insert(self, body, file_path):
        self.body = body
        self.file = file_path
        return "yt_vid"


def test_youtube_schedule_uploads_and_updates_item(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    _approved_item(data_dir, tmp_path)
    cfg = _config(tmp_path)

    fake = FakeUploader()
    monkeypatch.setattr(cli.youtube, "make_default_uploader", lambda **kw: fake)

    code = cli.main([
        "--data-dir", str(data_dir), "youtube-schedule",
        "--date", "2026-06-18", "--config", str(cfg),
        "--publish-from", "2026-06-18",
        "--token-file", "tok.json", "--client-secret", "cs.json",
    ])

    assert code == 0
    updated = load_pipeline_item(data_dir, "2026-06-18")
    assert updated["status"] == "scheduled"
    assert updated["youtube_video_id"] == "yt_vid"
    assert updated["publish_at"] == "2026-06-18T17:00:00Z"   # 12:00 CDT -> 17:00Z
    assert updated["publish_date"] == "2026-06-18"
    assert fake.body["status"]["privacyStatus"] == "private"
    assert fake.body["status"]["publishAt"] == "2026-06-18T17:00:00Z"
    assert fake.body["snippet"]["title"] == "Big title"


def test_youtube_schedule_skips_already_used_date(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    # An item already scheduled for 2026-06-18
    taken = create_pipeline_item(date="2026-06-01", topic={"id": "x", "title": "z"})
    taken["publish_date"] = "2026-06-18"
    save_pipeline_item(data_dir, taken)
    # The approved item to schedule
    _approved_item(data_dir, tmp_path, item_date="2026-06-17")
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.youtube, "make_default_uploader",
                        lambda **kw: FakeUploader())

    code = cli.main([
        "--data-dir", str(data_dir), "youtube-schedule",
        "--date", "2026-06-17", "--config", str(cfg),
        "--publish-from", "2026-06-18",
        "--token-file", "tok.json", "--client-secret", "cs.json",
    ])
    assert code == 0
    updated = load_pipeline_item(data_dir, "2026-06-17")
    assert updated["publish_date"] == "2026-06-19"  # 18 taken -> next is 19
    assert updated["publish_at"] == "2026-06-19T17:00:00Z"


def test_youtube_schedule_requires_approved(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    item["video_path"] = str(tmp_path / "v.mp4")
    save_pipeline_item(data_dir, item)  # status still "generated"
    cfg = _config(tmp_path)
    monkeypatch.setattr(cli.youtube, "make_default_uploader",
                        lambda **kw: FakeUploader())

    code = cli.main([
        "--data-dir", str(data_dir), "youtube-schedule",
        "--date", "2026-06-18", "--config", str(cfg),
    ])
    assert code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_youtube.py -q`
Expected: FAIL — unknown subcommand / `cli.youtube` attribute error.

- [ ] **Step 3: Update `cli.py`**

Add to the imports at the top of `ge-video-pipeline/gevideo/cli.py`:
```python
from datetime import date, time
from zoneinfo import ZoneInfo

from gevideo import youtube
from gevideo.slots import compute_publish_at, to_rfc3339
```

Register the parser (after the `heygen-generate` parser block):
```python
    _yt_token = str(Path.home() / ".config/ge-video/youtube_token.json")
    _yt_secret = str(Path.home() / ".config/ge-video/youtube_client_secret.json")
    p_sched = sub.add_parser("youtube-schedule")
    p_sched.add_argument("--date", required=True)
    p_sched.add_argument("--config", required=True)
    p_sched.add_argument("--publish-from", default=None)
    p_sched.add_argument("--token-file", default=_yt_token)
    p_sched.add_argument("--client-secret", default=_yt_secret)
```

Add the handler (before the final `return 1`):
```python
    if args.command == "youtube-schedule":
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        if item["status"] != "approved":
            print(f"item {args.date} is {item['status']}, not approved",
                  file=sys.stderr)
            return 1
        if not item.get("video_path"):
            print(f"item {args.date} has no video_path", file=sys.stderr)
            return 1

        cfg = load_config(args.config)
        used = queue.scheduled_publish_dates(data_dir)
        from_date = (date.fromisoformat(args.publish_from)
                     if args.publish_from else date.today())
        hh, mm = (int(x) for x in cfg.publish_time.split(":"))
        slot = compute_publish_at(used, from_date, time(hh, mm), cfg.timezone)
        publish_at = to_rfc3339(slot)
        publish_date = slot.astimezone(ZoneInfo(cfg.timezone)).date().isoformat()

        meta = item.get("metadata", {})
        uploader = youtube.make_default_uploader(
            token_file=args.token_file, client_secret=args.client_secret)
        video_id = youtube.schedule_upload(
            uploader, file_path=item["video_path"],
            title=meta.get("title", item["title"]),
            description=meta.get("description", ""),
            tags=meta.get("tags", []),
            publish_at=publish_at,
            category_id=meta.get("category_id", youtube.DEFAULT_CATEGORY_ID))

        queue.set_status(item, "scheduled")
        item["youtube_video_id"] = video_id
        item["publish_at"] = publish_at
        item["publish_date"] = publish_date
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> scheduled {video_id} to publish {publish_at}")
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_youtube.py -q`
Expected: 3 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add gevideo/cli.py tests/test_cli_youtube.py
git commit -m "feat: add youtube-schedule CLI command"
```

---

### Task 6: The `ge-distribute` skill

**Files:**
- Create: `ge-video-pipeline/skills/ge-distribute/SKILL.md`

- [ ] **Step 1: Write the skill**

`ge-video-pipeline/skills/ge-distribute/SKILL.md`:
```markdown
---
name: ge-distribute
description: >
  Publish an approved Great Elephant Law video to YouTube as a scheduled Short.
  ALWAYS invoke for "schedule the video," "publish to YouTube," "upload the
  video," "schedule the short," or after the attorney approves a staged video.
  Uploads the rendered MP4 via the YouTube Data API as PRIVATE with a future
  publishAt (YouTube auto-publishes at the slot), then records the video id and
  schedule on the pipeline item. Part of ge-video-pipeline. This is the v1
  YouTube adapter of a pluggable distribution layer (Opus Clip cross-post and
  Kit newsletter come later).
---

# ge-distribute — YouTube Scheduled Publish (v1 adapter)

## STEP 0 — PRECONDITIONS
- The pipeline item for the date must be `approved` (the attorney approved it via
  ge-content-queue). If it is `pending_approval`, `hold`, or anything else, stop —
  only approved items publish.
- The item must have a `video_path` (rendered by ge-heygen).
- A **verified** YouTube OAuth project + saved token must exist:
  `~/.config/ge-video/youtube_client_secret.json` (Desktop OAuth client) and
  `~/.config/ge-video/youtube_token.json` (created on first consent). **If the
  Cloud project is unverified, uploads stay locked private even past publishAt
  until it passes Google's API audit** — flag this to the attorney if videos are
  not going public.

## STEP 1 — SCHEDULE
```
PY="${CLAUDE_PLUGIN_ROOT}/.venv/bin/python"
DATA_DIR="$HOME/.local/share/ge-video"
CFG="$HOME/.config/ge-video/config.json"
$PY -m gevideo.cli --data-dir "$DATA_DIR" youtube-schedule \
  --date YYYY-MM-DD --config "$CFG"
```
This picks the next free daily slot (config `publish_time`/`timezone`, skipping
days already scheduled), uploads the MP4 as private with that `publishAt`,
advances the item to `scheduled`, and records `youtube_video_id`, `publish_at`,
and `publish_date`.

## STEP 2 — REPORT
Echo the scheduled video id and publish time. Remind the attorney of the
manual-post destinations a tool cannot automate (Facebook personal, Instagram
personal, Snapchat) — attach/link the MP4 for manual posting.

## STEP 3 — NOTES
- One upload = 1600 of the 10,000 daily YouTube quota units (~6/day max).
- A Short is just a vertical (9:16) video ≤ 3 minutes; no special API flag.
- ge-distribute only acts on `approved` items and only sets `scheduled`; it never
  publishes on HOLD or without approval.
```

- [ ] **Step 2: Validate the plugin**

Run: `cd ~/DW-Marketing-Skills && claude plugin validate ./ge-video-pipeline`
Expected: `✔ Validation passed`.

- [ ] **Step 3: Commit**

```bash
git add ge-video-pipeline/skills/ge-distribute/SKILL.md
git commit -m "feat: add ge-distribute skill (YouTube v1 adapter)"
```

---

### Task 7: README, version bump, final verification

**Files:**
- Modify: `ge-video-pipeline/README.md`
- Modify: `ge-video-pipeline/.claude-plugin/plugin.json` (0.2.0 → 0.3.0)
- Modify: `.claude-plugin/marketplace.json` (ge-video-pipeline 0.2.0 → 0.3.0)

- [ ] **Step 1: Bump versions**

In `ge-video-pipeline/.claude-plugin/plugin.json` change `"version": "0.2.0"` to `"version": "0.3.0"`.
In `.claude-plugin/marketplace.json`, change the `ge-video-pipeline` entry's `"version": "0.2.0"` to `"version": "0.3.0"`.

- [ ] **Step 2: Update the README**

In `ge-video-pipeline/README.md`, replace the Plan 2 / Plan 3 status lines:
```markdown
- **Plan 2: HeyGen generation — DONE.** `gevideo.heygen` client + `ge-heygen`
  skill + `heygen-generate` CLI. Renders the attorney's custom avatar+voice.
- **Plan 3: YouTube publish — DONE.** `gevideo.youtube` adapter + `ge-distribute`
  skill + `youtube-schedule` CLI. Uploads private with a scheduled `publishAt`.
- Plan 4: orchestrator + notifications + launchd. Plan 5: Opus Clip cross-post +
  Kit newsletter.
```

Add this section after the `## HeyGen rendering` section:
```markdown
## YouTube scheduling
Install the Google libraries: `.venv/bin/pip install -e ".[dev,youtube]"`.

Create a **Desktop OAuth client** in a Google Cloud project with the YouTube Data
API enabled; download it to `~/.config/ge-video/youtube_client_secret.json`. The
first run opens a browser for consent and writes `~/.config/ge-video/youtube_token.json`
(reused thereafter). Scope: `youtube.upload`.

> **Important:** uploads from an *unverified* Cloud project are locked to private
> until the project passes Google's API audit — schedule will not go public until
> then. Keep the OAuth consent screen's test user = the channel owner.

```bash
PY=.venv/bin/python
DATA=~/.local/share/ge-video
CFG=~/.config/ge-video/config.json
# item must be approved and have a rendered video.mp4
$PY -m gevideo.cli --data-dir "$DATA" youtube-schedule --date 2026-06-18 --config "$CFG"
```
```

- [ ] **Step 3: Run the full suite**

Run: `cd ~/DW-Marketing-Skills/ge-video-pipeline && .venv/bin/pytest -q`
Expected: all tests pass.

- [ ] **Step 4: Validate marketplace + plugin**

Run: `cd ~/DW-Marketing-Skills && claude plugin validate . && claude plugin validate ./ge-video-pipeline`
Expected: both `✔ Validation passed`.

- [ ] **Step 5: Commit and push**

```bash
git add ge-video-pipeline/README.md ge-video-pipeline/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "docs: update README and bump ge-video-pipeline to 0.3.0"
git push -u origin feat/youtube-publish
```

---

## Plan complete — what ships

A tested `gevideo.youtube` adapter (body builder, injectable-uploader
`schedule_upload`, and lazy Google-backed `make_default_uploader`), the
`scheduled_publish_dates` slot-deduplication helper, the `youtube-schedule` CLI
command that uploads an approved item's MP4 as private with a computed future
`publishAt`, and the `ge-distribute` skill — plugin bumped to 0.3.0. With a
verified YouTube OAuth project + token, an approved + rendered item schedules
itself onto the next free daily slot; all logic is covered by network-free tests.

**Next:** Plan 4 (orchestrator) chains ge-script → ge-heygen → packaging →
ge-publish → stage-for-approval, adds Gmail/Chat notifications, and installs the
launchd daily job — turning these manual CLI steps into the autonomous
approve-then-publish loop.
