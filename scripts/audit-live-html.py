#!/usr/bin/env python3
"""Canli HTML asset ozeti — mobil vs desktop."""
from __future__ import annotations

import re
import sys

import requests

UA_M = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
UA_D = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def analyze(name: str, ua: str) -> dict:
    h = requests.get(
        "https://ledajans.com/",
        headers={"User-Agent": ua, "Cache-Control": "no-cache", "Pragma": "no-cache"},
        timeout=45,
    ).text
    head = h.split("</head>")[0] if "</head>" in h else h[:12000]
    styles = re.findall(r"<link[^>]+rel=['\"]stylesheet['\"][^>]*>", h, re.I)
    scripts = re.findall(r"<script[^>]+src=['\"]([^'\"]+)", h, re.I)
    head_scripts = re.findall(r"<script[^>]+src=['\"]([^'\"]+)", head, re.I)
    head_css = re.findall(r"href=['\"]([^'\"]+\.css[^'\"]*)", head, re.I)
    out = {
        "name": name,
        "bytes": len(h),
        "gtm_delay": "ledajansGtmLoaded" in h,
        "idle": "ledajansRunWhenIdle" in h,
        "q60": h.count("ldajsn2-mobile-q60.webp"),
        "q72": h.count("ldajsn2-mobile-q72.webp"),
        "stylesheets": len(styles),
        "script_src": len(scripts),
        "head_scripts": head_scripts[:12],
        "head_css_sample": head_css[:15],
        "fa_async": ('font-awesome' in h.lower() or 'fontawesome' in h.lower()) and 'media="print"' in h,
        "chaty": "chaty" in h.lower(),
        "cf7": "contact-form-7" in h.lower(),
        "swiper": "swiper" in h.lower(),
        "picture": "<picture>" in h,
        "seo_title": bool(re.search(r"<title>[^<]+</title>", h, re.I)),
        "meta_desc": 'name="description"' in h.lower() or "name='description'" in h.lower(),
        "canonical": 'rel="canonical"' in h.lower(),
    }
    print("===", name, "html", out["bytes"])
    for k in (
        "gtm_delay", "idle", "q60", "q72", "stylesheets", "script_src",
        "fa_async", "chaty", "cf7", "swiper", "picture", "seo_title", "meta_desc", "canonical",
    ):
        print(f"  {k}:", out[k])
    print("  head_scripts:")
    for s in out["head_scripts"]:
        print("   ", s[:110])
    print("  head_css_sample:")
    for s in out["head_css_sample"]:
        print("   ", s[:110])
    return out


def main() -> int:
    m = analyze("mobile", UA_M)
    d = analyze("desktop", UA_D)
    # Desktop must not get mobile patch
    if d["gtm_delay"] or d["idle"]:
        print("REGRESSION: desktop mobile-patch aliyor")
        return 2
    if not m["gtm_delay"]:
        print("WARN: mobil GTM delay yok")
    print("SPLIT_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
