from __future__ import annotations

import os
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
headers = {"User-Agent": "LEDAJANS-ID-Check/1.0"}

for pid in (5557, 5001, 4986, 4969, 3958):
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        params={"context": "edit"},
        auth=auth,
        headers=headers,
        timeout=30,
    )
    if r.status_code != 200:
        print(f"id={pid} HTTP {r.status_code}")
        continue
    p = r.json()
    raw = (p.get("content") or {}).get("raw") or ""
    rendered = (p.get("content") or {}).get("rendered") or ""
    print(
        f"id={pid} slug={p.get('slug')} status={p.get('status')} link={p.get('link')} "
        f"raw={len(raw)} rendered={len(rendered)} title={p.get('title', {}).get('raw')}"
    )
    snippet = raw[:120].replace("\n", " ") if raw else rendered[:120].replace("\n", " ")
    print(f"  snip: {snippet}")

print("--- slug led-ekran ---")
r = requests.get(
    f"{site}/wp-json/wp/v2/pages",
    params={"slug": "led-ekran", "status": "any", "context": "edit"},
    auth=auth,
    headers=headers,
    timeout=30,
)
for p in r.json() if r.status_code == 200 else []:
    print(p.get("id"), p.get("status"), p.get("link"), p.get("slug"))
