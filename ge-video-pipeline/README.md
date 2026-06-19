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
- **Plan 4: orchestrator — DONE.** `ge-video-daily` skill chains the whole flow;
  `daily-start`/`stage`/`notify-chat` CLI + Google Chat notifier + launchd job.
- **Plan 5: v2 distribution — DONE.** `gevideo.kit` newsletter (v4 broadcasts) +
  `gevideo.crosspost` webhook handoff, both scheduled to the video's go-live.

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

## v2 distribution (newsletter + cross-post)
Both run after a video is scheduled on YouTube, timed to the same go-live:

- **Kit newsletter:** set `KIT_API_KEY` in `~/.config/ge-video/secrets.json`.
  `GE kit-broadcast --date <date>` schedules a Kit email (v4 broadcasts API)
  linking the YouTube video.
- **Cross-post:** the firm uses **Opus Clip, scheduled manually** — Opus's API
  can't ingest an external finished video, so the approval notification reminds
  the attorney to load the MP4 into Opus and schedule FB Page / Instagram /
  TikTok / LinkedIn / X by hand. To automate instead, set `CROSSPOST_WEBHOOK_URL`
  and run `GE crosspost --date <date>` — it POSTs `{video_url, title,
  description, publish_at, platforms}` to a Zapier / Make / Buffer / Publer
  webhook you control.

```bash
GE() { .venv/bin/python -m gevideo.cli --data-dir ~/.local/share/ge-video "$@"; }
GE kit-broadcast --date 2026-06-18
GE crosspost --date 2026-06-18           # uses CROSSPOST_WEBHOOK_URL
GE crosspost --date 2026-06-18 --platforms "tiktok,x"
```
