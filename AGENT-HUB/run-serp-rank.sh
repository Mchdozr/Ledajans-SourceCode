#!/usr/bin/env bash
# SERP sıra ölçümü — günlük ölçüm, Pazartesi haftalık rapor.
set -euo pipefail
cd /workspace

SNAP_DIR="AGENT-HUB/data/snapshots"
SNAP_FILE="${SNAP_DIR}/led-ekran-tr.html"
mkdir -p "${SNAP_DIR}"

# DuckDuckGo HTML (tr-tr) — Google CAPTCHA bypass için yedek; SERPER_API_KEY varsa script Google kullanır.
for attempt in 1 2 3 4 5; do
  if curl -fsSL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36" \
    -H "Accept-Language: tr-TR,tr;q=0.9" \
    "https://html.duckduckgo.com/html/?q=led+ekran&kl=tr-tr" \
    -o "${SNAP_FILE}" && rg -q 'uddg=' "${SNAP_FILE}"; then
    break
  fi
  sleep $((attempt * 2))
done

EXTRA=()
if rg -q 'uddg=' "${SNAP_FILE}" 2>/dev/null; then
  EXTRA+=(--snapshot-html "${SNAP_FILE}")
fi

python3 AGENT-HUB/serp_rank_check.py --keyword "led ekran" "${EXTRA[@]}" "$@"
