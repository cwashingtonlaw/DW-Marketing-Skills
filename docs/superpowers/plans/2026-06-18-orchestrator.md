# Daily Orchestrator Implementation Plan (Plan 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the manual CLI steps into the autonomous approve-then-publish loop. Add the deterministic glue (`daily-start`, `stage`, `notify-chat`), a Google Chat webhook notifier, the `ge-video-daily` orchestration skill that chains ge-script → ge-heygen → packaging → ge-publish gate → stage-for-approval → notify, and a launchd daily job.

**Architecture:** New testable Python: `queue.consume_next_ready` (pull + mark a backlog topic), `gevideo/notify.py` (`build_approval_message` pure text + `post_chat_webhook` with injectable transport), and three CLI commands — `daily-start` (idempotent: create today's pipeline item from the next ready topic), `stage` (CLEAR→`pending_approval` / HOLD→`hold`, recording the compliance verdict + packaging metadata), and `notify-chat` (post an approval message or arbitrary text to a Google Chat webhook). The `ge-video-daily` skill is the headless entrypoint Claude runs; `bin/` holds the launchd wrapper + plist + installer. Notifications use a Chat webhook (works under launchd with no MCP auth); email is an optional interactive skill step via the Gmail connector.

**Tech Stack:** Python 3.11+ stdlib (`urllib`, `json`, `datetime`), pytest; bash + launchd plist for scheduling (verified with `bash -n` and `plutil -lint`).

**Independently shippable:** at the end, `daily-start` + `stage` + `notify-chat` work by hand, the `ge-video-daily` skill documents the full chain, and `bin/install-launchd.sh` installs a daily timer. All Python logic is covered by network-free tests.

**Compliance invariant (unchanged):** nothing reaches `scheduled` without the automated `ge-publish` gate passing (CLEAR) AND the attorney approving. HOLD never advances to `pending_approval`.

---

### Task 1: `consume_next_ready` queue helper

**Files:**
- Modify: `ge-video-pipeline/gevideo/queue.py` (append function)
- Test: `ge-video-pipeline/tests/test_consume.py`

`consume_next_ready(backlog)` returns the first `ready` topic and marks it `used` (so it's not picked again), or `None` if none are ready.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_consume.py`:
```python
from gevideo.queue import add_topic, promote_topic, consume_next_ready


def test_consume_returns_first_ready_and_marks_used():
    backlog = []
    a = add_topic(backlog, title="A")
    b = add_topic(backlog, title="B")
    promote_topic(backlog, a["id"])
    promote_topic(backlog, b["id"])

    taken = consume_next_ready(backlog)

    assert taken["id"] == a["id"]
    assert backlog[0]["status"] == "used"
    # b is still ready
    assert backlog[1]["status"] == "ready"


def test_consume_skips_proposed_and_used():
    backlog = []
    a = add_topic(backlog, title="A")            # proposed
    b = add_topic(backlog, title="B")
    promote_topic(backlog, b["id"])              # ready
    consume_next_ready(backlog)                  # takes b -> used
    assert consume_next_ready(backlog) is None   # only A (proposed) left


def test_consume_empty_returns_none():
    assert consume_next_ready([]) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_consume.py -q`
Expected: FAIL with `ImportError: cannot import name 'consume_next_ready'`.

- [ ] **Step 3: Implement**

Append to `ge-video-pipeline/gevideo/queue.py` (after `count_ready`):
```python
def consume_next_ready(backlog: list[dict]) -> dict | None:
    for item in backlog:
        if item["status"] == "ready":
            item["status"] = "used"
            return item
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_consume.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/queue.py tests/test_consume.py
git commit -m "feat: add consume_next_ready backlog helper"
```

---

### Task 2: `build_approval_message`

**Files:**
- Create: `ge-video-pipeline/gevideo/notify.py`
- Test: `ge-video-pipeline/tests/test_notify_message.py`

Pure function producing the approval notification subject + body, including the compliance verdict, the video path, the approve/reject instruction, and the manual-post reminder.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_notify_message.py`:
```python
from gevideo.notify import build_approval_message


def _item():
    return {
        "date": "2026-06-18",
        "title": "DWI checkpoint rights",
        "status": "pending_approval",
        "video_path": "/data/pipeline/2026-06-18/video.mp4",
        "compliance_verdict": {"verdict": "CLEAR", "note": ""},
    }


def test_subject_has_date_and_title():
    msg = build_approval_message(_item())
    assert "2026-06-18" in msg["subject"]
    assert "DWI checkpoint rights" in msg["subject"]


def test_body_has_verdict_video_and_manual_reminder():
    body = build_approval_message(_item())["body"]
    assert "CLEAR" in body
    assert "/data/pipeline/2026-06-18/video.mp4" in body
    assert "approve today's video" in body
    assert "Facebook personal" in body
    assert "Instagram personal" in body
    assert "Snapchat" in body


def test_handles_missing_verdict():
    item = _item()
    item["compliance_verdict"] = None
    body = build_approval_message(item)["body"]
    assert "Compliance:" in body  # does not crash on None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_notify_message.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'gevideo.notify'`.

- [ ] **Step 3: Write minimal implementation**

`ge-video-pipeline/gevideo/notify.py`:
```python
"""Approval-notification message building and Google Chat webhook delivery."""
from __future__ import annotations


def build_approval_message(item: dict) -> dict:
    verdict = item.get("compliance_verdict")
    if isinstance(verdict, dict):
        vtext = verdict.get("verdict", "?")
    else:
        vtext = verdict if verdict else "(none)"

    date = item.get("date", "")
    title = item.get("title", "(untitled)")
    subject = f"[GE Video] Approve {date}: {title}"
    body = "\n".join([
        f"Daily video ready for approval — {date}",
        f"Title: {title}",
        f"Status: {item.get('status')}",
        f"Compliance: {vtext}",
        f"Video: {item.get('video_path')}",
        "",
        'To publish: run "approve today\'s video" (or reject to send to HOLD).',
        "",
        "Manual posts (no tool can automate these): "
        "Facebook personal, Instagram personal, Snapchat.",
    ])
    return {"subject": subject, "body": body}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_notify_message.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/notify.py tests/test_notify_message.py
git commit -m "feat: add approval-notification message builder"
```

---

### Task 3: `post_chat_webhook`

**Files:**
- Modify: `ge-video-pipeline/gevideo/notify.py` (append)
- Test: `ge-video-pipeline/tests/test_notify_webhook.py`

`post_chat_webhook(url, text, http=None)` posts `{"text": text}` to a Google Chat incoming webhook. The default transport uses `urllib`; tests inject a fake.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_notify_webhook.py`:
```python
from gevideo.notify import post_chat_webhook


class FakePoster:
    def __init__(self):
        self.calls = []

    def post(self, url, payload):
        self.calls.append((url, payload))
        return 200


def test_post_chat_webhook_sends_text_payload():
    poster = FakePoster()
    status = post_chat_webhook("https://chat.example/hook", "hello", http=poster)

    assert status == 200
    url, payload = poster.calls[0]
    assert url == "https://chat.example/hook"
    assert payload == {"text": "hello"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_notify_webhook.py -q`
Expected: FAIL with `ImportError: cannot import name 'post_chat_webhook'`.

- [ ] **Step 3: Append the implementation to `notify.py`**

Add to the end of `ge-video-pipeline/gevideo/notify.py`:
```python
import json
import urllib.request


class _UrllibPoster:
    def post(self, url: str, payload: dict) -> int:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req) as resp:
            return resp.status


def post_chat_webhook(webhook_url: str, text: str, http=None) -> int:
    http = http or _UrllibPoster()
    return http.post(webhook_url, {"text": text})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_notify_webhook.py -q`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/notify.py tests/test_notify_webhook.py
git commit -m "feat: add Google Chat webhook poster"
```

---

### Task 4: `daily-start` CLI command

**Files:**
- Modify: `ge-video-pipeline/gevideo/cli.py`
- Test: `ge-video-pipeline/tests/test_cli_daily.py`

`daily-start` is idempotent: if today's item exists it no-ops; otherwise it consumes the next ready topic and creates the pipeline item. Exit code `2` signals an empty backlog (so the orchestrator notifies "refill").

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_cli_daily.py`:
```python
import gevideo.cli as cli
from gevideo.queue import (
    add_topic, promote_topic, save_backlog, load_backlog,
    load_pipeline_item,
)


def test_daily_start_creates_item_and_consumes_topic(tmp_path):
    backlog = []
    t = add_topic(backlog, title="Field sobriety myths")
    promote_topic(backlog, t["id"])
    save_backlog(tmp_path, backlog)

    code = cli.main(["--data-dir", str(tmp_path), "daily-start",
                     "--date", "2026-06-18"])
    assert code == 0

    item = load_pipeline_item(tmp_path, "2026-06-18")
    assert item["title"] == "Field sobriety myths"
    assert item["status"] == "generated"
    assert load_backlog(tmp_path)[0]["status"] == "used"


def test_daily_start_is_idempotent(tmp_path):
    backlog = []
    a = add_topic(backlog, title="A")
    b = add_topic(backlog, title="B")
    promote_topic(backlog, a["id"])
    promote_topic(backlog, b["id"])
    save_backlog(tmp_path, backlog)

    cli.main(["--data-dir", str(tmp_path), "daily-start", "--date", "2026-06-18"])
    cli.main(["--data-dir", str(tmp_path), "daily-start", "--date", "2026-06-18"])

    # Only ONE topic consumed despite two runs for the same date
    used = [t for t in load_backlog(tmp_path) if t["status"] == "used"]
    assert len(used) == 1
    assert load_pipeline_item(tmp_path, "2026-06-18")["title"] == "A"


def test_daily_start_empty_backlog_returns_2(tmp_path):
    save_backlog(tmp_path, [])  # no ready topics
    code = cli.main(["--data-dir", str(tmp_path), "daily-start",
                     "--date", "2026-06-18"])
    assert code == 2
    assert load_pipeline_item(tmp_path, "2026-06-18") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_daily.py -q`
Expected: FAIL — unknown subcommand `daily-start` (argparse SystemExit) or attribute errors.

- [ ] **Step 3: Update `cli.py`**

Register the parser (after the `youtube-schedule` parser block, before `args = parser.parse_args(argv)`):
```python
    p_daily = sub.add_parser("daily-start")
    p_daily.add_argument("--date", default=None)
```

Add the handler (before the final `return 1`):
```python
    if args.command == "daily-start":
        target_date = args.date or date.today().isoformat()
        if queue.load_pipeline_item(data_dir, target_date) is not None:
            existing = queue.load_pipeline_item(data_dir, target_date)
            print(f"{target_date} already started: {existing['title']} "
                  f"({existing['status']})")
            return 0
        backlog = queue.load_backlog(data_dir)
        topic = queue.consume_next_ready(backlog)
        if topic is None:
            print("backlog empty: no ready topic. Run ge-ideate to refill.",
                  file=sys.stderr)
            return 2
        queue.save_backlog(data_dir, backlog)
        item = queue.create_pipeline_item(target_date, topic)
        queue.save_pipeline_item(data_dir, item)
        print(f"{target_date} started: {topic['title']}")
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_daily.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/cli.py tests/test_cli_daily.py
git commit -m "feat: add idempotent daily-start CLI command"
```

---

### Task 5: `stage` CLI command

**Files:**
- Modify: `ge-video-pipeline/gevideo/cli.py`
- Test: `ge-video-pipeline/tests/test_cli_stage.py`

`stage` records the compliance verdict and (CLEAR) moves the item to `pending_approval` or (HOLD) to `hold`, and writes packaging metadata (title/description/tags) when provided.

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_cli_stage.py`:
```python
import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item,
)


def test_stage_clear_moves_to_pending_and_records_metadata(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)

    code = cli.main([
        "--data-dir", str(tmp_path), "stage", "--date", "2026-06-18",
        "--verdict", "CLEAR", "--note", "ok",
        "--title", "Real title", "--description", "desc", "--tags", "a, b ,c",
    ])
    assert code == 0
    updated = load_pipeline_item(tmp_path, "2026-06-18")
    assert updated["status"] == "pending_approval"
    assert updated["compliance_verdict"] == {"verdict": "CLEAR", "note": "ok"}
    assert updated["metadata"]["title"] == "Real title"
    assert updated["metadata"]["description"] == "desc"
    assert updated["metadata"]["tags"] == ["a", "b", "c"]


def test_stage_hold_moves_to_hold(tmp_path):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "x"})
    save_pipeline_item(tmp_path, item)

    code = cli.main([
        "--data-dir", str(tmp_path), "stage", "--date", "2026-06-18",
        "--verdict", "HOLD", "--note", "banned phrase",
    ])
    assert code == 0
    updated = load_pipeline_item(tmp_path, "2026-06-18")
    assert updated["status"] == "hold"
    assert updated["compliance_verdict"]["verdict"] == "HOLD"


def test_stage_missing_item_returns_1(tmp_path):
    code = cli.main([
        "--data-dir", str(tmp_path), "stage", "--date", "2099-01-01",
        "--verdict", "CLEAR",
    ])
    assert code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_stage.py -q`
Expected: FAIL — unknown subcommand `stage`.

- [ ] **Step 3: Update `cli.py`**

Register the parser (after the `daily-start` parser block):
```python
    p_stage = sub.add_parser("stage")
    p_stage.add_argument("--date", required=True)
    p_stage.add_argument("--verdict", required=True, choices=["CLEAR", "HOLD"])
    p_stage.add_argument("--note", default="")
    p_stage.add_argument("--title", default=None)
    p_stage.add_argument("--description", default=None)
    p_stage.add_argument("--tags", default=None)
```

Add the handler (before the final `return 1`):
```python
    if args.command == "stage":
        item = queue.load_pipeline_item(data_dir, args.date)
        if item is None:
            print(f"no pipeline item for {args.date}", file=sys.stderr)
            return 1
        target = "pending_approval" if args.verdict == "CLEAR" else "hold"
        try:
            queue.set_status(item, target)
        except queue.InvalidTransition as exc:
            print(f"cannot stage: {exc}", file=sys.stderr)
            return 1
        item["compliance_verdict"] = {"verdict": args.verdict, "note": args.note}
        if args.title is not None:
            item["metadata"]["title"] = args.title
        if args.description is not None:
            item["metadata"]["description"] = args.description
        if args.tags is not None:
            item["metadata"]["tags"] = [t.strip() for t in args.tags.split(",")
                                        if t.strip()]
        queue.save_pipeline_item(data_dir, item)
        print(f"{args.date} -> {target} ({args.verdict})")
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_stage.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gevideo/cli.py tests/test_cli_stage.py
git commit -m "feat: add stage CLI command (compliance verdict + metadata)"
```

---

### Task 6: `notify-chat` CLI command

**Files:**
- Modify: `ge-video-pipeline/gevideo/cli.py`
- Test: `ge-video-pipeline/tests/test_cli_notify.py`

`notify-chat` posts either an arbitrary `--text` or the approval message for `--date` to a Google Chat webhook (from `--webhook-url` or the `GCHAT_WEBHOOK_URL` secret).

- [ ] **Step 1: Write the failing test**

`ge-video-pipeline/tests/test_cli_notify.py`:
```python
import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, set_status,
)


def test_notify_chat_text_posts_raw(tmp_path, monkeypatch):
    sent = {}
    monkeypatch.setattr(cli.notify, "post_chat_webhook",
                        lambda url, text, **kw: sent.update(url=url, text=text) or 200)

    code = cli.main([
        "--data-dir", str(tmp_path), "notify-chat",
        "--text", "backlog empty", "--webhook-url", "https://hook",
    ])
    assert code == 0
    assert sent["url"] == "https://hook"
    assert sent["text"] == "backlog empty"


def test_notify_chat_date_posts_approval_message(tmp_path, monkeypatch):
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "Hook"})
    set_status(item, "pending_approval")
    item["video_path"] = "/v.mp4"
    item["compliance_verdict"] = {"verdict": "CLEAR", "note": ""}
    save_pipeline_item(tmp_path, item)

    sent = {}
    monkeypatch.setattr(cli.notify, "post_chat_webhook",
                        lambda url, text, **kw: sent.update(text=text) or 200)

    code = cli.main([
        "--data-dir", str(tmp_path), "notify-chat",
        "--date", "2026-06-18", "--webhook-url", "https://hook",
    ])
    assert code == 0
    assert "Hook" in sent["text"]
    assert "Facebook personal" in sent["text"]


def test_notify_chat_requires_text_or_date(tmp_path):
    code = cli.main([
        "--data-dir", str(tmp_path), "notify-chat", "--webhook-url", "https://hook",
    ])
    assert code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli_notify.py -q`
Expected: FAIL — unknown subcommand `notify-chat`.

- [ ] **Step 3: Update `cli.py`**

Add to the imports at the top: `from gevideo import notify`.

Register the parser (after the `stage` parser block):
```python
    p_notify = sub.add_parser("notify-chat")
    p_notify.add_argument("--date", default=None)
    p_notify.add_argument("--text", default=None)
    p_notify.add_argument("--webhook-url", default=None)
```

Add the handler (before the final `return 1`):
```python
    if args.command == "notify-chat":
        url = args.webhook_url or get_secret("GCHAT_WEBHOOK_URL")
        if args.text:
            message = args.text
        elif args.date:
            item = queue.load_pipeline_item(data_dir, args.date)
            if item is None:
                print(f"no pipeline item for {args.date}", file=sys.stderr)
                return 1
            msg = notify.build_approval_message(item)
            message = f"{msg['subject']}\n\n{msg['body']}"
        else:
            print("notify-chat needs --text or --date", file=sys.stderr)
            return 1
        notify.post_chat_webhook(url, message)
        print("chat notified")
        return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli_notify.py -q`
Expected: 3 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add gevideo/cli.py tests/test_cli_notify.py
git commit -m "feat: add notify-chat CLI command"
```

---

### Task 7: The `ge-video-daily` orchestrator skill

**Files:**
- Create: `ge-video-pipeline/skills/ge-video-daily/SKILL.md`

- [ ] **Step 1: Write the skill**

`ge-video-pipeline/skills/ge-video-daily/SKILL.md`:
```markdown
---
name: ge-video-daily
description: >
  Produce today's Great Elephant Law short video end-to-end and stage it for
  attorney approval. ALWAYS invoke for "run today's video," "daily video job,"
  "make today's short," or when the launchd daily job fires. Pulls the next
  backlog topic, writes a compliant Short script, renders it with the attorney's
  HeyGen avatar, packages metadata, runs the ge-publish compliance gate, stages
  the result, and notifies the attorney for approval. Orchestrates ge-script,
  ge-shorts, ge-package, ge-seo, ge-publish, ge-heygen, and ge-distribute.
---

# ge-video-daily — Daily Video Orchestrator

Drive the whole pipeline for ONE day. Use the plugin venv for every CLI call:
```
PY="${CLAUDE_PLUGIN_ROOT}/.venv/bin/python"
DATA_DIR="$HOME/.local/share/ge-video"
CFG="$HOME/.config/ge-video/config.json"
GE() { "$PY" -m gevideo.cli --data-dir "$DATA_DIR" "$@"; }
```

## STEP 1 — START THE DAY (pull a topic)
Run `GE daily-start`.
- Exit 0, "already started": today's item exists — continue from wherever it is
  (don't regenerate). Inspect `$DATA_DIR/pipeline/<today>/metadata.json`.
- **Exit 2 (empty backlog):** notify and STOP —
  `GE notify-chat --text "Backlog empty — run ge-ideate to add topics. No video today."`
  Then tell the attorney. Do not fabricate a topic.
- Exit 0 with "started: <title>": proceed with that topic.

## STEP 2 — SCRIPT (ge-script → ge-shorts)
Invoke **ge-script** then **ge-shorts** to write a 30–60s vertical Short script
for the topic, applying **ge-compliance** (and ge-compliance-la). Produce the
SPOKEN words only (no `[B-ROLL]`/timecodes), <= 1500 characters. Write them to
`$DATA_DIR/pipeline/<today>/script.txt`.

## STEP 3 — RENDER (ge-heygen)
`GE heygen-generate --date <today> --script-file "$DATA_DIR/pipeline/<today>/script.txt" --config "$CFG"`
This downloads `video.mp4` and records it on the item. If it errors, notify and
stop (do not stage).

## STEP 4 — PACKAGE (ge-package → ge-seo)
Invoke **ge-package** and **ge-seo** to produce the title (< 60 chars), a 200+
word description with the disclaimer block, and tags (broad + geo + brand).

## STEP 5 — COMPLIANCE GATE (ge-publish)
Invoke **ge-publish** on the script + packaging. It returns CLEAR or HOLD.

## STEP 6 — STAGE
- CLEAR: `GE stage --date <today> --verdict CLEAR --title "<title>" --description "<desc>" --tags "<t1,t2,...>"`
- HOLD:  `GE stage --date <today> --verdict HOLD --note "<blockers>"`
(HOLD moves the item to `hold` and does NOT enter the approval queue.)

## STEP 7 — NOTIFY FOR APPROVAL
`GE notify-chat --date <today>` — sends the approval message (title, compliance
verdict, video path, approve/reject instruction, manual-post reminder) to Google
Chat. **If running interactively** (not the headless launchd job) and the Gmail
connector is available, ALSO send the attorney an email with the same content and
the video attached/linked — headless runs may lack the connector, so Chat is the
guaranteed channel.

## STEP 8 — STOP (await approval)
Do NOT publish. The attorney approves later via **ge-content-queue**
("approve today's video"), which then triggers **ge-distribute** to schedule the
YouTube upload. ge-video-daily ends after notifying.

## INVARIANTS
- Never schedule/publish here. Staging + notification only.
- HOLD never reaches `pending_approval`.
- Only the attorney's own HeyGen avatar/voice (ge-compliance-la spokesperson rule).
```

- [ ] **Step 2: Validate the plugin**

Run: `cd ~/DW-Marketing-Skills && claude plugin validate ./ge-video-pipeline`
Expected: `✔ Validation passed`.

- [ ] **Step 3: Commit**

```bash
git add ge-video-pipeline/skills/ge-video-daily/SKILL.md
git commit -m "feat: add ge-video-daily orchestrator skill"
```

---

### Task 8: launchd daily job (wrapper + plist + installer)

**Files:**
- Create: `ge-video-pipeline/bin/ge-video-daily.sh`
- Create: `ge-video-pipeline/bin/com.greatelephant.gevideo.daily.plist`
- Create: `ge-video-pipeline/bin/install-launchd.sh`

- [ ] **Step 1: Create the wrapper script**

`ge-video-pipeline/bin/ge-video-daily.sh`:
```bash
#!/usr/bin/env bash
# Daily Great Elephant Law video job. Invoked by launchd; runs the
# ge-video-daily skill headlessly via the Claude CLI.
set -euo pipefail

# launchd has a minimal PATH; add the usual locations for claude/python.
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

LOG="$HOME/.local/share/ge-video/daily.log"
mkdir -p "$(dirname "$LOG")"

{
  echo "=== ge-video-daily start $(date -u +%FT%TZ) ==="
  claude -p "Run the ge-video-daily skill to produce today's Great Elephant Law short video and stage it for approval."
  echo "=== ge-video-daily done $(date -u +%FT%TZ) ==="
} >> "$LOG" 2>&1
```

- [ ] **Step 2: Create the plist template**

`ge-video-pipeline/bin/com.greatelephant.gevideo.daily.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.greatelephant.gevideo.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>PLACEHOLDER_SCRIPT_PATH</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>PLACEHOLDER_LOG</string>
    <key>StandardErrorPath</key>
    <string>PLACEHOLDER_LOG</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

- [ ] **Step 3: Create the installer**

`ge-video-pipeline/bin/install-launchd.sh`:
```bash
#!/usr/bin/env bash
# Render the plist with absolute paths and load it as a user LaunchAgent.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/ge-video-daily.sh"
LOG="$HOME/.local/share/ge-video/launchd.log"
PLIST_SRC="$HERE/com.greatelephant.gevideo.daily.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.greatelephant.gevideo.daily.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$(dirname "$LOG")"
chmod +x "$SCRIPT"
sed -e "s#PLACEHOLDER_SCRIPT_PATH#$SCRIPT#g" \
    -e "s#PLACEHOLDER_LOG#$LOG#g" \
    "$PLIST_SRC" > "$PLIST_DST"

launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"

echo "Installed launchd job: com.greatelephant.gevideo.daily (daily 06:00)"
echo "Wrapper: $SCRIPT"
echo "Logs:    $LOG  and  $HOME/.local/share/ge-video/daily.log"
echo "Test now: launchctl start com.greatelephant.gevideo.daily"
```

- [ ] **Step 4: Verify syntax**

Run:
```bash
cd ~/DW-Marketing-Skills/ge-video-pipeline
bash -n bin/ge-video-daily.sh
bash -n bin/install-launchd.sh
plutil -lint bin/com.greatelephant.gevideo.daily.plist
chmod +x bin/ge-video-daily.sh bin/install-launchd.sh
```
Expected: no syntax errors; `plutil` prints `OK`.

- [ ] **Step 5: Commit**

```bash
git add ge-video-pipeline/bin
git commit -m "feat: add launchd daily job (wrapper, plist, installer)"
```

---

### Task 9: README, version bump, final verification

**Files:**
- Modify: `ge-video-pipeline/README.md`
- Modify: `ge-video-pipeline/.claude-plugin/plugin.json` (0.3.0 → 0.4.0)
- Modify: `.claude-plugin/marketplace.json` (ge-video-pipeline 0.3.0 → 0.4.0)

- [ ] **Step 1: Bump versions**

In `ge-video-pipeline/.claude-plugin/plugin.json` change `"version": "0.3.0"` to `"version": "0.4.0"`.
In `.claude-plugin/marketplace.json`, change the `ge-video-pipeline` entry's `"version": "0.3.0"` to `"version": "0.4.0"`.

- [ ] **Step 2: Update the README**

In `ge-video-pipeline/README.md`, replace the Plan 3 / Plan 4 status lines:
```markdown
- **Plan 3: YouTube publish — DONE.** `gevideo.youtube` adapter + `ge-distribute`
  skill + `youtube-schedule` CLI. Uploads private with a scheduled `publishAt`.
- **Plan 4: orchestrator — DONE.** `ge-video-daily` skill chains the whole flow;
  `daily-start`/`stage`/`notify-chat` CLI + Google Chat notifier + launchd job.
- Plan 5: Opus Clip cross-post + Kit newsletter.
```

Add this section after the `## YouTube scheduling` section:
```markdown
## Daily automation
The `ge-video-daily` skill runs the whole loop for one day: pull topic → script
(ge-script/ge-shorts) → render (ge-heygen) → package (ge-package/ge-seo) →
compliance gate (ge-publish) → stage → notify for approval. It never publishes;
the attorney approves via `ge-content-queue`, which triggers `ge-distribute`.

Notifications go to **Google Chat** via an incoming webhook — set
`GCHAT_WEBHOOK_URL` in `~/.config/ge-video/secrets.json` (or pass `--webhook-url`).
Email is an optional interactive step via the Gmail connector.

Install the daily timer (macOS launchd, runs 06:00):
```bash
ge-video-pipeline/bin/install-launchd.sh
# test immediately:
launchctl start com.greatelephant.gevideo.daily
tail -f ~/.local/share/ge-video/daily.log
```
Run a one-off without launchd: `claude -p "Run the ge-video-daily skill ..."`.
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
git commit -m "docs: update README and bump ge-video-pipeline to 0.4.0"
git push -u origin feat/orchestrator
```

---

## Plan complete — what ships

The autonomous daily loop: `daily-start` (idempotent topic pull), `stage`
(verdict + metadata), `notify-chat` (Google Chat), the `consume_next_ready` and
`build_approval_message`/`post_chat_webhook` helpers, the `ge-video-daily`
orchestrator skill that chains script → render → package → compliance → stage →
notify, and a launchd daily job — plugin bumped to 0.4.0. All Python is covered
by network-free tests. The attorney still approves before anything schedules.

**Next:** Plan 5 adds the v2 distribution adapters (Opus Clip cross-post + Kit
newsletter) behind the existing ge-distribute interface, scheduled to the video's
go-live time.
