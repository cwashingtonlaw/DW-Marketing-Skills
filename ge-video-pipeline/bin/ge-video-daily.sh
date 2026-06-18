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
