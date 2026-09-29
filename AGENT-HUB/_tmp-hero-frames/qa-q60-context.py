#!/usr/bin/env python3
import re
import requests

UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
html = requests.get(
    "https://ledajans.com/",
    headers={"User-Agent": UA, "Cache-Control": "no-cache"},
    timeout=45,
).text
print("count_q60", html.count("ldajsn2-mobile-q60"))
print("count_q72", html.count("ldajsn2-mobile-q72"))
print("count_stant_mobile", html.count("hero-stant-poster-mobile.webp"))
print("count_as_video", len(re.findall(r'as=["\']video["\']', html, re.I)))
for m in re.finditer(r".{0,160}ldajsn2-mobile-q60.{0,160}", html):
    snippet = re.sub(r"\s+", " ", m.group(0))
    print("SNIP:", snippet[:400])
print("preload_links:")
for m in re.finditer(r"<link[^>]+rel=['\"]preload['\"][^>]*>", html, re.I):
    tag = re.sub(r"\s+", " ", m.group(0))
    if "hero" in tag.lower() or "q60" in tag.lower() or "video" in tag.lower() or "stant" in tag.lower() or "ldajsn" in tag.lower():
        print(tag[:500])
