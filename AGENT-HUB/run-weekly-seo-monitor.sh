#!/usr/bin/env bash
# Haftalik SEO monitor dongusu — smoke + CWV proxy + baseline hatirlatma
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "=== LEDAJANS weekly SEO monitor $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
python3 scripts/run-weekly-seo-monitor.py || true
python3 scripts/run-cwv-check.py || true
echo ""
echo "Manuel adimlar:"
echo "  1. GSC query-page export -> scripts/update-serp-baseline-from-gsc.py"
echo "  2. npx lighthouse https://ledajans.com/ --form-factor=mobile --output=json"
echo "  3. Ahrefs/GBP haftalik kontrol -> AGENT-HUB/OFFPAGE-EEAT-STRATEGY-2026-07-12.md"
