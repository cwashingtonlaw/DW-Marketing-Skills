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
