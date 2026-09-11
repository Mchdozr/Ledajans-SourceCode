#!/usr/bin/env python3
"""Canli footer dogrulama: anasayfa + iletisim + urun sayfasi."""
from __future__ import annotations

import time

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
PAGES = [
    "https://ledajans.com/",
    "https://ledajans.com/iletisim/",
    "https://ledajans.com/ic-mekan-led-ekran/",
    "https://ledajans.com/sertifikalarimiz/",
]


def main() -> int:
    bust = str(int(time.time()))
    ok = True
    for url in PAGES:
        r = requests.get(
            url,
            params={"nocache": bust},
            headers={"User-Agent": UA, "Cache-Control": "no-cache"},
            timeout=45,
        )
        t = r.text
        checks = {
            "status": r.status_code,
            "ledajans-footer": "ledajans-footer" in t,
            "hide_css": "ledajans-hide-old-footer" in t,
            "Hızlı Linkler": "Hızlı Linkler" in t,
            "Galeri": 'class="ledajans-footer-gallery"' in t,
            "snippet": "ledajans-footer-2026" in t or "ledajans-hide-old-footer" in t,
        }
        print(url, checks)
        if r.status_code != 200 or not checks["ledajans-footer"] or not checks["hide_css"]:
            ok = False
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
