#!/usr/bin/env python3
"""Live signals for hero stant risk review. No secrets printed."""
from __future__ import annotations

import re

import requests

UA_M = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
UA_D = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
ASSETS = [
    "https://ledajans.com/wp-content/uploads/2026/09/hero-stant-1280.mp4",
    "https://ledajans.com/wp-content/uploads/2026/09/hero-stant-poster.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/hero-stant-poster-mobile.webp",
]


def main() -> None:
    for url in ASSETS:
        r = requests.get(url, timeout=20, allow_redirects=False, stream=True)
        loc = r.headers.get("Location", "-")
        cl = r.headers.get("Content-Length", "-")
        ct = r.headers.get("Content-Type", "-")[:60]
        name = url.rsplit("/", 1)[-1]
        print(f"ASSET {r.status_code} cl={cl} ct={ct} loc={loc[:80]} {name}")
        r.close()

    sess = requests.Session()
    html_m = sess.get(
        "https://ledajans.com/",
        headers={"User-Agent": UA_M, "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    html_d = sess.get(
        "https://ledajans.com/",
        headers={"User-Agent": UA_D, "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    for name, html in (("mobile", html_m), ("desktop", html_d)):
        robots = re.search(
            r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)', html, re.I
        )
        canon = re.search(
            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html, re.I
        )
        preloads = re.findall(r"<link[^>]+rel=['\"]preload['\"][^>]*>", html, re.I)
        hero_pre = [
            p.replace("\n", " ")[:220]
            for p in preloads
            if any(x in p.lower() for x in ("hero-", "atrium", "video", ".mp4", "stant"))
        ]
        print(f"--- {name} ---")
        print("robots", robots.group(1) if robots else "-")
        print("canonical", canon.group(1) if canon else "-")
        print("noindex", "noindex" in html.lower())
        print("atrium", "hero-atrium" in html)
        print("stant", "hero-stant" in html)
        print("rawStant", "StantVideo.mp4" in html)
        print("videoPreloadTag", bool(re.search(r'rel=["\']preload["\'][^>]+as=["\']video', html, re.I)))
        print("h1_ok", "LED Ekran Satış" in html)
        print("hero_preloads", hero_pre[:8])


if __name__ == "__main__":
    main()
