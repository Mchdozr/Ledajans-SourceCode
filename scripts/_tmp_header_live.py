#!/usr/bin/env python3
"""Canli header HTML + logo URL durumlari."""
from __future__ import annotations

import re
from pathlib import Path

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
SITE = "https://ledajans.com"


def main() -> int:
    t = requests.get(
        SITE + "/?nocache=hdr",
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    print("has_123bc72", "123bc72" in t)
    print("has_8af5606", "8af5606" in t)
    print("has_elementor-43", "elementor-43" in t)
    print("has_wp-site-header", "wp-site-header" in t)
    print("has_F46F2C_css", "#F46F2C" in t or "#f46f2c" in t)

    m = re.search(r"<header\b[^>]*>.*?</header>", t, flags=re.I | re.S)
    if m:
        chunk = m.group(0)
        print("header_len", len(chunk))
        out = Path(__file__).resolve().parents[1] / "AGENT-HUB" / "BACKUPS" / "2026-09-11-live-header.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(chunk, encoding="utf-8")
        print("wrote", out)
        print("--- imgs ---")
        for src in re.findall(r'<img[^>]+src="([^"]+)"', chunk):
            print(" img", src[:160])
        print("classes", re.findall(r'class="([^"]*header[^"]*)"', chunk)[:15])
        print("data-ids", re.findall(r'data-id="([^"]+)"', chunk)[:20])

    print("--- logo urls ---")
    urls = sorted(set(re.findall(r'https://ledajans\.com/wp-content/uploads/[^"\']+\.(?:png|jpg|jpeg|webp|svg)', t, flags=re.I)))
    logos = [u for u in urls if "logo" in u.lower() or "ledajans" in u.lower()]
    for u in logos[:20]:
        r = requests.head(u, headers={"User-Agent": UA}, timeout=20, allow_redirects=True)
        print(r.status_code, u)

    # also check known paths
    for u in [
        "https://ledajans.com/wp-content/uploads/2022/12/LedajansLogo.png",
        "https://ledajans.com/wp-content/uploads/2022/12/ledajans-logo-web.jpg",
        "https://ledajans.com/wp-content/uploads/2026/02/ledajans-logo.png",
        "https://ledajans.com/wp-content/uploads/2022/12/leadajans-logo2-19-11-2025-16-39-05-scaled.png",
    ]:
        r = requests.get(u, headers={"User-Agent": UA}, timeout=20, allow_redirects=True)
        print("GET", r.status_code, len(r.content), r.headers.get("content-type"), u)

    idx = t.lower().find("wp-site-header")
    if idx != -1:
        print("around_header_idx", idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
