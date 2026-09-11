#!/usr/bin/env python3
from __future__ import annotations

import re
import sys

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"


def main() -> int:
    r = requests.get(
        "https://ledajans.com/",
        headers={"User-Agent": UA, "Cache-Control": "no-cache", "Pragma": "no-cache"},
        timeout=45,
    )
    t = r.text
    print("status", r.status_code, "len", len(t))
    markers = [
        "ledajans-hero-poster",
        "ledajans-hero-content",
        "fair-reveal-active",
        "signistanbul-logo.webp",
        "signistanbul-3.png",
        "fuar-kart-arkaplan.webp",
        "ledajans-home-certs",
        "ledajans-brands",
        "ledajans-about",
        "la-fuar-popup",
        "min(450px, 38vw)",
        "max(600px, 100vh)",
        "max(600px, 100dvh)",
        "hemen her sektördeyiz",
        "LED Ekran Çözümleri",
    ]
    for m in markers:
        print(f"has {m}={m in t}")

    for name in (
        "ledajans-hero",
        "ledajans-home-certs",
        "ledajans-brands",
        "ledajans-about",
        "ledajans-indoor",
    ):
        print(f"idx {name}={t.find(name)}")

    m = re.search(r'<section class="ledajans-hero[^"]*"', t)
    print("hero_tag", m.group(0) if m else "NONE")
    print("poster_div", '<div class="ledajans-hero-poster">' in t)
    print("poster_css", ".ledajans-hero-poster {" in t or ".ledajans-hero-poster{" in t)

    i = t.find("ledajans-hero-fair-logos")
    if i >= 0:
        chunk = t[i : i + 1800]
        img = re.search(r"<img[^>]+ledajans-hero-fair-sign-logo[^>]*>", chunk)
        print("fair_img", img.group(0)[:300] if img else "NO_IMG_NEAR")

    # count hero widgets
    print("hero_section_count", t.count('class="ledajans-hero"') + t.count("class=\"ledajans-hero "))
    print("hero_class_variants", re.findall(r'class="ledajans-hero[^"]*"', t)[:8])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
