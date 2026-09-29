from __future__ import annotations

import re
import sys

import requests

ua = {"User-Agent": "LEDAJANS-LinkScan/1.0"}
for page in sys.argv[1:]:
    h = requests.get(page, headers=ua, timeout=60).text
    links = sorted({l.split("#")[0] for l in re.findall(r'href="(https://ledajans\.com/[^"]*)"', h)
                    if not re.search(r"wp-(content|json|includes)|/feed|xmlrpc|\.(css|js|png|jpe?g|webp|pdf)", l)})
    print("==", page, len(links))
    for l in links:
        if not l:
            continue
        r = requests.get(l, headers=ua, timeout=60, allow_redirects=False)
        loc = r.headers.get("location", "")
        if r.status_code != 200 and loc.rstrip("/") in ("https://ledajans.com", ""):
            print("  HOME/ERR", r.status_code, l)
