# HeyGen Generation Implementation Plan (Plan 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add HeyGen text-to-avatar video generation to `ge-video-pipeline`: a tested `gevideo.heygen` client that renders a script with the attorney's custom avatar+voice, polls to completion, downloads the MP4 into the day's pipeline directory, and updates the pipeline item — plus the `ge-heygen` skill and a `heygen-generate` CLI command.

**Architecture:** `gevideo/heygen.py` holds a `HeyGenClient` with an **injectable HTTP transport** (default uses stdlib `urllib`; tests inject a fake), so all logic is unit-tested with zero network calls. A `build_generate_payload` function builds the verified v2 request body, `wait_for_completion` polls with injectable clock/sleep, and `generate_to_file` orchestrates create→poll→download. `gevideo/secrets.py` loads the API key from env or `~/.config/ge-video/secrets.json`. A new `heygen-generate` CLI command wires config + secrets + the pipeline item.

**Tech Stack:** Python 3.11+ stdlib only (`urllib`, `json`, `time`, `pathlib`), pytest. **No new dependencies.**

**Verified HeyGen API (mid-2026, v2/v1 — supported through 2026-10-31):**
- Auth header `X-Api-Key: <key>`, base `https://api.heygen.com`.
- Create: `POST /v2/video/generate` → `{"error": null, "data": {"video_id": "..."}}`.
- Status: `GET /v1/video_status.get?video_id=<id>` → `{"data": {"id","status","video_url","duration","error"}}`; status ∈ `pending|processing|waiting|completed|failed`.
- `video_url` is a signed, time-limited CDN URL (download promptly, no auth header).
- `input_text` max **1500 chars**. Vertical Short dimension **720×1280**.

**This plan is independently shippable:** at the end you can render a real Short from a script file via `heygen-generate` (with a paid HeyGen key + avatar/voice ids), and every code path is covered by mocked tests.

---

### Task 1: Secrets loader

**Files:**
- Create: `ge-video-pipeline/gevideo/secrets.py`
- Test: `ge-video-pipeline/tests/test_secrets.py`

`get_secret(name)` returns an env var if set, else the key from `~/.config/ge-video/secrets.json`, else raises `KeyError`. A `config_path` argument allows tests to point elsewhere.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_secrets.py`:
```python
import json

import pytest

from gevideo.secrets import get_secret


def test_env_var_takes_precedence(tmp_path, monkeypatch):
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text(json.dumps({"HEYGEN_API_KEY": "from-file"}))
    monkeypatch.setenv("HEYGEN_API_KEY", "from-env")

    assert get_secret("HEYGEN_API_KEY", config_path=secrets_file) == "from-env"


def test_falls_back_to_secrets_file(tmp_path, monkeypatch):
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text(json.dumps({"HEYGEN_API_KEY": "from-file"}))
    monkeypatch.delenv("HEYGEN_API_KEY", raising=False)

    assert get_secret("HEYGEN_API_KEY", config_path=secrets_file) == "from-file"


def test_missing_secret_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("HEYGEN_API_KEY", raising=False)
    assert not (tmp_path / "secrets.json").exists()
    with pytest.raises(KeyError):
        get_secret("HEYGEN_API_KEY", config_path=tmp_path / "secrets.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_secrets.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.secrets'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/secrets.py`:
```python
"""Load secret values from the environment or a local secrets file."""
from __future__ import annotations

import json
import os
from pathlib import Path


def _default_secrets_path() -> Path:
    return Path.home() / ".config/ge-video/secrets.json"


def get_secret(name: str, config_path: Path | str | None = None) -> str:
    env_value = os.environ.get(name)
    if env_value:
        return env_value

    path = Path(config_path) if config_path else _default_secrets_path()
    if path.exists():
        data = json.loads(path.read_text())
        if name in data:
            return data[name]

    raise KeyError(name)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_secrets.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/secrets.py tests/test_secrets.py
git commit -m "feat: add secrets loader (env or secrets.json)"
```

---

### Task 2: HeyGen request-payload builder

**Files:**
- Create: `ge-video-pipeline/gevideo/heygen.py`
- Test: `ge-video-pipeline/tests/test_heygen_payload.py`

`build_generate_payload` produces the verified v2 body and enforces the 1500-char `input_text` limit.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_heygen_payload.py`:
```python
import pytest

from gevideo.heygen import build_generate_payload, MAX_INPUT_TEXT


def test_payload_has_verified_structure():
    payload = build_generate_payload(
        script="Hello there.", avatar_id="av_1", voice_id="vo_1",
        title="My Short", width=720, height=1280, speed=1.0,
    )
    assert payload["title"] == "My Short"
    assert payload["test"] is False
    assert payload["caption"] is False
    assert payload["dimension"] == {"width": 720, "height": 1280}

    inp = payload["video_inputs"][0]
    assert inp["character"]["type"] == "avatar"
    assert inp["character"]["avatar_id"] == "av_1"
    assert inp["character"]["avatar_style"] == "normal"
    assert inp["voice"]["type"] == "text"
    assert inp["voice"]["voice_id"] == "vo_1"
    assert inp["voice"]["input_text"] == "Hello there."
    assert inp["voice"]["speed"] == 1.0


def test_test_flag_can_be_set_true():
    payload = build_generate_payload(
        script="x", avatar_id="a", voice_id="v", title="t", test=True,
    )
    assert payload["test"] is True


def test_script_over_limit_raises():
    too_long = "a" * (MAX_INPUT_TEXT + 1)
    with pytest.raises(ValueError):
        build_generate_payload(script=too_long, avatar_id="a", voice_id="v", title="t")


def test_script_at_limit_is_allowed():
    ok = "a" * MAX_INPUT_TEXT
    payload = build_generate_payload(script=ok, avatar_id="a", voice_id="v", title="t")
    assert payload["video_inputs"][0]["voice"]["input_text"] == ok
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_heygen_payload.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.heygen'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/heygen.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_heygen_payload.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/heygen.py tests/test_heygen_payload.py
git commit -m "feat: add HeyGen generate-payload builder with length guard"
```

---

### Task 3: HeyGen client with injectable transport

**Files:**
- Modify: `ge-video-pipeline/gevideo/heygen.py` (append client + transport)
- Test: `ge-video-pipeline/tests/test_heygen_client.py`

`HeyGenClient` takes an `http` transport object (methods `post_json(url, headers, payload)`, `get_json(url, headers)`, `get_bytes(url)`). Tests inject a fake; the default `_UrllibHttp` uses stdlib. `create_video` returns the `video_id` or raises `HeyGenError`; `get_status` returns the `data` dict; `download` writes bytes to a path.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_heygen_client.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_heygen_client.py -q`
Expected: FAIL with `ImportError: cannot import name 'HeyGenClient'`.

- [ ] **Step 3: Append the client to `heygen.py`**

Add to the end of `ge-video-pipeline/gevideo/heygen.py`:
```python
import json
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_heygen_client.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/heygen.py tests/test_heygen_client.py
git commit -m "feat: add HeyGen client with injectable transport"
```

---

### Task 4: Polling + generate-to-file orchestration

**Files:**
- Modify: `ge-video-pipeline/gevideo/heygen.py` (append `HeyGenTimeout`, `wait_for_completion`, `generate_to_file`)
- Test: `ge-video-pipeline/tests/test_heygen_flow.py`

`wait_for_completion` polls `get_status` until `completed` (returns the data dict), raises `HeyGenError` on `failed`, and raises `HeyGenTimeout` past the deadline — using injectable `sleep`/`now`. `generate_to_file` runs create → wait → download and returns a result dict.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_heygen_flow.py`:
```python
import pytest

from gevideo.heygen import (
    wait_for_completion, generate_to_file, HeyGenError, HeyGenTimeout,
)


class FakeClient:
    """Stub HeyGenClient for flow tests."""
    def __init__(self, statuses, video_id="vid123", blob=b"MP4"):
        self._statuses = list(statuses)
        self._video_id = video_id
        self._blob = blob
        self.created = None
        self.downloaded = None

    def create_video(self, **kwargs):
        self.created = kwargs
        return self._video_id

    def get_status(self, video_id):
        return self._statuses.pop(0)

    def download(self, video_url, dest_path):
        from pathlib import Path
        Path(dest_path).write_bytes(self._blob)
        self.downloaded = (video_url, str(dest_path))


def test_wait_returns_on_completed_after_polling():
    client = FakeClient(statuses=[
        {"status": "processing"},
        {"status": "waiting"},
        {"status": "completed", "video_url": "u", "duration": 30.0},
    ])
    slept = []
    data = wait_for_completion(client, "vid123", poll_interval=5,
                               sleep=slept.append, now=lambda: 0.0)
    assert data["status"] == "completed"
    assert slept == [5, 5]  # slept before each re-poll


def test_wait_raises_on_failed():
    client = FakeClient(statuses=[{"status": "failed",
                                   "error": {"message": "boom"}}])
    with pytest.raises(HeyGenError):
        wait_for_completion(client, "vid123", sleep=lambda s: None,
                            now=lambda: 0.0)


def test_wait_times_out():
    client = FakeClient(statuses=[{"status": "processing"}] * 100)
    ticks = iter([0.0, 10.0, 9999.0])
    with pytest.raises(HeyGenTimeout):
        wait_for_completion(client, "vid123", poll_interval=5, timeout=60,
                            sleep=lambda s: None, now=lambda: next(ticks))


def test_generate_to_file_runs_full_flow(tmp_path):
    client = FakeClient(statuses=[
        {"status": "completed", "video_url": "https://signed/x.mp4",
         "duration": 42.0}])
    dest = tmp_path / "video.mp4"

    result = generate_to_file(
        client, script="hi", avatar_id="a", voice_id="v", title="t",
        dest_path=dest, sleep=lambda s: None, now=lambda: 0.0)

    assert dest.read_bytes() == b"MP4"
    assert result["video_id"] == "vid123"
    assert result["duration"] == 42.0
    assert result["video_url"] == "https://signed/x.mp4"
    assert client.created["script"] == "hi"
    assert client.downloaded == ("https://signed/x.mp4", str(dest))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_heygen_flow.py -q`
Expected: FAIL with `ImportError: cannot import name 'wait_for_completion'`.

- [ ] **Step 3: Append the flow functions to `heygen.py`**

Add `import time` near the other imports at the bottom import block, then append:
```python
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
```

Note on the timeout test: the deadline is `now()+timeout` computed on the first call (`0.0+60=60`). The loop polls once (processing), then on the second iteration checks `now()` again — the `ticks` iterator yields `0.0` (deadline calc), `10.0` (first not-first check, under deadline → but status still processing so loops), `9999.0` (over deadline → raises). Adjust the iterator if your control flow reads `now()` a different number of times; the intent is: first poll processing, later poll past deadline → `HeyGenTimeout`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_heygen_flow.py -q`
Expected: 4 passed. If `test_wait_times_out` fails on iterator exhaustion, change `ticks` to `iter([0.0, 10.0, 9999.0, 9999.0])` (extra value tolerates an additional `now()` read) — do not change the production code to satisfy the test.

- [ ] **Step 5: Commit**

```bash
git add gevideo/heygen.py tests/test_heygen_flow.py
git commit -m "feat: add HeyGen polling and generate-to-file flow"
```

---

### Task 5: `heygen-generate` CLI command

**Files:**
- Modify: `ge-video-pipeline/gevideo/cli.py` (add the `heygen-generate` subcommand)
- Test: `ge-video-pipeline/tests/test_cli_heygen.py`

The command reads the day's script file, loads config (avatar/voice/dimension) and the API key, renders + downloads into `<data_dir>/pipeline/<date>/video.mp4`, and writes `video_path` onto the pipeline item. It calls `gevideo.heygen.generate_to_file`; the test monkeypatches that function so no client/network is needed.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_cli_heygen.py`:
```python
import json

import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item,
)


def _write_config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"avatar_id": "av_1", "voice_id": "vo_1"}))
    return cfg


def test_heygen_generate_renders_and_updates_item(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "Hook"})
    save_pipeline_item(data_dir, item)

    script_file = tmp_path / "script.txt"
    script_file.write_text("Read this aloud.")
    cfg = _write_config(tmp_path)
    monkeypatch.setenv("HEYGEN_API_KEY", "KEY")

    captured = {}

    def fake_generate_to_file(client, **kwargs):
        captured.update(kwargs)
        # simulate the download the real function performs
        from pathlib import Path
        Path(kwargs["dest_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(kwargs["dest_path"]).write_bytes(b"MP4")
        return {"video_id": "vid123", "video_url": "u", "duration": 30.0}

    monkeypatch.setattr(cli.heygen, "generate_to_file", fake_generate_to_file)

    code = cli.main([
        "--data-dir", str(data_dir), "heygen-generate",
        "--date", "2026-06-18", "--script-file", str(script_file),
        "--config", str(cfg),
    ])

    assert code == 0
    assert captured["script"] == "Read this aloud."
    assert captured["avatar_id"] == "av_1"
    assert captured["voice_id"] == "vo_1"

    updated = load_pipeline_item(data_dir, "2026-06-18")
    expected_path = str(data_dir / "pipeline" / "2026-06-18" / "video.mp4")
    assert updated["video_path"] == expected_path
    assert updated["metadata"]["heygen_video_id"] == "vid123"


def test_heygen_generate_missing_item_returns_nonzero(tmp_path, monkeypatch):
    script_file = tmp_path / "script.txt"
    script_file.write_text("x")
    cfg = _write_config(tmp_path)
    monkeypatch.setenv("HEYGEN_API_KEY", "KEY")

    code = cli.main([
        "--data-dir", str(tmp_path / "data"), "heygen-generate",
        "--date", "2099-01-01", "--script-file", str(script_file),
        "--config", str(cfg),
    ])
    assert code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_heygen.py -q`
Expected: FAIL — either `AttributeError` on `cli.heygen` or the `heygen-generate` subcommand is unknown (SystemExit from argparse).

- [ ] **Step 3: Add the subcommand to `cli.py`**

At the top of `ge-video-pipeline/gevideo/cli.py`, update the imports:
```python
from gevideo import queue
from gevideo import heygen
from gevideo.config import load_config
from gevideo.secrets import get_secret
```

Register the parser (after the `reject` parser, before `args = parser.parse_args(argv)`):
```python
    p_gen = sub.add_parser("heygen-generate")
    p_gen.add_argument("--date", required=True)
    p_gen.add_argument("--script-file", required=True)
    p_gen.add_argument("--config", required=True)
```

Add the handler (before the final `return 1`):
```python
    if args.command == "heygen-generate":
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        cfg = load_config(args.config)
        script = Path(args.script_file).read_text()
        api_key = get_secret("HEYGEN_API_KEY")
        client = heygen.HeyGenClient(api_key)
        dest = Path(data_dir) / "pipeline" / args.date / "video.mp4"
        result = heygen.generate_to_file(
            client, script=script, avatar_id=cfg.avatar_id,
            voice_id=cfg.voice_id, title=item["title"], dest_path=dest)
        item["video_path"] = str(dest)
        item["metadata"]["heygen_video_id"] = result["video_id"]
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> rendered {result['video_id']} -> {dest}")
        return 0
```

Add the `Path` import at the top of the file if not present:
```python
from pathlib import Path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_heygen.py -q`
Expected: 2 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest -q`
Expected: all tests pass (backbone 27 + Plan 2 additions).

- [ ] **Step 6: Commit**

```bash
git add gevideo/cli.py tests/test_cli_heygen.py
git commit -m "feat: add heygen-generate CLI command"
```

---

### Task 6: The `ge-heygen` skill

**Files:**
- Create: `ge-video-pipeline/skills/ge-heygen/SKILL.md`

- [ ] **Step 1: Write the skill**

`ge-video-pipeline/skills/ge-heygen/SKILL.md`:
```markdown
---
name: ge-heygen
description: >
  Render a Great Elephant Law short-form video with the responsible attorney's
  custom HeyGen avatar + voice. ALWAYS invoke for "generate the HeyGen video,"
  "render the avatar video," "make the video with HeyGen," "produce today's
  video," or after a Short script is ready and a pipeline item exists. Submits
  the script to HeyGen (v2 generate), polls to completion, downloads the MP4
  into the day's pipeline folder, and records it on the pipeline item. Part of
  ge-video-pipeline; called by ge-video-daily after ge-script/ge-shorts.
---

# ge-heygen — HeyGen Avatar Video Renderer

## STEP 0 — PRECONDITIONS
- A pipeline item must already exist for the target date (created by
  ge-video-daily). If not, stop and say so.
- A finalized Short **spoken script** must be saved to a text file. HeyGen reads
  ONLY spoken words — strip `[B-ROLL]`, `[ON-SCREEN TEXT]`, timecodes, and stage
  cues first. The script must be <= 1500 characters (HeyGen's limit); if longer,
  trim or split before rendering.
- `HEYGEN_API_KEY` must be available (env var or `~/.config/ge-video/secrets.json`),
  and `~/.config/ge-video/config.json` must contain `avatar_id` and `voice_id`
  for the attorney's custom avatar. (List options with the HeyGen API
  `/v2/avatars` and `/v2/voices` endpoints if the ids are unknown.)

## STEP 1 — RENDER
Run:
```
PY="${CLAUDE_PLUGIN_ROOT}/.venv/bin/python"
DATA_DIR="$HOME/.local/share/ge-video"
CFG="$HOME/.config/ge-video/config.json"
$PY -m gevideo.cli --data-dir "$DATA_DIR" heygen-generate \
  --date YYYY-MM-DD --script-file <path-to-spoken-script> --config "$CFG"
```
This creates the video, polls until complete (a ~60s clip can take several
minutes), downloads `video.mp4` into `$DATA_DIR/pipeline/<date>/`, and records
`video_path` + `metadata.heygen_video_id` on the pipeline item.

## STEP 2 — REPORT
Echo the command's result (the rendered video id and the saved path). If it
errors (bad avatar/voice id, throttling, failed render), report the message and
do NOT advance the item — generation can be retried.

## STEP 3 — HANDOFF
> **Next:** packaging + the ge-publish compliance gate, then staging the item
> for approval (ge-content-queue). ge-heygen does not change the item's status;
> the orchestrator (ge-video-daily) drives the state machine.

## COMPLIANCE NOTE
Only the responsible attorney's own custom avatar + voice may be used for ad
content (Louisiana bars a non-lawyer spokesperson — see ge-compliance-la). Never
substitute a stock HeyGen avatar for published firm marketing.
```

- [ ] **Step 2: Validate the plugin**

Run: `cd ~/DW-Marketing-Skills && claude plugin validate ./ge-video-pipeline`
Expected: `✔ Validation passed`.

- [ ] **Step 3: Commit**

```bash
git add ge-video-pipeline/skills/ge-heygen/SKILL.md
git commit -m "feat: add ge-heygen skill"
```

---

### Task 7: Update README, bump version, final verification

**Files:**
- Modify: `ge-video-pipeline/README.md`
- Modify: `ge-video-pipeline/.claude-plugin/plugin.json` (version 0.1.0 → 0.2.0)
- Modify: `.claude-plugin/marketplace.json` (ge-video-pipeline version 0.1.0 → 0.2.0)

- [ ] **Step 1: Bump the plugin version**

In `ge-video-pipeline/.claude-plugin/plugin.json` change `"version": "0.1.0"` to `"version": "0.2.0"`.

In `.claude-plugin/marketplace.json`, change the `ge-video-pipeline` entry's `"version": "0.1.0"` to `"version": "0.2.0"`.

- [ ] **Step 2: Update the README status + add HeyGen setup**

In `ge-video-pipeline/README.md`, replace the `## Status` section's first two bullets with:
```markdown
- **Plan 1: backbone — DONE.** config, content queue, slot computation,
  `ge-content-queue` skill + CLI.
- **Plan 2: HeyGen generation — DONE.** `gevideo.heygen` client + `ge-heygen`
  skill + `heygen-generate` CLI. Renders the attorney's custom avatar+voice.
```

And add this section after the `## CLI` section:
```markdown
## HeyGen rendering
Requires a **paid HeyGen API plan** (no free API tier) and the attorney's custom
`avatar_id` / `voice_id` in `~/.config/ge-video/config.json`. Put the API key in
`~/.config/ge-video/secrets.json` (`{"HEYGEN_API_KEY": "..."}`, chmod 600) or the
`HEYGEN_API_KEY` env var.

```bash
PY=.venv/bin/python
DATA=~/.local/share/ge-video
CFG=~/.config/ge-video/config.json
# script.txt must be SPOKEN words only, <= 1500 chars
$PY -m gevideo.cli --data-dir "$DATA" heygen-generate \
  --date 2026-06-18 --script-file script.txt --config "$CFG"
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
git commit -m "docs: update ge-video-pipeline README and bump to 0.2.0"
git push -u origin feat/heygen-generation
```

---

## Plan complete — what ships

A tested `gevideo.heygen` client (payload builder with the 1500-char guard,
injectable-transport client, polling, generate-to-file), the `heygen-generate`
CLI command that renders into the pipeline item, and the `ge-heygen` skill —
plugin bumped to 0.2.0. With a paid HeyGen key and the attorney's avatar/voice
ids, you can render a real vertical Short from a spoken-script file; every code
path is covered by mocked tests with no network calls.

**Next:** Plan 3 (YouTube publish) consumes the `video_path` this plan writes and
uploads it as private with a scheduled `publishAt`.
