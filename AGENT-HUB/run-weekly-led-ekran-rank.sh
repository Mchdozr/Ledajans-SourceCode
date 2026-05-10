#!/usr/bin/env bash
# Haftada en fazla bir kez sıra raporu (cron günlük olsa bile).
set -euo pipefail
cd /workspace
exec python3 AGENT-HUB/led_ekran_rank_report.py --min-days-between-runs 7
