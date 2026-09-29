#!/usr/bin/env python3
import re
import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
url = "https://ledajans.com/?nocache=hero-loop-20260922t1033"
r = requests.get(
    url,
    headers={
        "User-Agent": UA,
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    },
    timeout=45,
)
print("status", r.status_code, "len", len(r.text))
print("cf", r.headers.get("CF-Cache-Status"))
print("age", r.headers.get("Age"))
print("cache-control", r.headers.get("Cache-Control"))
print("litespeed", r.headers.get("X-LiteSpeed-Cache") or r.headers.get("X-Litespeed-Cache"))
print("x-litespeed-tag", (r.headers.get("X-LiteSpeed-Tag") or "")[:120])
html = r.text
print("hero-stant-1920", "hero-stant-1920.mp4" in html)
print("hero-stant-1280", "hero-stant-1280" in html)
print("Firefly", "Firefly" in html)
print("StantVideo", "StantVideo" in html)
print("loop=false JS", "heroVideo.loop = false" in html)
print("loop=true JS", "heroVideo.loop = true" in html)
print("ended listener", "addEventListener('ended'" in html)
print("canplay listener", "addEventListener('canplay'" in html)
print("canplay play()", bool(re.search(r"canplay[\s\S]{0,400}?heroVideo\.play\(\)", html)))
print("html loop attr webkit+loop", bool(re.search(r"webkit-playsinline\s+loop", html)))
print("playedOnce", "playedOnce" in html)
print("widget 122e243", "122e243" in html)

m = re.search(r"<video[^>]*id=[\"']ledajansHeroVideo[\"'][^>]*>", html, re.I)
print("VIDEO_TAG", m.group(0) if m else "MISSING")

# any loop attribute on video tags
for vm in re.finditer(r"<video\b[^>]*>", html, re.I):
    tag = vm.group(0)
    print("VIDEO_ANY", tag[:400])
    if re.search(r"\sloop(\s|=|>|/)", tag, re.I) or 'loop="' in tag.lower() or " loop" in tag.lower():
        print("HAS_LOOP_ATTR", True)

print("--- LOOP LINES ---")
for i, line in enumerate(html.splitlines()):
    low = line.lower()
    if "loop" in low and ("hero" in low or "video" in low or "ledajanshero" in low or "heroVideo" in line):
        print(f"{i+1}: {line.strip()[:220]}")

# extract canplay/ended snippet
idx = html.find("addEventListener('canplay'")
if idx >= 0:
    print("--- CANPLAY SNIPPET ---")
    print(html[idx : idx + 700])
idx2 = html.find("addEventListener('ended'")
if idx2 >= 0:
    print("--- ENDED SNIPPET ---")
    print(html[idx2 : idx2 + 700])
