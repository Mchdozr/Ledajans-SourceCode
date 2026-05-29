#!/usr/bin/env bash
# Haftalık "led ekran" SERP sıra ölçümü (cron: 0 6 * * 1 veya mevcut otomasyon)
set -euo pipefail
WORKDIR="/workspace"
LOG_FILE="$WORKDIR/AGENT-HUB/serp-weekly.log"
cd "$WORKDIR"
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] serp-weekly tick" >> "$LOG_FILE"
python3 "$WORKDIR/AGENT-HUB/serp_rank_tracker.py" >> "$LOG_FILE" 2>&1
python3 "$WORKDIR/AGENT-HUB/live_dashboard.py" >> "$LOG_FILE" 2>&1 || true
