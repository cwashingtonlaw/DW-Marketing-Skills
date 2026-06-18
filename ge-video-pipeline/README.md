# ge-video-pipeline

Daily HeyGen short-form video pipeline for Great Elephant Law. This plugin owns
the content backlog, the per-day pipeline state machine, publish-slot
scheduling, and the approve-then-publish workflow. It reuses the `ge-youtube`
content + compliance skills (ge-ideate, ge-script, ge-shorts, ge-publish).

## Status
- **Plan 1: backbone — DONE.** config, content queue, slot computation,
  `ge-content-queue` skill + CLI.
- **Plan 2: HeyGen generation — DONE.** `gevideo.heygen` client + `ge-heygen`
  skill + `heygen-generate` CLI. Renders the attorney's custom avatar+voice.
- **Plan 3: YouTube publish — DONE.** `gevideo.youtube` adapter + `ge-distribute`
  skill + `youtube-schedule` CLI. Uploads private with a scheduled `publishAt`.
- Plan 4: orchestrator + notifications + launchd. Plan 5: Opus Clip cross-post +
  Kit newsletter.

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
