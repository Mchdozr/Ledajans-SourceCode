#!/usr/bin/env bash
set -euo pipefail

WORKDIR="/workspace"
LOG_FILE="$WORKDIR/AGENT-HUB/serp-rank-tracker.log"

cd "$WORKDIR"
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] serp-rank-tracker start" >> "$LOG_FILE"
python3 "$WORKDIR/AGENT-HUB/serp_rank_tracker.py" >> "$LOG_FILE" 2>&1
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] serp-rank-tracker done (exit=$?)" >> "$LOG_FILE"
