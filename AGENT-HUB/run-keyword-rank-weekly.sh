#!/usr/bin/env bash
set -euo pipefail
cd /workspace
python3 AGENT-HUB/keyword_rank_weekly.py "$@"
