#!/usr/bin/env python3
"""P0 para sayfalarinin canli on-page dogrulamasi."""
from __future__ import annotations

import re
import sys

import requests

PAGES = [
    {
        "slug": "led-ekran",
        "must_have": [
            "LED Ekran Çözümleri ve Fiyatları",
            "led-ekran-fiyatlari-2026",
            "ic-mekan-led-ekran",
            "dis-mekan-led-ekran",
            "rental-ekran",
        ],
        "must_not": ["Profesyonel LED Ekran Çözümleri"],
    },
    {
        "slug": "dis-mekan-led-ekran",
        "must_have": [
            "Dış Mekan LED Ekran",
            "IP65",
            "dis-mekan-led-ekran-fiyatlari-2026",
            "outdoor",
        ],
        "must_not": [],
    },
    {
        "slug": "rental-ekran",
        "must_have": [
            "LED Ekran Kiralama",
            "rental-led-ekran-kiralama-fiyatlari-2026",
            "kiralama",
        ],
        "must_not": [],
    },
    {
        "slug": "ic-mekan-led-ekran",
        "must_have": [
            "İç Mekan LED Ekran",
            "p2-vs-p3-led-ekran",
            "ic-mekan-led-ekran-fiyatlari-2026",
            "indoor",
        ],
        "must_not": ["Rental ekranlarımız hakkında"],
    },
]


def extract_h1(html: str) -> list[str]:
    return [re.sub(r"\s+", " ", m).strip() for m in re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)]


def main() -> int:
    headers = {"User-Agent": "LEDAJANS-Verify-Money-Pages/1.0", "Cache-Control": "no-cache"}
    fail = 0
    for page in PAGES:
        url = f"https://ledajans.com/{page['slug']}/"
        print(f"\n=== /{page['slug']}/ ===")
        try:
            r = requests.get(url, headers=headers, timeout=45)
        except requests.RequestException as e:
            print(f"  HATA: {e}")
            fail += 1
            continue
        print(f"  HTTP {r.status_code}")
        if r.status_code != 200:
            fail += 1
            continue
        html = r.text
        h1s = extract_h1(html)
        print(f"  H1: {h1s[:3] if h1s else '(yok)'}")
        for needle in page["must_have"]:
            ok = needle.lower() in html.lower()
            print(f"  {'OK' if ok else 'EKSIK'}: {needle}")
            if not ok:
                fail += 1
        for needle in page.get("must_not", []):
            bad = needle.lower() in html.lower()
            if bad:
                print(f"  ESKI KALDI: {needle}")
                fail += 1
    print(f"\n{'SONUC: BASARISIZ' if fail else 'SONUC: 4/4 GECTI'} ({fail} eksik)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
