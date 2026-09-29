from __future__ import annotations

import re
import time

import requests

html = requests.get(
    f"https://ledajans.com/led-ekran/?nocache={int(time.time())}",
    headers={"User-Agent": "Mozilla/5.0 LEDAJANS-HDR-V2", "Cache-Control": "no-cache"},
    timeout=40,
).text

canvases = re.findall(r'<div class="canvas-mobile">([\s\S]*?)</div>\s*</div>\s*</div>', html)
print("canvas_blocks", len(canvases))
# fallback: split by canvas-mobile
parts = html.split('class="canvas-mobile"')
print("splits", len(parts) - 1)
for i, p in enumerate(parts[1:], 1):
    chunk = p[:6000]
    hrefs = re.findall(r'href="([^"]+)"', chunk)
    titles = re.findall(r'menu-title">([^<]+)', chunk)
    print(f"\n--- canvas {i} n_hrefs={len(hrefs)} ---")
    print("titles", titles[:20])
    print("hrefs", hrefs[:20])
    print("has_case", "/case/" in chunk)
    print("has_ic", "/ic-mekan-led-ekran/" in chunk)
    print("has_sertifika", "sertifikalarimiz" in chunk)

# desktop menu
d = re.search(r'id="menu-anamenu-desktop"[\s\S]{0,5000}', html)
if d:
    print("\nDESKTOP hrefs", re.findall(r'href="([^"]+)"', d.group(0))[:20])
    print("DESKTOP titles", re.findall(r'menu-title">([^<]+)', d.group(0)))
