from __future__ import annotations

import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")

site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
auth = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
headers = {"User-Agent": "LEDAJANS-Backup/1.0"}
slugs = [
    "magaza-vitrin-led-ekran",
    "fuar-led-ekran",
    "istanbul-led-ekran",
    "gob-led-ekran",
    "cephe-led-ekran",
    "pitch-secim-rehberi",
    "led-ekran",
    "cob-ekran",
    "ic-mekan-led-ekran",
    "dis-mekan-led-ekran",
    "rental-ekran",
]

for slug in slugs:
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": slug, "status": "any"},
        auth=auth,
        headers=headers,
        timeout=30,
    )
    items = r.json() if r.status_code == 200 else []
    if not items:
        print(f"MISSING {slug}")
        continue
    p = items[0]
    meta = p.get("meta") or {}
    raw = (p.get("content") or {}).get("raw") or ""
    el = meta.get("_elementor_data")
    (OUT / f"{slug}.meta.json").write_text(
        json.dumps(
            {
                "id": p["id"],
                "slug": slug,
                "link": p.get("link"),
                "status": p.get("status"),
                "modified": p.get("modified"),
                "elementor": bool(el),
                "raw_len": len(raw),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if raw:
        (OUT / f"{slug}.html").write_text(raw, encoding="utf-8")
    if el:
        text = el if isinstance(el, str) else json.dumps(el, ensure_ascii=False)
        (OUT / f"{slug}.elementor.json").write_text(text, encoding="utf-8")
    print(f"OK {slug} id={p['id']} status={p.get('status')} elementor={bool(el)} raw={len(raw)}")
