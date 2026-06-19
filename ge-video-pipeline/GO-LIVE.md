# Go-Live Checklist — ge-video-pipeline

One-time setup to take the daily video pipeline from "built" to "running."
Do these in order. **Do not enable the launchd timer until the manual dry-run
(step 7) succeeds.**

All paths assume the repo at `~/DW-Marketing-Skills`. Shorthand:
```bash
cd ~/DW-Marketing-Skills/ge-video-pipeline
PY=.venv/bin/python
DATA=~/.local/share/ge-video
CFG=~/.config/ge-video/config.json
GE() { $PY -m gevideo.cli --data-dir "$DATA" "$@"; }
```

## 1. Python env
- [ ] `python3 -m venv .venv`
- [ ] `.venv/bin/pip install -e ".[dev,youtube]"`
- [ ] `.venv/bin/pytest -q` → all pass

## 2. HeyGen (avatar + API)
- [ ] Paid HeyGen plan with API access (no free API tier).
- [ ] Create the **custom avatar + voice clone of the responsible attorney**
      (required — LA bars a non-lawyer spokesperson).
- [ ] Note the `avatar_id` and `voice_id` (`/v2/avatars`, `/v2/voices`).
- [ ] Top up PAYG API credits (~$1/min of video).

## 3. YouTube OAuth (START EARLY — verification can take days)
- [ ] Google Cloud project with **YouTube Data API v3** enabled.
- [ ] Create a **Desktop OAuth client**; download to
      `~/.config/ge-video/youtube_client_secret.json`.
- [ ] Add the channel owner as a test user on the consent screen.
- [ ] **Submit the project for API verification** — until it passes, uploads stay
      locked private even past `publishAt`.
- [ ] First-run consent writes `~/.config/ge-video/youtube_token.json` (done
      automatically the first time `youtube-schedule` runs).

## 4. Config + secrets
- [ ] `~/.config/ge-video/config.json`:
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
- [ ] `~/.config/ge-video/secrets.json` (then `chmod 600`):
```json
{
  "HEYGEN_API_KEY": "...",
  "GCHAT_WEBHOOK_URL": "https://chat.googleapis.com/v1/spaces/.../messages?key=...&token=...",
  "KIT_API_KEY": "...               (only if using the newsletter)"
}
```
- [ ] Google Chat: create an **incoming webhook** in the target space → paste as
      `GCHAT_WEBHOOK_URL`.
- [ ] Kit (optional): generate a v4 API key (account → Developer) → `KIT_API_KEY`.
- [ ] Opus Clip: **nothing to configure** — used manually (the approval notice
      reminds you to load the MP4 into Opus).

## 5. Seed the content backlog
- [ ] Run `ge-ideate` to generate topics, or add them by hand:
      `GE backlog-add --title "..." --notes "..."`
- [ ] Promote the ones you approve: `GE backlog-promote --id <id>`
- [ ] Confirm: `GE queue-status` shows enough `ready` topics.

## 6. Firm-profile / compliance (one-time, in ge-youtube)
- [ ] Fill the **FIRM PROFILE** block in
      `ge-youtube/skills/ge-compliance/SKILL.md` (`CITY_STATE`,
      `RESPONSIBLE_ATTORNEY`, `FIRM_WEBSITE`, `FIRM_PHONE`, `GOVERNING_RULES`).
- [ ] Have the responsible attorney review/approve that file.

## 7. Manual dry-run (DO THIS BEFORE THE TIMER)
- [ ] One-off: `claude -p "Run the ge-video-daily skill to produce today's video and stage it for approval."`
- [ ] Verify: a pipeline item exists at `$DATA/pipeline/<today>/`, `video.mp4`
      downloaded, compliance verdict recorded, and the Google Chat ping arrived.
- [ ] Approve it: `GE approve --date <today>`
- [ ] Schedule it: `GE youtube-schedule --date <today> --config "$CFG"`
- [ ] Confirm in YouTube Studio the video is **private + scheduled** for the slot.
- [ ] (If using Kit) `GE kit-broadcast --date <today>` → confirm a scheduled
      broadcast appears in Kit.
- [ ] Load the MP4 into Opus and schedule the cross-posts by hand.
- [ ] Let it actually go live once; watch the whole loop end to end.

## 8. Enable the daily timer
- [ ] `bin/install-launchd.sh` (installs the LaunchAgent, runs daily 06:00).
- [ ] Test immediately: `launchctl start com.greatelephant.gevideo.daily`
- [ ] Watch: `tail -f ~/.local/share/ge-video/daily.log`

## Daily reality once live
- **Auto:** topic → script → HeyGen render → compliance gate → stage → Chat ping;
  on approval → YouTube scheduled publish (+ Kit newsletter if enabled).
- **You, each morning:** read the Chat ping, run "approve today's video" (or
  reject), then drop the MP4 into Opus for the social cross-posts.

## Guardrails (always true)
- Nothing publishes on a compliance **HOLD** or without your **approval**.
- Only the attorney's own HeyGen avatar/voice is used for ad content.
- Keep `ready` backlog above the threshold (the ping warns you when it's low).
