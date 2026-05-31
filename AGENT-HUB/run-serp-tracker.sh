#!/usr/bin/env bash
# Cron / automation: günlük SERP ölçümü + Pazartesi haftalık özet
set -euo pipefail
WORKDIR="/workspace"
LOG_FILE="$WORKDIR/AGENT-HUB/serp-tracker.log"

cd "$WORKDIR"
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] serp-tracker start" >> "$LOG_FILE"
python3 "$WORKDIR/AGENT-HUB/serp_rank_tracker.py" --weekly >> "$LOG_FILE" 2>&1 || true
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] serp-tracker done" >> "$LOG_FILE"
