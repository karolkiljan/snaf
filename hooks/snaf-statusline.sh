#!/usr/bin/env bash
# snaf — statusline badge
# Reads ~/.claude/.snaf-active flag and prints [SNAF] when active.
# Add to ~/.claude/settings.json:
#   "statusLine": { "type": "command", "command": "bash /path/to/snaf-statusline.sh" }

FLAG="$HOME/.claude/.snaf-active"

if [ -f "$FLAG" ]; then
  echo "[SNAF]"
fi
