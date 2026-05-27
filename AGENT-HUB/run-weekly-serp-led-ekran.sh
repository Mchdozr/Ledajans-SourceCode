#!/usr/bin/env bash
# Haftalık cron örneği: 0 6 * * 1 cd /workspace && bash AGENT-HUB/run-weekly-serp-led-ekran.sh
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 AGENT-HUB/weekly_serp_led_ekran.py
