#!/usr/bin/env bash
# Haftalık (veya cron ile) çalıştırın. Aynı ISO haftada ikinci kez yazmaz; tekrar ölçüm için --force kullanın.
set -euo pipefail
cd /workspace
exec python3 AGENT-HUB/serp_weekly_led_ekran.py "$@"
