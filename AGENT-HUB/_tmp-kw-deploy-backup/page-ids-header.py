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
h = {"User-Agent": "Mozilla/5.0 LEDAJANS-PAGES"}

slugs = [
    "sertifikalarimiz",
    "ic-mekan-led-ekran",
    "dis-mekan-led-ekran",
    "rental-ekran",
    "ic-mekan-rgb-panel",
    "kontrol-kartlari",
    "guc-kaynaklari",
    "huidu-processor-hdplayer-indir",
    "teknik-destek-videolari",
    "led-ekran",
]
for slug in slugs:
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": slug, "per_page": 5},
        auth=auth,
        headers=h,
        timeout=30,
    )
    items = r.json() if r.status_code == 200 else []
    if not items:
        print(slug, r.status_code, "NONE")
        continue
    for it in items:
        print(f"{slug:40} id={it['id']} link={it.get('link')}")
