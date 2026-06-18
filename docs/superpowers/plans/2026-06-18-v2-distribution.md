# v2 Distribution Implementation Plan (Plan 5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the v2 distribution adapters behind the existing `ge-distribute` interface, both scheduled to the video's go-live (`publish_at`): a **Kit newsletter** email (real v4 broadcasts API) and a **generic webhook cross-post** handoff (POST the YouTube URL + caption + schedule to a configurable webhook the attorney wires to Opus Clip / Buffer / Publer / Make).

**Architecture:** `gevideo/kit.py` (pure `build_broadcast_body` + `youtube_email_html`, injectable-transport `KitClient.create_broadcast`, lazy-stdlib `make_default_client`) and `gevideo/crosspost.py` (pure `build_crosspost_payload`, injectable `post_crosspost`). Two CLI commands — `kit-broadcast` and `crosspost` — read a *scheduled* pipeline item (it already has `youtube_video_id` + `publish_at` from Plan 3), build the YouTube link, and hand off, recording the result on the item. The `ge-distribute` skill gains v2 steps that run after the YouTube schedule. All network calls go through injectable transports so tests stay offline.

**Tech Stack:** Python 3.11+ stdlib (`urllib`, `json`), pytest. No new dependencies.

**Verified APIs (2026):**
- **Kit v4:** `POST https://api.kit.com/v4/broadcasts`, header `X-Kit-Api-Key`. Body requires `subject, content (HTML), description, preview_text, public, published_at, subscriber_filter`; optional `send_at` (ISO8601, UTC-assumed) schedules the send automatically — **no separate send call**. Empty `subscriber_filter` = all subscribers. Response id at `response["broadcast"]["id"]`; errors under `response["errors"]`.
- **Opus Clip:** its API can only post clips from an Opus project (not an external finished video), and its Zapier app has no posting action — so cross-posting is a **generic webhook handoff** the user routes to their scheduler of choice. (Documented in the skill.)

**Independently shippable:** at the end, a scheduled item can fan out to a Kit newsletter and a cross-post webhook by hand (`kit-broadcast`, `crosspost`), the `ge-distribute` skill chains them after YouTube, and all logic is covered by offline tests. This completes the pipeline (Plans 1–5).

---

### Task 1: Kit broadcast body builder + email HTML

**Files:**
- Create: `ge-video-pipeline/gevideo/kit.py`
- Test: `ge-video-pipeline/tests/test_kit_body.py`

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_kit_body.py`:
```python
from gevideo.kit import build_broadcast_body, youtube_email_html


def test_body_schedules_with_send_at_and_defaults_to_all_subscribers():
    body = build_broadcast_body(
        subject="New video", html_content="<p>hi</p>",
        send_at="2026-06-20T17:00:00Z")
    assert body["subject"] == "New video"
    assert body["content"] == "<p>hi</p>"
    assert body["send_at"] == "2026-06-20T17:00:00Z"
    assert body["published_at"] == "2026-06-20T17:00:00Z"
    assert body["public"] is False
    assert body["subscriber_filter"] == []   # all subscribers
    # required fields present and non-empty
    assert body["description"]
    assert body["preview_text"]


def test_explicit_description_and_preview_kept():
    body = build_broadcast_body(
        subject="S", html_content="x", send_at="2026-06-20T17:00:00Z",
        description="internal", preview_text="peek")
    assert body["description"] == "internal"
    assert body["preview_text"] == "peek"


def test_youtube_email_html_links_to_video():
    html = youtube_email_html("My Short", "https://youtu.be/abc123")
    assert "My Short" in html
    assert "https://youtu.be/abc123" in html
    assert "<a " in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_kit_body.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.kit'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/kit.py`:
```python
"""Kit (kit.com) v4 broadcast adapter — schedule a newsletter email.

The Google-style lazy pattern is unnecessary here (stdlib only); the HTTP
transport is injectable so tests run offline.
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_kit_body.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/kit.py tests/test_kit_body.py
git commit -m "feat: add Kit broadcast body builder and email HTML"
```

---

### Task 2: Kit client

**Files:**
- Modify: `ge-video-pipeline/gevideo/kit.py` (append client)
- Test: `ge-video-pipeline/tests/test_kit_client.py`

`KitClient.create_broadcast(body)` POSTs to `/v4/broadcasts` with the `X-Kit-Api-Key` header and returns the new broadcast id, raising `KitError` on an `errors` response. `make_default_client` is the factory the CLI uses.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_kit_client.py`:
```python
import pytest

from gevideo.kit import KitClient, KitError


class FakeHttp:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def post_json(self, url, headers, payload):
        self.calls.append((url, headers, payload))
        return self.result


def test_create_broadcast_returns_id_and_sends_key():
    http = FakeHttp({"broadcast": {"id": 64}})
    client = KitClient("KEY", http=http)

    bid = client.create_broadcast({"subject": "s"})

    assert bid == 64
    url, headers, payload = http.calls[0]
    assert url == "https://api.kit.com/v4/broadcasts"
    assert headers["X-Kit-Api-Key"] == "KEY"
    assert payload == {"subject": "s"}


def test_create_broadcast_raises_on_errors():
    http = FakeHttp({"errors": ["invalid params"]})
    client = KitClient("KEY", http=http)
    with pytest.raises(KitError):
        client.create_broadcast({"subject": "s"})


def test_make_default_client_is_callable():
    from gevideo import kit
    assert callable(kit.make_default_client)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_kit_client.py -q`
Expected: FAIL with `ImportError: cannot import name 'KitClient'`.

- [ ] **Step 3: Append the client to `kit.py`**

Add to the end of `ge-video-pipeline/gevideo/kit.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_kit_client.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/kit.py tests/test_kit_client.py
git commit -m "feat: add Kit broadcast client"
```

---

### Task 3: Generic webhook cross-post

**Files:**
- Create: `ge-video-pipeline/gevideo/crosspost.py`
- Test: `ge-video-pipeline/tests/test_crosspost.py`

`build_crosspost_payload` builds the handoff JSON; `post_crosspost` POSTs it to a webhook via an injectable transport.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_crosspost.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_crosspost.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.crosspost'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/crosspost.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_crosspost.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/crosspost.py tests/test_crosspost.py
git commit -m "feat: add generic webhook cross-post handoff"
```

---

### Task 4: `kit-broadcast` CLI command

**Files:**
- Modify: `ge-video-pipeline/gevideo/cli.py`
- Test: `ge-video-pipeline/tests/test_cli_kit.py`

Requires a scheduled item (has `youtube_video_id` + `publish_at`), builds the YouTube link + email, and schedules a Kit broadcast for the video's go-live, recording `kit_broadcast_id` on the item.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_cli_kit.py`:
```python
import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item,
)


def _scheduled_item(data_dir):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "Hook"})
    item["status"] = "scheduled"
    item["youtube_video_id"] = "abc123"
    item["publish_at"] = "2026-06-18T17:00:00Z"
    item["metadata"] = {"title": "Big title"}
    save_pipeline_item(data_dir, item)
    return item


class FakeKitClient:
    def __init__(self):
        self.body = None

    def create_broadcast(self, body):
        self.body = body
        return 777


def test_kit_broadcast_schedules_and_records_id(tmp_path, monkeypatch):
    _scheduled_item(tmp_path)
    fake = FakeKitClient()
    monkeypatch.setattr(cli.kit, "make_default_client", lambda key: fake)
    monkeypatch.setenv("KIT_API_KEY", "KEY")

    code = cli.main([
        "--data-dir", str(tmp_path), "kit-broadcast", "--date", "2026-06-18",
    ])
    assert code == 0
    # Broadcast scheduled for the video's go-live, links to the YouTube URL
    assert fake.body["send_at"] == "2026-06-18T17:00:00Z"
    assert "https://youtu.be/abc123" in fake.body["content"]
    assert "Big title" in fake.body["subject"]

    updated = load_pipeline_item(tmp_path, "2026-06-18")
    assert updated["kit_broadcast_id"] == 777


def test_kit_broadcast_requires_scheduled_video(tmp_path, monkeypatch):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)  # no youtube_video_id / publish_at
    monkeypatch.setenv("KIT_API_KEY", "KEY")

    code = cli.main([
        "--data-dir", str(tmp_path), "kit-broadcast", "--date", "2026-06-18",
    ])
    assert code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_kit.py -q`
Expected: FAIL — unknown subcommand `kit-broadcast` / `cli.kit` attribute error.

- [ ] **Step 3: Update `cli.py`**

Add to the imports at the top: `from gevideo import kit`.

Register the parser (after the `notify-chat` parser block):
```python
    p_kit = sub.add_parser("kit-broadcast")
    p_kit.add_argument("--date", required=True)
    p_kit.add_argument("--api-key", default=None)
```

Add the handler (before the final `return 1`):
```python
    if args.command == "kit-broadcast":
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        if not item.get("youtube_video_id") or not item.get("publish_at"):
            print(f"item {args.date} is not scheduled (no youtube_video_id / "
                  f"publish_at)", file=sys.stderr)
            return 1
        title = item.get("metadata", {}).get("title", item["title"])
        youtube_url = f"https://youtu.be/{item['youtube_video_id']}"
        body = kit.build_broadcast_body(
            subject=title,
            html_content=kit.youtube_email_html(title, youtube_url),
            send_at=item["publish_at"])
        api_key = args.api_key or get_secret("KIT_API_KEY")
        client = kit.make_default_client(api_key)
        broadcast_id = client.create_broadcast(body)
        item["kit_broadcast_id"] = broadcast_id
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> kit broadcast {broadcast_id} for {item['publish_at']}")
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_kit.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/cli.py tests/test_cli_kit.py
git commit -m "feat: add kit-broadcast CLI command"
```

---

### Task 5: `crosspost` CLI command

**Files:**
- Modify: `ge-video-pipeline/gevideo/cli.py`
- Test: `ge-video-pipeline/tests/test_cli_crosspost.py`

Requires a scheduled item, builds the handoff payload (YouTube URL, title, description, `publish_at`, platforms), POSTs it to the webhook, and records `crosspost` on the item.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_cli_crosspost.py`:
```python
import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item,
)


def _scheduled_item(data_dir):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "Hook"})
    item["status"] = "scheduled"
    item["youtube_video_id"] = "abc123"
    item["publish_at"] = "2026-06-18T17:00:00Z"
    item["metadata"] = {"title": "Big title", "description": "desc"}
    save_pipeline_item(data_dir, item)
    return item


def test_crosspost_posts_payload_and_records(tmp_path, monkeypatch):
    _scheduled_item(tmp_path)
    sent = {}
    monkeypatch.setattr(cli.crosspost, "post_crosspost",
                        lambda url, payload, **kw: sent.update(url=url, payload=payload) or 200)

    code = cli.main([
        "--data-dir", str(tmp_path), "crosspost", "--date", "2026-06-18",
        "--webhook-url", "https://hook",
    ])
    assert code == 0
    assert sent["url"] == "https://hook"
    assert sent["payload"]["video_url"] == "https://youtu.be/abc123"
    assert sent["payload"]["publish_at"] == "2026-06-18T17:00:00Z"
    assert sent["payload"]["title"] == "Big title"

    updated = load_pipeline_item(tmp_path, "2026-06-18")
    assert updated["crosspost"]["posted"] is True


def test_crosspost_custom_platforms(tmp_path, monkeypatch):
    _scheduled_item(tmp_path)
    sent = {}
    monkeypatch.setattr(cli.crosspost, "post_crosspost",
                        lambda url, payload, **kw: sent.update(payload=payload) or 200)

    cli.main([
        "--data-dir", str(tmp_path), "crosspost", "--date", "2026-06-18",
        "--webhook-url", "https://hook", "--platforms", "tiktok, x",
    ])
    assert sent["payload"]["platforms"] == ["tiktok", "x"]


def test_crosspost_requires_scheduled_video(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)
    code = cli.main([
        "--data-dir", str(tmp_path), "crosspost", "--date", "2026-06-18",
        "--webhook-url", "https://hook",
    ])
    assert code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_crosspost.py -q`
Expected: FAIL — unknown subcommand `crosspost` / `cli.crosspost` attribute error.

- [ ] **Step 3: Update `cli.py`**

Add to the imports at the top: `from gevideo import crosspost`.

Register the parser (after the `kit-broadcast` parser block):
```python
    p_xp = sub.add_parser("crosspost")
    p_xp.add_argument("--date", required=True)
    p_xp.add_argument("--webhook-url", default=None)
    p_xp.add_argument("--platforms", default=None)
```

Add the handler (before the final `return 1`):
```python
    if args.command == "crosspost":
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        if not item.get("youtube_video_id") or not item.get("publish_at"):
            print(f"item {args.date} is not scheduled (no youtube_video_id / "
                  f"publish_at)", file=sys.stderr)
            return 1
        url = args.webhook_url or get_secret("CROSSPOST_WEBHOOK_URL")
        platforms = ([p.strip() for p in args.platforms.split(",") if p.strip()]
                     if args.platforms else None)
        meta = item.get("metadata", {})
        payload = crosspost.build_crosspost_payload(
            video_url=f"https://youtu.be/{item['youtube_video_id']}",
            title=meta.get("title", item["title"]),
            description=meta.get("description", ""),
            publish_at=item["publish_at"],
            platforms=platforms)
        crosspost.post_crosspost(url, payload)
        item["crosspost"] = {"posted": True, "platforms": payload["platforms"]}
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> cross-posted to {payload['platforms']}")
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_crosspost.py -q`
Expected: 3 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add gevideo/cli.py tests/test_cli_crosspost.py
git commit -m "feat: add crosspost CLI command"
```

---

### Task 6: Extend the `ge-distribute` skill with v2 steps

**Files:**
- Modify: `ge-video-pipeline/skills/ge-distribute/SKILL.md`

- [ ] **Step 1: Replace STEP 3 (NOTES) with v2 distribution + notes**

In `ge-video-pipeline/skills/ge-distribute/SKILL.md`, replace the `## STEP 3 — NOTES` section (the final section) with:
```markdown
## STEP 3 — v2 DISTRIBUTION (after YouTube is scheduled)
Once the item is `scheduled` (has `youtube_video_id` + `publish_at`), optionally
fan out — both timed to the same go-live:

- **Newsletter (Kit):** `GE kit-broadcast --date <today>` — schedules a Kit email
  to the subscriber list linking the YouTube video, sent at `publish_at`. Needs
  `KIT_API_KEY` in secrets. Records `kit_broadcast_id`.
- **Social cross-post (webhook):** `GE crosspost --date <today>` — POSTs
  `{video_url, title, description, publish_at, platforms}` to the configured
  webhook (`CROSSPOST_WEBHOOK_URL`). Wire that webhook to your scheduler (Zapier
  Catch Hook / Make / Buffer / Publer) which posts to Facebook Page, Instagram,
  TikTok, LinkedIn, X. **Opus Clip's API cannot post an external finished video,
  so the handoff is tool-agnostic.** Records `crosspost`.

Both fail soft: if a v2 step errors, the YouTube publish still stands — report
the failure so it can be retried or done by hand.

## STEP 4 — NOTES
- One YouTube upload = 1600 of the 10,000 daily quota units (~6/day max).
- A Short is just a vertical (9:16) video <= 3 minutes; no special API flag.
- ge-distribute only acts on `approved`/`scheduled` items and never publishes on
  HOLD or without approval.
- Manual-only destinations (no tool automates them): Facebook personal,
  Instagram personal, Snapchat.
```

- [ ] **Step 2: Validate the plugin**

Run: `cd ~/DW-Marketing-Skills && claude plugin validate ./ge-video-pipeline`
Expected: `✔ Validation passed`.

- [ ] **Step 3: Commit**

```bash
git add ge-video-pipeline/skills/ge-distribute/SKILL.md
git commit -m "docs: add v2 distribution steps to ge-distribute skill"
```

---

### Task 7: README, version bump, final verification

**Files:**
- Modify: `ge-video-pipeline/README.md`
- Modify: `ge-video-pipeline/.claude-plugin/plugin.json` (0.4.0 → 0.5.0)
- Modify: `.claude-plugin/marketplace.json` (ge-video-pipeline 0.4.0 → 0.5.0)

- [ ] **Step 1: Bump versions**

In `ge-video-pipeline/.claude-plugin/plugin.json` change `"version": "0.4.0"` to `"version": "0.5.0"`.
In `.claude-plugin/marketplace.json`, change the `ge-video-pipeline` entry's `"version": "0.4.0"` to `"version": "0.5.0"`.

- [ ] **Step 2: Update the README**

In `ge-video-pipeline/README.md`, replace the Plan 4 / Plan 5 status lines:
```markdown
- **Plan 4: orchestrator — DONE.** `ge-video-daily` skill chains the whole flow;
  `daily-start`/`stage`/`notify-chat` CLI + Google Chat notifier + launchd job.
- **Plan 5: v2 distribution — DONE.** `gevideo.kit` newsletter (v4 broadcasts) +
  `gevideo.crosspost` webhook handoff, both scheduled to the video's go-live.
```

Add this section after the `## Daily automation` section:
```markdown
## v2 distribution (newsletter + cross-post)
Both run after a video is scheduled on YouTube, timed to the same go-live:

- **Kit newsletter:** set `KIT_API_KEY` in `~/.config/ge-video/secrets.json`.
  `GE kit-broadcast --date <date>` schedules a Kit email (v4 broadcasts API)
  linking the YouTube video.
- **Cross-post webhook:** set `CROSSPOST_WEBHOOK_URL` in secrets.
  `GE crosspost --date <date>` POSTs `{video_url, title, description,
  publish_at, platforms}` to that webhook. Wire it to Zapier / Make / Buffer /
  Publer to post to FB Page, Instagram, TikTok, LinkedIn, X. (Opus Clip's API
  can't post an external finished video, so this handoff is tool-agnostic — point
  the webhook at whichever scheduler you use.)

```bash
GE() { .venv/bin/python -m gevideo.cli --data-dir ~/.local/share/ge-video "$@"; }
GE kit-broadcast --date 2026-06-18
GE crosspost --date 2026-06-18           # uses CROSSPOST_WEBHOOK_URL
GE crosspost --date 2026-06-18 --platforms "tiktok,x"
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
git commit -m "docs: update README and bump ge-video-pipeline to 0.5.0"
git push -u origin feat/v2-distribution
```

---

## Plan complete — what ships

The v2 distribution layer: a real `gevideo.kit` newsletter adapter (v4 broadcasts,
scheduled via `send_at`), a tool-agnostic `gevideo.crosspost` webhook handoff, the
`kit-broadcast` and `crosspost` CLI commands, and `ge-distribute` extended to fan
out after the YouTube schedule — plugin bumped to 0.5.0. All logic is covered by
offline tests. This completes the pipeline: topic → script → HeyGen → compliance
gate → approve → YouTube schedule → newsletter + cross-post, all timed to one
go-live, with the attorney approving before anything ships.
