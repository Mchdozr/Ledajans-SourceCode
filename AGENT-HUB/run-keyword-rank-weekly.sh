#!/usr/bin/env bash
# Günlük/haftalık SERP kontrolü — cron: 0 6 * * * (06:00 UTC)
set -euo pipefail
cd /workspace
exec python3 AGENT-HUB/keyword_rank_weekly.py
