from __future__ import annotations

import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-Audit", "Cache-Control": "no-cache"}

url = "https://ledajans.com/ic-mekan-rgb-panel/"
html = requests.get(url, headers=UA, timeout=30, params={"nc": "1"}).text
(OUT / "live-ic-mekan-rgb-panel.html").write_text(html, encoding="utf-8")

markers = ["İç Mekan RGB LED Paneller", "İç Mekan Flexible LED Paneller", "İç Mekan RGB GOB LED Paneller"]
pos = [(m, html.find(m)) for m in markers]
print(pos)
start = min(p for _, p in pos if p >= 0)
end_m = re.search(r"<footer|elementor-location-footer", html[start:])
seg = html[start : start + end_m.start()] if end_m else html[start:]
hrefs = re.findall(r'href="([^"]*)"', seg)
seen = []
for h in hrefs:
    if h not in seen:
        seen.append(h)
for h in seen:
    print("HREF", h)
if len(sys.argv) > 1:
    for h in seen:
        if not h.startswith("http"):
            continue
        r = requests.get(h, headers=UA, timeout=20, allow_redirects=False)
        print(r.status_code, h, "->", r.headers.get("Location"), r.headers.get("X-Redirect-By"))
