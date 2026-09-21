#!/usr/bin/env python3
"""Canlı EN/DE, çöp URL ve TR Hero regresyon kontrolleri."""
from __future__ import annotations

import re
import sys

import requests

ORIGIN = "https://ledajans.com"
UA = "LEDAJANS-I18N-QA/1.0"

PROBES = [
    (f"{ORIGIN}/en/", 200, None, True),
    (f"{ORIGIN}/de/", 200, None, True),
    (f"{ORIGIN}/en/led-screen/", 200, None, True),
    (f"{ORIGIN}/de/led-display/", 200, None, True),
    (f"{ORIGIN}/en/indoor-led-screen/", 200, None, False),
    (f"{ORIGIN}/en/outdoor-led-screen/", 200, None, False),
    (f"{ORIGIN}/en/rental-led-screen/", 200, None, False),
    (f"{ORIGIN}/en/cob-led-screen/", 200, None, False),
    (f"{ORIGIN}/en/contact/", 200, None, False),
    (f"{ORIGIN}/case/", 301, "/projeler", False),
    (f"{ORIGIN}/en/case/", 301, "/projeler", False),
    (f"{ORIGIN}/feed/", 301, None, False),
    (f"{ORIGIN}/gva_template/tr-2/", 410, None, False),
    (f"{ORIGIN}/led/", 301, "/led-ekran", False),
    (f"{ORIGIN}/led-ekran/", 200, None, False),
    (f"{ORIGIN}/", 200, None, False),
]


def hreflang_ok(html: str) -> bool:
    low = html.lower()
    return (
        'hreflang="tr-tr"' in low
        or "hreflang='tr-tr'" in low
        or 'hreflang="tr"' in low
    ) and ("hreflang=\"en" in low or "hreflang='en" in low) and (
        "hreflang=\"de" in low or "hreflang='de" in low
    )


def hero_ok(html: str) -> bool:
    return "ldajsn2-mobile-q60.webp" in html or "hero-poster.webp" in html or "ledajans-video" in html


def one(url: str, want: int, loc: str | None, check_i18n: bool) -> bool:
    r = requests.get(
        url,
        timeout=25,
        allow_redirects=False,
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
    )
    got = r.headers.get("Location", "")
    title = ""
    if r.status_code == 200:
        m = re.search(r"<title>(.*?)</title>", r.text, re.I | re.S)
        title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    ok = r.status_code == want
    if loc and loc not in (got or "").lower():
        ok = False
    extra = ""
    if r.status_code == 200 and check_i18n:
        hl = hreflang_ok(r.text)
        extra = f" hreflang={hl}"
        if not hl:
            ok = False
        h1 = len(re.findall(r"<h1\b", r.text, re.I))
        extra += f" h1={h1}"
        if "lang-item-en" not in r.text or "lang-item-de" not in r.text:
            extra += " menu=MISS"
            ok = False
    if url.rstrip("/") == ORIGIN and r.status_code == 200:
        extra += f" hero={hero_ok(r.text)}"
        if not hero_ok(r.text):
            ok = False
    print(
        f"{'OK' if ok else 'FAIL'} {r.status_code} {url} loc={got[:70]} title={title[:60]!r}{extra}"
    )
    return ok


def main() -> int:
    fails = 0
    for row in PROBES:
        if not one(*row):
            fails += 1
    print("fails", fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
