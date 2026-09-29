from __future__ import annotations

import json
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
H = {"User-Agent": "LEDAJANS-QA/1.0"}

SLUGS = [
    "h2-5-dis-mekan-rgb-panel",
    "h3-076-dis-mekan-rgb-panel",
    "h4-dis-mekan-rgb-panel",
    "h5-dis-mekan-rgb-panel",
    "p10-4s-dis-mekan-rgb-panel",
]

types = requests.get(f"{site}/wp-json/wp/v2/types", auth=auth, headers=H, timeout=30).json()
bases = {k: v.get("rest_base") for k, v in types.items()}
print("types", bases)

check = sys.argv[1:] or ["pages", "posts", bases.get("portfolio") or "portfolio"]
for base in check:
    r = requests.get(
        f"{site}/wp-json/wp/v2/{base}",
        params={"slug": ",".join(SLUGS), "status": "any", "context": "edit", "per_page": 50, "_fields": "id,slug,status,link,type,modified"},
        auth=auth,
        headers=H,
        timeout=30,
    )
    print(base, r.status_code, r.text[:1500])
