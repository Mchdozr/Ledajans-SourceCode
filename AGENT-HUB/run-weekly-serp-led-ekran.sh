#!/usr/bin/env bash
set -euo pipefail
cd /workspace
exec python3 AGENT-HUB/tools/weekly_serp_led_ekran.py "$@"
