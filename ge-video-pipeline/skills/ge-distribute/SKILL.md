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
- A Short is just a vertical (9:16) video <= 3 minutes; no special API flag.
- ge-distribute only acts on `approved` items and only sets `scheduled`; it never
  publishes on HOLD or without approval.
