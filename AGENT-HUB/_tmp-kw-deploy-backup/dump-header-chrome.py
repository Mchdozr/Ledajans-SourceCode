from __future__ import annotations

import re
from pathlib import Path

import requests

ua = {"User-Agent": "Mozilla/5.0 LEDAJANS-HDR3"}
out = Path(__file__).resolve().parent
for slug, path in [("home", "/"), ("hakkimizda", "/hakkimizda/"), ("blog", "/huidu-c08l-controller/"), ("led", "/led-ekran/")]:
    html = requests.get(f"https://ledajans.com{path}", headers=ua, timeout=40).text
    (out / f"hdr-{slug}.html").write_text(html, encoding="utf-8")
    for pat in [
        r'gva-breadcrumb[\s\S]{0,400}',
        r'page-title[\s\S]{0,300}',
        r'title-info[\s\S]{0,300}',
        r'class="[^"]*h1[^"]*title[^"]*"[\s\S]{0,200}',
        r'<h1[^>]*>[\s\S]{0,120}</h1>',
    ]:
        ms = re.findall(pat, html, re.I)
        print(f"\n=== {slug} {pat[:40]} count={len(ms)} ===")
        for m in ms[:3]:
            print(re.sub(r"\s+", " ", m)[:220])
