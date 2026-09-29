from __future__ import annotations

import json
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

SLUGS = [
    "p1-9-ic-mekan-rental-led-ekran",
    "p2-6-ic-mekan-rental-led-ekran",
    "p2-9-ic-mekan-rental-led-ekran",
    "p3-9-ic-mekan-rental-led-ekran",
    "p2-6-dis-mekan-rental-led-ekran",
    "p2-9-dis-mekan-rental-led-ekran",
    "p3-9-dis-mekan-rental-led-ekran",
]

types = requests.get(f"{site}/wp-json/wp/v2/types", auth=auth, headers=headers, timeout=30).json()
print("types:", {k: t.get("rest_base") for k, t in types.items()}, flush=True)
bases = [b for b in ("pages", "posts", "product", "case", "portfolio") if b in {t.get("rest_base") for t in types.values()}]
print("rest bases:", bases, flush=True)

for slug in SLUGS:
    found = []
    for base in bases:
        r = requests.get(
            f"{site}/wp-json/wp/v2/{base}",
            params={"slug": slug, "status": "any", "context": "edit", "_fields": "id,status,link,type,modified,meta"},
            auth=auth, headers=headers, timeout=30,
        )
        if r.ok and isinstance(r.json(), list):
            for it in r.json():
                meta = it.get("meta") or {}
                rm = {k: v for k, v in meta.items() if "robots" in k or "redirect" in k} if isinstance(meta, dict) else {}
                found.append((base, it.get("id"), it.get("status"), it.get("link"), it.get("modified"), rm))
    print(slug, json.dumps(found, ensure_ascii=False))

r = requests.get(f"{site}/wp-json/redirection/v1/redirect", params={"per_page": 200, "filterBy[url]": "rental"}, auth=auth, headers=headers, timeout=30)
print("redirection:", r.status_code)
if r.ok:
    for it in r.json().get("items", []):
        print("  ", it.get("id"), it.get("url"), "->", it.get("action_data"), it.get("enabled"))
