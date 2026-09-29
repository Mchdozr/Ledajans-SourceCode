from __future__ import annotations

import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")

site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
auth = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
H = {"User-Agent": "LEDAJANS-Tpl/1.0"}

ids = [int(x) for x in sys.argv[2:]]
tpl = sys.argv[1]
for pid in ids:
    r = requests.post(f"{site}/wp-json/wp/v2/pages/{pid}", json={"template": tpl}, auth=auth, headers=H, timeout=60)
    print(pid, r.status_code, r.json().get("template") if r.ok else r.text[:200])
requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=H, timeout=60)

for pid in ids:
    link = requests.get(f"{site}/wp-json/wp/v2/pages/{pid}", params={"_fields": "link"}, headers=H, timeout=60).json()["link"]
    t = requests.get(link, headers={**H, "Cache-Control": "no-cache"}, params={"nocache": "1"}, timeout=60).text
    print(link, "h1:", re.findall(r"<h1[^>]*>(.*?)</h1>", t, re.S), "breadcrumb-strip:", "custom-breadcrumb" in t, "header:", "gva-header" in t or "<header" in t, "footer:", "<footer" in t)
