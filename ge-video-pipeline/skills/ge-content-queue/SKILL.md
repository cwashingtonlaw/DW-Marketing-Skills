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
