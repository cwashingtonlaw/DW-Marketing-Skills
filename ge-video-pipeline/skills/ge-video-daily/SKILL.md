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

## STEP 2 — SCRIPT (ge-script -> ge-shorts)
Invoke **ge-script** then **ge-shorts** to write a 30-60s vertical Short script
for the topic, applying **ge-compliance** (and ge-compliance-la). Produce the
SPOKEN words only (no `[B-ROLL]`/timecodes), <= 1500 characters. Write them to
`$DATA_DIR/pipeline/<today>/script.txt`.

## STEP 3 — RENDER (ge-heygen)
`GE heygen-generate --date <today> --script-file "$DATA_DIR/pipeline/<today>/script.txt" --config "$CFG"`
This downloads `video.mp4` and records it on the item. If it errors, notify and
stop (do not stage).

## STEP 4 — PACKAGE (ge-package -> ge-seo)
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
