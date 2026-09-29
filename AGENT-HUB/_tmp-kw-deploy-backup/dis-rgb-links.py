from __future__ import annotations

import re
import sys

import requests

URL = "https://ledajans.com/dis-mekan-rgb-panel/"
H = {"User-Agent": "Mozilla/5.0 LEDAJANS-QA"}

html = requests.get(URL, headers=H, timeout=30).text
i = html.find("Dış Mekan RGB LED Paneller")
print("len", len(html), "section idx", i)
seg = html[i : i + 60000] if i >= 0 else html
hrefs = re.findall(r'href="([^"]+)"', seg)
seen = []
for h in hrefs:
    if h not in seen:
        seen.append(h)
for h in seen:
    print(h)
if len(sys.argv) > 1:
    open(sys.argv[1], "w", encoding="utf-8").write(html)
