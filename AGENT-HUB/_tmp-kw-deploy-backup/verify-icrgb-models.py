from __future__ import annotations

import io
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-Verify", "Cache-Control": "no-cache"}
created = json.loads((HERE / "icrgb-model-preview" / "created.json").read_text(encoding="utf-8"))

print("== 18 model sayfası")
bad = 0
for slug, pid, link in created:
    r = requests.get(link, headers=UA, timeout=30, allow_redirects=False)
    h = r.text

    def g(p: str) -> str:
        m = re.search(p, h)
        return m.group(1) if m else "-"

    ok = r.status_code == 200 and g(r'rel="canonical" href="([^"]+)"') == link and "noindex" not in g(r'name="robots" content="([^"]+)"')
    bad += not ok
    print(r.status_code, pid, link, "|", g(r"<title>([^<]*)</title>"), "|", g(r'name="robots" content="([^,"]+)'), "| canon_ok" if ok else "| SORUN")

print("== sayfa 5006 linkleri")
page = requests.get("https://ledajans.com/ic-mekan-rgb-panel/", headers=UA, params={"v": str(int(time.time()))}, timeout=30).text
hrefs = []
for h in re.findall(r'href="(https://ledajans\.com/[^"#?]*)"', page):
    if "/wp-content/" in h or "/wp-json/" in h or "/xmlrpc" in h or "/feed" in h or "/comments/" in h:
        continue
    if h not in hrefs:
        hrefs.append(h)
old = {link for _, _, link in created}
print("sayfadaki model linkleri:", len(old & set(hrefs)), "/ 18")
fail = 0
for h in hrefs:
    r = requests.get(h, headers=UA, timeout=30, allow_redirects=False)
    if r.status_code != 200:
        fail += 1
        print("  ", r.status_code, h, "->", r.headers.get("Location"))
print(f"toplam {len(hrefs)} benzersiz iç link, 200 olmayan: {fail}; model sayfa sorunu: {bad}")
