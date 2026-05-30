#!/usr/bin/env bash
# Haftalık "led ekran" sıra raporu — Cursor Automation veya cron ile çalıştırın.
# Önerilen cron: 0 6 * * 1  (her Pazartesi 06:00 UTC)
set -euo pipefail
cd /workspace
exec python3 AGENT-HUB/keyword_rank_weekly.py "$@"
