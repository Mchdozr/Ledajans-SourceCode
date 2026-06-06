#!/usr/bin/env bash
# Günlük SERP izleme — cron: 0 6 * * *
set -euo pipefail
cd /workspace

# Google bulut IP'de otomatik engellenebilir; --google-mobile-rank Cloud Agent browser doğrulaması ile verilir.
GOOGLE_RANK="${GOOGLE_MOBILE_RANK:-}"

ARGS=()
if [[ -n "$GOOGLE_RANK" ]]; then
  ARGS+=(--google-mobile-rank "$GOOGLE_RANK")
fi

python3 AGENT-HUB/check-serp-rank.py "${ARGS[@]}"
