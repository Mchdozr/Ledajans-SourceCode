#!/usr/bin/env python3
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
html_m = requests.get(
    "https://ledajans.com/",
    headers={"User-Agent": UA_M, "Cache-Control": "no-cache"},
    timeout=45,
).text
html_d = requests.get(
    "https://ledajans.com/",
    headers={"User-Agent": UA_D, "Cache-Control": "no-cache"},
    timeout=45,
).text
for name, html in (("mobile", html_m), ("desktop", html_d)):
    print(f"===== {name} ALL PRELOAD =====")
    for p in re.findall(r"<link[^>]+rel=['\"]preload['\"][^>]*>", html, re.I):
        compact = " ".join(p.split())
        print(compact[:300])
    print("plugin_stant", "hero-stant-poster-mobile.webp" in html)
    print("plugin_atrium_nomedia", "hero-atrium-led-mobile.webp" in html)
    print("plugin_atrium_v2", "hero-atrium-led-mobile-v2.webp" in html)
    print("hero-poster.webp", "hero-poster.webp" in html)
    print("Firefly", "Firefly" in html)
    print("data-src hero", bool(re.search(r'data-src="[^"]+\.mp4"', html)))
    srcs = re.findall(r'data-src="([^"]+)"', html)
    print("data-src", srcs[:5])
