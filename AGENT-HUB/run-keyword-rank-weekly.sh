#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 AGENT-HUB/keyword_rank_weekly.py
