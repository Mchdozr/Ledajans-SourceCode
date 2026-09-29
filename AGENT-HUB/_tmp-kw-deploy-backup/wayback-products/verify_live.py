from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
name = sys.argv[1] if len(sys.argv) > 1 else "summary"
summary = json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
ua = {"User-Agent": "LEDAJANS-Verify/1.0", "Cache-Control": "no-cache"}

fails = 0
for it in summary:
    url = f"https://ledajans.com/{it['slug']}/?nocache={int(time.time())}"
    r = requests.get(url, headers=ua, timeout=60, allow_redirects=False)
    h = r.text
    body = h.split("</header>", 1)[-1] if "</header>" in h else h
    h1 = len(re.findall(r"<h1[\s>]", h))
    spec = it["specs"][0].replace("&amp;", "&")
    has_spec = spec in h.replace("&amp;", "&")
    robots = re.search(r'<meta name="robots" content="([^"]+)"', h)
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    left_menu = "indoor-sidebar" in h or "la-model-cards" in h
    ok = r.status_code == 200 and h1 == 1 and has_spec and robots and "noindex" not in robots.group(1)
    fails += not ok
    print(f"{'OK ' if ok else 'ERR'} {r.status_code} h1={h1} spec={has_spec} robots={robots.group(1) if robots else '-'} "
          f"canon={'ok' if canon and canon.group(1).rstrip('/').endswith(it['slug']) else canon.group(1) if canon else '-'} {it['slug']}")
print("FAILS", fails)
