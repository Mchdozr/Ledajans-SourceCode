#!/usr/bin/env bash
set -euo pipefail

WORKDIR="/workspace"
LOG_FILE="$WORKDIR/AGENT-HUB/live-dashboard.log"

cd "$WORKDIR"

while true; do
  python3 "$WORKDIR/AGENT-HUB/live_dashboard.py" >> "$LOG_FILE" 2>&1 || true
  sleep 20
done
