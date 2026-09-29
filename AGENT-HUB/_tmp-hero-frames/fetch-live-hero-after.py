#!/usr/bin/env python3
import re
import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
html = requests.get(
    "https://ledajans.com/?nocache=hero-loop-after-fix",
    headers={"User-Agent": UA, "Cache-Control": "no-cache", "Pragma": "no-cache"},
    timeout=45,
).text
tag = re.search(r"<video[^>]*id=['\"]ledajansHeroVideo['\"][^>]*>", html, re.I | re.S)
print("hero_tag", (tag.group(0) if tag else "MISSING")[:400])
print("hero_tag_has_loop_attr", bool(tag and re.search(r"\sloop(\s|=|/|>)", tag.group(0), re.I)))
print("playedOnce", "playedOnce" in html)
print("canplay_guard", "playedOnce || heroVideo.ended" in html)
print("loop_false", "heroVideo.loop = false" in html)
print("loop_true", "heroVideo.loop = true" in html)
print("1920", "hero-stant-1920.mp4" in html)
print("1280", "hero-stant-1280" in html)
print("Firefly", "Firefly" in html)
print("duration_seek_005", "duration - 0.05" in html)
idx = html.find("addEventListener('canplay'")
print("---CANPLAY---")
print(html[idx:idx+550] if idx >= 0 else "MISSING")
