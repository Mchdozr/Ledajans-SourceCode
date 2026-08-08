#!/usr/bin/env bash
set -euo pipefail

WORKDIR="/workspace"
LOG_FILE="$WORKDIR/AGENT-HUB/keyword-rank-weekly.log"

cd "$WORKDIR"

echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] keyword-rank-weekly start" >> "$LOG_FILE"
python3 "$WORKDIR/AGENT-HUB/keyword_rank_weekly.py" "$@" >> "$LOG_FILE" 2>&1
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] keyword-rank-weekly done" >> "$LOG_FILE"
