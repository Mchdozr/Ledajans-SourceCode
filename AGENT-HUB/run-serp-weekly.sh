#!/usr/bin/env bash
# Haftalık SERP sıra ölçümü — cron ile çalıştırılabilir.
set -euo pipefail
cd /workspace
python3 AGENT-HUB/serp_rank_tracker.py --keyword "led ekran" --weekly-report
