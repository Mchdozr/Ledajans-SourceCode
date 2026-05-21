#!/usr/bin/env bash
# Haftalık / periyodik SERP proxy ölçümü: "led ekran" + ledajans.com
set -euo pipefail
cd /workspace
exec python3 AGENT-HUB/keyword_serp_led_ekran.py
