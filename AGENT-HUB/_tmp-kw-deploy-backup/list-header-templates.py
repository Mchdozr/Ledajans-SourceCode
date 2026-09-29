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
h = {"User-Agent": "Mozilla/5.0 LEDAJANS-TMPL"}

types = [
    "gva__template",
    "elementor_library",
    "elementor-hf",
    "wp_template",
    "wp_template_part",
]
for t in types:
    r = requests.get(
        f"{site}/wp-json/wp/v2/{t}",
        params={"per_page": 100},
        auth=auth,
        headers=h,
        timeout=40,
    )
    print(f"\n=== {t} {r.status_code} ===")
    if r.status_code != 200:
        print(r.text[:300])
        continue
    items = r.json()
    print("n", len(items))
    for it in items[:40]:
        title = (it.get("title") or {}).get("rendered") or it.get("slug")
        print(
            f"  id={it.get('id')} type={it.get('type')} slug={it.get('slug')} "
            f"status={it.get('status')} title={title}"
        )

r = requests.get(f"{site}/wp-json/wp/v2/types", auth=auth, headers=h, timeout=30)
print("\n=== types ===")
if r.status_code == 200:
    for k, v in r.json().items():
        rest = v.get("rest_base")
        if any(x in k.lower() for x in ["tmpl", "elementor", "gva", "header", "hf"]):
            print(k, rest)
