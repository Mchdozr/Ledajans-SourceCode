#!/usr/bin/env bash
set -euo pipefail

WORKDIR="/workspace"
LOG_FILE="$WORKDIR/AGENT-HUB/auto-orchestrator.log"

cd "$WORKDIR"

while true; do
  echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] auto-orchestrator tick" >> "$LOG_FILE"
  python3 "$WORKDIR/AGENT-HUB/auto_orchestrator.py" >> "$LOG_FILE" 2>&1 || true
  sleep 1200
done
