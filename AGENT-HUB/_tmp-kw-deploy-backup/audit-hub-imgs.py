from __future__ import annotations

import re
import time

import requests

ua = {"User-Agent": "Mozilla/5.0 LEDAJANS-HUB-IMG", "Cache-Control": "no-cache"}
html = requests.get(f"https://ledajans.com/led-ekran/?nocache={int(time.time())}", headers=ua, timeout=40).text
print("len", len(html), "senaryo", "Kullanım senaryoları" in html)
srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
# widget-only-ish: uploads
ups = [s for s in srcs if "/wp-content/uploads/" in s]
print("upload imgs", len(ups))
seen = []
for s in ups:
    if s not in seen:
        seen.append(s)

for url in seen:
    try:
        r = requests.get(url, headers=ua, timeout=20, stream=True)
        chunk = next(r.iter_content(64), b"")
        ctype = r.headers.get("Content-Type", "")[:40]
        clen = r.headers.get("Content-Length", "")
        magic = chunk[:12]
        htmlish = b"<html" in chunk.lower() or chunk.startswith(b"<!DOCTYPE") or chunk.startswith(b"<!doctype") or chunk.startswith(b"<!")
        print(f"{r.status_code} {ctype:28} {str(clen):8} html={htmlish} magic={magic!r}  {url.split('/')[-1]}")
        r.close()
    except Exception as exc:
        print("ERR", url.split("/")[-1], type(exc).__name__)
