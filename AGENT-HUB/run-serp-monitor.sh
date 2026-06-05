#!/usr/bin/env bash
# Günlük/haftalık "led ekran" SERP ölçümü (cron: 0 6 * * *)
set -euo pipefail
WORKDIR="/workspace"
LOG_FILE="$WORKDIR/AGENT-HUB/serp-monitor.log"
cd "$WORKDIR"
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] serp-monitor tick" >> "$LOG_FILE"
python3 "$WORKDIR/AGENT-HUB/serp_baseline_monitor.py" >> "$LOG_FILE" 2>&1
python3 "$WORKDIR/AGENT-HUB/live_dashboard.py" >> "$LOG_FILE" 2>&1 || true
