#!/usr/bin/env bash
set -euo pipefail
cd /workspace
exec python3 AGENT-HUB/weekly_keyword_rank.py "$@"
