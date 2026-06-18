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
