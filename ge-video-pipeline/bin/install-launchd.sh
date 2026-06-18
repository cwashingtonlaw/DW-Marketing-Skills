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
