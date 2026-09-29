from __future__ import annotations

import re
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
headers = {"User-Agent": "LEDAJANS-Diag/1.0"}
F = "id,status,slug,link,title,modified"

for base in ("pages", "posts"):
    for status in ("trash", "draft,private,pending,future,publish"):
        r = requests.get(f"{site}/wp-json/wp/v2/{base}", params={"status": status, "search": "rental", "per_page": 100, "context": "edit", "_fields": F}, auth=auth, headers=headers, timeout=60)
        print(base, status, r.status_code, flush=True)
        if r.ok:
            for it in r.json():
                print("   ", it["id"], it["status"], it["slug"], it["modified"], flush=True)

for base in ("pages", "posts"):
    r = requests.get(f"{site}/wp-json/wp/v2/{base}", params={"status": "any", "search": "P3.9", "per_page": 100, "context": "edit", "_fields": F}, auth=auth, headers=headers, timeout=60)
    print(base, "search P3.9", r.status_code, flush=True)
    if r.ok:
        for it in r.json():
            print("   ", it["id"], it["status"], it["slug"], it["modified"], flush=True)

idx = requests.get(f"{site}/sitemap_index.xml", headers=headers, timeout=30).text
maps = re.findall(r"<loc>([^<]+)</loc>", idx)
print("sitemaps:", maps, flush=True)
for m in maps:
    body = requests.get(m, headers=headers, timeout=30).text
    for u in re.findall(r"<loc>([^<]+)</loc>", body):
        if re.search(r"p\d-\d|rental|kiralik|kiralama", u):
            print("  ", u, flush=True)
