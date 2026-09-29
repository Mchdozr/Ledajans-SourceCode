from __future__ import annotations

import json
import re
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
h = (HERE / "p3-9-ic-mekan-rental-led-ekran.page.html").read_text(encoding="utf-8")
print("styles", len(re.findall(r"<style", h)))
print("widgets", sorted(set(re.findall(r'data-widget_type="([^"]+)"', h))))
print("top sections", len(re.findall(r"elementor-top-section", h)))
print(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))[:1200])

for s in json.loads((HERE / "summary.json").read_text(encoding="utf-8")):
    for u in s["specs"]:
        if u.endswith(".pdf"):
            r = requests.head(u, timeout=20, allow_redirects=False)
            print(r.status_code, r.headers.get("content-type"), u)
