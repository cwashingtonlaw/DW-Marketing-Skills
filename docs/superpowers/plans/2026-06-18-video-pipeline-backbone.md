# Video Pipeline Backbone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the tested foundation of the `ge-video-pipeline` plugin — config loading, the content-queue state machine, publish-slot computation, and a CLI/skill to drive them by hand — so later plans (HeyGen, YouTube, orchestrator, distribution) plug into a verified backbone.

**Architecture:** A small Python package `gevideo` holding pure logic (no external APIs in this plan): `config.py` loads settings, `queue.py` manages the topic backlog and the per-day pipeline item with a validated status state machine, `slots.py` computes the next free daily publish timestamp, and `cli.py` exposes commands the `ge-content-queue` skill calls. State lives as JSON under a data directory outside the repo.

**Tech Stack:** Python 3.11+ (stdlib only — `json`, `dataclasses`, `datetime`, `zoneinfo`, `argparse`, `uuid`), pytest for tests, setuptools editable install.

**This plan is part of a sequence.** It is independently shippable: at the end you can add topics, promote them, create a day's pipeline item, walk it through statuses, compute its publish slot, and approve/reject it from the CLI. Plans 2–5 add HeyGen, YouTube, the orchestrator, and cross-post/newsletter distribution.

---

### Task 1: Scaffold the `ge-video-pipeline` plugin and Python project

**Files:**
- Create: `ge-video-pipeline/.claude-plugin/plugin.json`
- Create: `ge-video-pipeline/pyproject.toml`
- Create: `ge-video-pipeline/gevideo/__init__.py`
- Create: `ge-video-pipeline/tests/__init__.py`
- Create: `ge-video-pipeline/.gitignore`
- Modify: `.claude-plugin/marketplace.json` (add the new plugin entry)

- [ ] **Step 1: Create the plugin manifest**

`ge-video-pipeline/.claude-plugin/plugin.json`:
```json
{
  "name": "ge-video-pipeline",
  "version": "0.1.0",
  "description": "Daily HeyGen short-form video pipeline for Great Elephant Law — content queue, scheduling, and approval workflow that feeds YouTube and (later) cross-post distribution. Depends on the ge-youtube content + compliance skills.",
  "author": {
    "name": "Chris Washington",
    "email": "cjw@danielswashington.com"
  },
  "skills": "./skills"
}
```

- [ ] **Step 2: Create the Python project file**

`ge-video-pipeline/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "gevideo"
version = "0.1.0"
description = "Great Elephant Law daily video pipeline backbone"
requires-python = ">=3.11"

[project.optional-dependencies]
dev = ["pytest>=8"]

[tool.setuptools]
packages = ["gevideo"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Create empty package and test init files**

`ge-video-pipeline/gevideo/__init__.py`:
```python
```

`ge-video-pipeline/tests/__init__.py`:
```python
```

- [ ] **Step 4: Create .gitignore for the plugin**

`ge-video-pipeline/.gitignore`:
```
__pycache__/
*.pyc
*.egg-info/
.pytest_cache/
.venv/
build/
dist/
```

- [ ] **Step 5: Add the plugin to the marketplace**

In `.claude-plugin/marketplace.json`, add this object to the `plugins` array (after the `ge-youtube` entry):
```json
    {
      "name": "ge-video-pipeline",
      "source": "./ge-video-pipeline",
      "description": "Daily HeyGen short-form video pipeline — content queue, scheduling, and approval workflow feeding YouTube and cross-post distribution.",
      "version": "0.1.0",
      "author": {
        "name": "Chris Washington",
        "email": "cjw@danielswashington.com"
      }
    }
```

- [ ] **Step 6: Install and verify the project builds**

Run: `cd ge-video-pipeline && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`
Expected: installs `gevideo` and `pytest` with no errors.

- [ ] **Step 7: Verify both manifests validate**

Run: `claude plugin validate . && claude plugin validate ./ge-video-pipeline`
Expected: both print `✔ Validation passed`.

- [ ] **Step 8: Commit**

```bash
git add ge-video-pipeline/.claude-plugin ge-video-pipeline/pyproject.toml ge-video-pipeline/gevideo ge-video-pipeline/tests ge-video-pipeline/.gitignore .claude-plugin/marketplace.json
git commit -m "feat: scaffold ge-video-pipeline plugin and gevideo package"
```

---

### Task 2: Config loader

**Files:**
- Create: `ge-video-pipeline/gevideo/config.py`
- Test: `ge-video-pipeline/tests/test_config.py`

The config holds non-secret settings. Defaults apply when keys are absent. `data_dir` defaults to `~/.local/share/ge-video` (expanded).

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_config.py`:
```python
import json
from pathlib import Path

from gevideo.config import Config, load_config


def test_load_config_applies_defaults_for_missing_keys(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"avatar_id": "av_1", "voice_id": "vo_1"}))

    cfg = load_config(cfg_file)

    assert cfg.avatar_id == "av_1"
    assert cfg.voice_id == "vo_1"
    assert cfg.publish_time == "12:00"
    assert cfg.timezone == "America/Chicago"
    assert cfg.buffer_days == 3
    assert cfg.backlog_low_threshold == 5


def test_load_config_overrides_defaults(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({
        "avatar_id": "av_1", "voice_id": "vo_1",
        "publish_time": "09:30", "timezone": "America/New_York",
        "buffer_days": 7, "backlog_low_threshold": 10,
        "data_dir": "/tmp/ge-video-data",
    }))

    cfg = load_config(cfg_file)

    assert cfg.publish_time == "09:30"
    assert cfg.timezone == "America/New_York"
    assert cfg.buffer_days == 7
    assert cfg.backlog_low_threshold == 10
    assert cfg.data_dir == Path("/tmp/ge-video-data")


def test_load_config_data_dir_defaults_to_local_share():
    # When data_dir is absent, it expands under the user's home.
    cfg = Config(avatar_id="a", voice_id="v")
    assert cfg.data_dir == Path.home() / ".local/share/ge-video"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.config'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/config.py`:
```python
"""Load non-secret pipeline configuration from a JSON file."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


def _default_data_dir() -> Path:
    return Path.home() / ".local/share/ge-video"


@dataclass
class Config:
    avatar_id: str
    voice_id: str
    channel_id: str = ""
    publish_time: str = "12:00"          # local HH:MM
    timezone: str = "America/Chicago"
    buffer_days: int = 3                 # keep this many days scheduled ahead
    backlog_low_threshold: int = 5       # warn when ready topics drop below this
    data_dir: Path = field(default_factory=_default_data_dir)


def load_config(path: Path | str) -> Config:
    data = json.loads(Path(path).read_text())
    data_dir = data.get("data_dir")
    return Config(
        avatar_id=data["avatar_id"],
        voice_id=data["voice_id"],
        channel_id=data.get("channel_id", ""),
        publish_time=data.get("publish_time", "12:00"),
        timezone=data.get("timezone", "America/Chicago"),
        buffer_days=data.get("buffer_days", 3),
        backlog_low_threshold=data.get("backlog_low_threshold", 5),
        data_dir=Path(data_dir) if data_dir else _default_data_dir(),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/config.py tests/test_config.py
git commit -m "feat: add config loader with defaults"
```

---

### Task 3: Backlog management

**Files:**
- Create: `ge-video-pipeline/gevideo/queue.py`
- Test: `ge-video-pipeline/tests/test_backlog.py`

The backlog is an ordered list of topic dicts persisted to `<data_dir>/backlog.json`. A topic is `{"id": str, "title": str, "notes": str, "status": "proposed"|"ready"}`. `next_ready_topic` returns the first `ready` topic in list order (list order = priority).

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_backlog.py`:
```python
from gevideo.queue import (
    add_topic, promote_topic, next_ready_topic, count_ready,
    load_backlog, save_backlog,
)


def test_add_topic_appends_proposed_with_id(tmp_path):
    backlog = []
    item = add_topic(backlog, title="Field sobriety myths", notes="LA angle")
    assert item["title"] == "Field sobriety myths"
    assert item["notes"] == "LA angle"
    assert item["status"] == "proposed"
    assert item["id"]
    assert backlog == [item]


def test_promote_topic_sets_ready(tmp_path):
    backlog = []
    item = add_topic(backlog, title="T", notes="")
    promote_topic(backlog, item["id"])
    assert backlog[0]["status"] == "ready"


def test_promote_unknown_id_raises(tmp_path):
    backlog = []
    add_topic(backlog, title="T", notes="")
    try:
        promote_topic(backlog, "does-not-exist")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_next_ready_returns_first_ready_in_order(tmp_path):
    backlog = []
    a = add_topic(backlog, title="A", notes="")
    b = add_topic(backlog, title="B", notes="")
    # a is proposed, b is ready -> next ready is b
    promote_topic(backlog, b["id"])
    assert next_ready_topic(backlog)["id"] == b["id"]
    # promote a too -> a is earlier in order, so it wins
    promote_topic(backlog, a["id"])
    assert next_ready_topic(backlog)["id"] == a["id"]


def test_next_ready_returns_none_when_no_ready(tmp_path):
    backlog = []
    add_topic(backlog, title="A", notes="")
    assert next_ready_topic(backlog) is None


def test_count_ready(tmp_path):
    backlog = []
    a = add_topic(backlog, title="A", notes="")
    b = add_topic(backlog, title="B", notes="")
    promote_topic(backlog, a["id"])
    assert count_ready(backlog) == 1


def test_save_and_load_backlog_roundtrip(tmp_path):
    backlog = []
    add_topic(backlog, title="A", notes="n")
    save_backlog(tmp_path, backlog)
    loaded = load_backlog(tmp_path)
    assert loaded == backlog


def test_load_backlog_missing_file_returns_empty(tmp_path):
    assert load_backlog(tmp_path) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_backlog.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.queue'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/queue.py`:
```python
"""Content backlog and per-day pipeline-item state, persisted as JSON."""
from __future__ import annotations

import json
import uuid
from pathlib import Path


# ---------- backlog ----------

def add_topic(backlog: list[dict], title: str, notes: str = "") -> dict:
    item = {"id": uuid.uuid4().hex, "title": title, "notes": notes,
            "status": "proposed"}
    backlog.append(item)
    return item


def promote_topic(backlog: list[dict], topic_id: str) -> dict:
    for item in backlog:
        if item["id"] == topic_id:
            item["status"] = "ready"
            return item
    raise KeyError(topic_id)


def next_ready_topic(backlog: list[dict]) -> dict | None:
    for item in backlog:
        if item["status"] == "ready":
            return item
    return None


def count_ready(backlog: list[dict]) -> int:
    return sum(1 for item in backlog if item["status"] == "ready")


def _backlog_path(data_dir: Path | str) -> Path:
    return Path(data_dir) / "backlog.json"


def load_backlog(data_dir: Path | str) -> list[dict]:
    path = _backlog_path(data_dir)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_backlog(data_dir: Path | str, backlog: list[dict]) -> None:
    path = _backlog_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(backlog, indent=2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_backlog.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/queue.py tests/test_backlog.py
git commit -m "feat: add content backlog management"
```

---

### Task 4: Pipeline item + status state machine

**Files:**
- Modify: `ge-video-pipeline/gevideo/queue.py` (append the pipeline-item functions)
- Test: `ge-video-pipeline/tests/test_pipeline_item.py`

A pipeline item is one video for one date, persisted to `<data_dir>/pipeline/<YYYY-MM-DD>/metadata.json`. Status transitions are validated; illegal moves raise `InvalidTransition`.

Status flow:
`generated → pending_approval → approved → scheduled → published`
plus `hold` and `error` side states.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_pipeline_item.py`:
```python
import pytest

from gevideo.queue import (
    create_pipeline_item, set_status, load_pipeline_item, save_pipeline_item,
    InvalidTransition,
)


def test_create_pipeline_item_starts_generated():
    item = create_pipeline_item(date="2026-06-18",
                                topic={"id": "t1", "title": "Hello"})
    assert item["date"] == "2026-06-18"
    assert item["topic_id"] == "t1"
    assert item["title"] == "Hello"
    assert item["status"] == "generated"


def test_legal_transition_generated_to_pending():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    set_status(item, "pending_approval")
    assert item["status"] == "pending_approval"


def test_full_happy_path():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    for nxt in ["pending_approval", "approved", "scheduled", "published"]:
        set_status(item, nxt)
    assert item["status"] == "published"


def test_illegal_transition_raises():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    with pytest.raises(InvalidTransition):
        set_status(item, "published")  # cannot jump generated -> published


def test_hold_can_return_to_pending():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    set_status(item, "pending_approval")
    set_status(item, "hold")
    set_status(item, "pending_approval")
    assert item["status"] == "pending_approval"


def test_published_is_terminal():
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    for nxt in ["pending_approval", "approved", "scheduled", "published"]:
        set_status(item, nxt)
    with pytest.raises(InvalidTransition):
        set_status(item, "error")


def test_save_and_load_pipeline_item_roundtrip(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)
    loaded = load_pipeline_item(tmp_path, "2026-06-18")
    assert loaded == item


def test_load_missing_pipeline_item_returns_none(tmp_path):
    assert load_pipeline_item(tmp_path, "2026-01-01") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_pipeline_item.py -v`
Expected: FAIL with `ImportError: cannot import name 'create_pipeline_item'`.

- [ ] **Step 3: Append the implementation to `queue.py`**

Add to the end of `ge-video-pipeline/gevideo/queue.py`:
```python
# ---------- pipeline item ----------

class InvalidTransition(Exception):
    """Raised when a status change is not allowed."""


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "generated": {"pending_approval", "hold", "error"},
    "pending_approval": {"approved", "hold"},
    "approved": {"scheduled", "error"},
    "scheduled": {"published", "error"},
    "hold": {"pending_approval", "generated"},
    "error": {"generated"},
    "published": set(),
}


def create_pipeline_item(date: str, topic: dict) -> dict:
    return {
        "date": date,
        "topic_id": topic["id"],
        "title": topic["title"],
        "status": "generated",
        "script_path": None,
        "video_path": None,
        "metadata": {},          # title, description, tags, thumbnail brief
        "compliance_verdict": None,
        "publish_at": None,      # RFC3339 string set at scheduling time
        "youtube_video_id": None,
    }


def set_status(item: dict, new_status: str) -> dict:
    current = item["status"]
    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"{current} -> {new_status}")
    item["status"] = new_status
    return item


def _pipeline_dir(data_dir: Path | str, date: str) -> Path:
    return Path(data_dir) / "pipeline" / date


def save_pipeline_item(data_dir: Path | str, item: dict) -> None:
    d = _pipeline_dir(data_dir, item["date"])
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(json.dumps(item, indent=2))


def load_pipeline_item(data_dir: Path | str, date: str) -> dict | None:
    path = _pipeline_dir(data_dir, date) / "metadata.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_pipeline_item.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/queue.py tests/test_pipeline_item.py
git commit -m "feat: add pipeline item with validated status state machine"
```

---

### Task 5: Publish-slot computation

**Files:**
- Create: `ge-video-pipeline/gevideo/slots.py`
- Test: `ge-video-pipeline/tests/test_slots.py`

`compute_publish_at` finds the earliest date on/after `from_date` not already in `used_dates`, combines it with the local publish time in the configured timezone, and returns a timezone-aware UTC `datetime`. `to_rfc3339` formats it for the YouTube API.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_slots.py`:
```python
from datetime import date, datetime, time, timezone

from gevideo.slots import compute_publish_at, to_rfc3339


def test_first_free_slot_is_from_date_when_unused():
    # 2026-06-18 is CDT (UTC-5); 12:00 local -> 17:00 UTC.
    dt = compute_publish_at(used_dates=set(), from_date=date(2026, 6, 18),
                            publish_time=time(12, 0), tz="America/Chicago")
    assert dt == datetime(2026, 6, 18, 17, 0, tzinfo=timezone.utc)


def test_skips_used_dates():
    dt = compute_publish_at(used_dates={date(2026, 6, 18), date(2026, 6, 19)},
                            from_date=date(2026, 6, 18),
                            publish_time=time(12, 0), tz="America/Chicago")
    assert dt == datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc)


def test_to_rfc3339_uses_z_suffix():
    dt = datetime(2026, 6, 18, 17, 0, tzinfo=timezone.utc)
    assert to_rfc3339(dt) == "2026-06-18T17:00:00Z"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_slots.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.slots'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/slots.py`:
```python
"""Compute the next free daily publish slot as a UTC timestamp."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def compute_publish_at(used_dates: set[date], from_date: date,
                       publish_time: time, tz: str) -> datetime:
    day = from_date
    while day in used_dates:
        day += timedelta(days=1)
    local = datetime.combine(day, publish_time, tzinfo=ZoneInfo(tz))
    return local.astimezone(timezone.utc)


def to_rfc3339(dt: datetime) -> str:
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_slots.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/slots.py tests/test_slots.py
git commit -m "feat: add publish-slot computation"
```

---

### Task 6: CLI entrypoint

**Files:**
- Create: `ge-video-pipeline/gevideo/cli.py`
- Test: `ge-video-pipeline/tests/test_cli.py`

The CLI is how the `ge-content-queue` skill drives the backbone. Commands operate on a `--data-dir` (so tests use a tmp dir). Subcommands: `backlog-add`, `backlog-promote`, `backlog-list`, `queue-status`, `approve`, `reject`. `approve` moves the day's item `pending_approval → approved`; `reject` moves it `pending_approval → hold`. Each prints a one-line result.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_cli.py`:
```python
from gevideo.cli import main
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, set_status,
    load_pipeline_item, load_backlog,
)


def test_backlog_add_then_list(tmp_path, capsys):
    code = main(["--data-dir", str(tmp_path), "backlog-add",
                 "--title", "DWI checkpoints", "--notes", "LA"])
    assert code == 0
    backlog = load_backlog(tmp_path)
    assert backlog[0]["title"] == "DWI checkpoints"
    assert backlog[0]["status"] == "proposed"

    main(["--data-dir", str(tmp_path), "backlog-list"])
    out = capsys.readouterr().out
    assert "DWI checkpoints" in out
    assert "proposed" in out


def test_backlog_promote(tmp_path):
    main(["--data-dir", str(tmp_path), "backlog-add", "--title", "T", "--notes", ""])
    topic_id = load_backlog(tmp_path)[0]["id"]
    code = main(["--data-dir", str(tmp_path), "backlog-promote", "--id", topic_id])
    assert code == 0
    assert load_backlog(tmp_path)[0]["status"] == "ready"


def test_approve_moves_pending_to_approved(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    set_status(item, "pending_approval")
    save_pipeline_item(tmp_path, item)

    code = main(["--data-dir", str(tmp_path), "approve", "--date", "2026-06-18"])
    assert code == 0
    assert load_pipeline_item(tmp_path, "2026-06-18")["status"] == "approved"


def test_reject_moves_pending_to_hold(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    set_status(item, "pending_approval")
    save_pipeline_item(tmp_path, item)

    code = main(["--data-dir", str(tmp_path), "reject", "--date", "2026-06-18"])
    assert code == 0
    assert load_pipeline_item(tmp_path, "2026-06-18")["status"] == "hold"


def test_approve_missing_item_returns_nonzero(tmp_path):
    code = main(["--data-dir", str(tmp_path), "approve", "--date", "2099-01-01"])
    assert code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.cli'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/cli.py`:
```python
"""Command-line entrypoint the ge-content-queue skill calls."""
from __future__ import annotations

import argparse
import sys

from gevideo import queue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gevideo")
    parser.add_argument("--data-dir", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("backlog-add")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--notes", default="")

    p_prom = sub.add_parser("backlog-promote")
    p_prom.add_argument("--id", required=True)

    sub.add_parser("backlog-list")
    sub.add_parser("queue-status")

    p_app = sub.add_parser("approve")
    p_app.add_argument("--date", required=True)

    p_rej = sub.add_parser("reject")
    p_rej.add_argument("--date", required=True)

    args = parser.parse_args(argv)
    data_dir = args.data_dir

    if args.command == "backlog-add":
        backlog = queue.load_backlog(data_dir)
        item = queue.add_topic(backlog, title=args.title, notes=args.notes)
        queue.save_backlog(data_dir, backlog)
        print(f"added topic {item['id']}: {item['title']} (proposed)")
        return 0

    if args.command == "backlog-promote":
        backlog = queue.load_backlog(data_dir)
        try:
            queue.promote_topic(backlog, args.id)
        except KeyError:
            print(f"no topic with id {args.id}", file=sys.stderr)
            return 1
        queue.save_backlog(data_dir, backlog)
        print(f"promoted {args.id} -> ready")
        return 0

    if args.command == "backlog-list":
        for item in queue.load_backlog(data_dir):
            print(f"{item['id']}  {item['status']:9}  {item['title']}")
        return 0

    if args.command == "queue-status":
        backlog = queue.load_backlog(data_dir)
        print(f"ready topics: {queue.count_ready(backlog)}")
        return 0

    if args.command in ("approve", "reject"):
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        target = "approved" if args.command == "approve" else "hold"
        try:
            queue.set_status(item, target)
        except queue.InvalidTransition as exc:
            print(f"cannot {args.command}: {exc}", file=sys.stderr)
            return 1
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> {target}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli.py -v`
Expected: 5 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest -v`
Expected: all tests from Tasks 2–6 pass (config, backlog, pipeline item, slots, cli).

- [ ] **Step 6: Commit**

```bash
git add gevideo/cli.py tests/test_cli.py
git commit -m "feat: add gevideo CLI for backlog and approval"
```

---

### Task 7: The `ge-content-queue` skill

**Files:**
- Create: `ge-video-pipeline/skills/ge-content-queue/SKILL.md`

This skill teaches Claude to drive the CLI for the human-facing actions: review what's queued, add/promote backlog topics, and approve/reject the day's video. It writes instructions FOR Claude.

- [ ] **Step 1: Write the skill**

`ge-video-pipeline/skills/ge-content-queue/SKILL.md`:
```markdown
---
name: ge-content-queue
description: >
  Manage the Great Elephant Law daily-video content backlog and the
  pending-approval queue. ALWAYS invoke for "content backlog," "video backlog,"
  "what's queued," "queue status," "add a video topic," "promote a topic,"
  "approve today's video," "approve the video," or "reject the video." Lists the
  backlog, adds/promotes topics (proposed -> ready), reports how many ready
  topics remain, and approves or rejects a staged video by date. Part of the
  ge-video-pipeline plugin; consumed by ge-video-daily.
---

# ge-content-queue — Backlog & Approval Queue

## STEP 0 — LOCATE THE TOOLS
The backbone CLI lives at `${CLAUDE_PLUGIN_ROOT}/gevideo` and runs via the
plugin's virtualenv. Set:
- `PY="${CLAUDE_PLUGIN_ROOT}/.venv/bin/python"`
- `DATA_DIR="$HOME/.local/share/ge-video"` (or the `data_dir` from
  `~/.config/ge-video/config.json` if set)

All commands take `--data-dir "$DATA_DIR"`.

## STEP 1 — PICK THE ACTION
Run `$PY -m gevideo.cli --data-dir "$DATA_DIR" <command>`:

| Intent | Command |
|---|---|
| Show the backlog | `backlog-list` |
| How many ready topics remain | `queue-status` |
| Add a topic | `backlog-add --title "<title>" --notes "<notes>"` |
| Promote a topic to ready | `backlog-promote --id <id>` |
| Approve the staged video | `approve --date YYYY-MM-DD` |
| Reject (send to hold) | `reject --date YYYY-MM-DD` |

When the attorney says "approve today's video" without a date, use today's date
in the configured timezone.

## STEP 2 — REPORT
Echo the CLI's one-line result back to the attorney. For `queue-status`, if the
ready count is at or below the backlog-low threshold, recommend running
`ge-ideate` to refill the backlog.

## STEP 3 — APPROVAL SEMANTICS
- `approve` only works on an item in `pending_approval`; a HOLD item must be
  fixed and re-staged first. If the CLI reports an illegal transition, explain
  why and do not retry.
- Approving does NOT itself publish — it marks the item `approved`. The
  ge-video-daily / ge-distribute step performs the scheduled upload.
```

- [ ] **Step 2: Validate the plugin still passes**

Run: `cd ~/DW-Marketing-Skills && claude plugin validate ./ge-video-pipeline`
Expected: `✔ Validation passed`.

- [ ] **Step 3: Commit**

```bash
git add ge-video-pipeline/skills/ge-content-queue/SKILL.md
git commit -m "feat: add ge-content-queue skill"
```

---

### Task 8: Wire up the plugin README and final verification

**Files:**
- Create: `ge-video-pipeline/README.md`

- [ ] **Step 1: Write the README**

`ge-video-pipeline/README.md`:
```markdown
# ge-video-pipeline

Daily HeyGen short-form video pipeline for Great Elephant Law. This plugin owns
the content backlog, the per-day pipeline state machine, publish-slot
scheduling, and the approve-then-publish workflow. It reuses the `ge-youtube`
content + compliance skills (ge-ideate, ge-script, ge-shorts, ge-publish).

## Status
- **Plan 1 (this build): backbone** — config, content queue, slot computation,
  `ge-content-queue` skill + CLI. Tested, no external APIs.
- Plan 2: HeyGen generation. Plan 3: YouTube publish. Plan 4: orchestrator +
  notifications + launchd. Plan 5: Opus Clip cross-post + Kit newsletter.

## Setup
```bash
cd ge-video-pipeline
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest          # run the test suite
```

Create `~/.config/ge-video/config.json` (non-secret IDs):
```json
{
  "avatar_id": "<heygen avatar id>",
  "voice_id": "<heygen voice id>",
  "channel_id": "<youtube channel id>",
  "publish_time": "12:00",
  "timezone": "America/Chicago",
  "buffer_days": 3,
  "backlog_low_threshold": 5
}
```
State (backlog + per-day items) is written under `~/.local/share/ge-video/`.

## CLI
```bash
PY=.venv/bin/python
DATA=~/.local/share/ge-video
$PY -m gevideo.cli --data-dir "$DATA" backlog-add --title "DWI checkpoints" --notes "LA"
$PY -m gevideo.cli --data-dir "$DATA" backlog-list
$PY -m gevideo.cli --data-dir "$DATA" backlog-promote --id <id>
$PY -m gevideo.cli --data-dir "$DATA" queue-status
$PY -m gevideo.cli --data-dir "$DATA" approve --date 2026-06-18
```
```

- [ ] **Step 2: Run the full test suite one more time**

Run: `cd ~/DW-Marketing-Skills/ge-video-pipeline && .venv/bin/pytest -v`
Expected: all tests pass.

- [ ] **Step 3: Validate marketplace + plugin**

Run: `cd ~/DW-Marketing-Skills && claude plugin validate . && claude plugin validate ./ge-video-pipeline`
Expected: both `✔ Validation passed`.

- [ ] **Step 4: Commit and push**

```bash
git add ge-video-pipeline/README.md
git commit -m "docs: add ge-video-pipeline README"
git push
```

---

## Plan complete — what ships

A tested `gevideo` backbone (config, backlog, pipeline state machine, slot
computation, CLI) and the `ge-content-queue` skill, registered as a new plugin in
the `dw-marketing` marketplace. You can add and promote topics, stage a pipeline
item, walk it through its statuses, compute its publish slot, and approve/reject
it — all under test, with no external API dependencies.

**Next:** Plan 2 (HeyGen generation) builds `ge-heygen` + `gevideo/heygen.py`
against the current HeyGen API docs, consuming a `ready` topic and producing the
`video.mp4` + `generated` pipeline item this backbone defines.
