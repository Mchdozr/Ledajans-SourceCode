#!/usr/bin/env bash
# Haftalık SERP kontrolü — cron: 0 6 * * 1 (Pazartesi 06:00 UTC)
set -euo pipefail
cd /workspace

if python3 scripts/check-serp-led-ekran.py --device desktop; then
  exit 0
fi

# Google CAPTCHA: tarayıcı doğrulaması sonrası manuel sıra ile kaydet
# Örnek: python3 scripts/check-serp-led-ekran.py --rank 1 --device desktop --source manual_web_check
echo "SERP otomatik çekim başarısız; manuel doğrulama gerekli (exit $?)" >&2
exit 1
