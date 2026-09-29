from __future__ import annotations

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
headers = {"User-Agent": "LEDAJANS-Backup2/1.0"}

ids = {
    5001: "led-ekran",
    3958: "cob-ekran",
    5002: "ic-mekan-led-ekran",
    5003: "dis-mekan-led-ekran",
    5004: "rental-ekran",
    4986: "gob-led-ekran",
    4969: "magaza-vitrin-led-ekran",
    4992: "fuar-led-ekran",
    4987: "istanbul-led-ekran",
}

for pid, slug in ids.items():
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        params={"context": "edit"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    p = r.json()
    raw = (p.get("content") or {}).get("raw") or ""
    (OUT / f"{slug}-{pid}.html").write_text(raw, encoding="utf-8")
    markers = [
        "la-cob-hub",
        "la-faq-wrap",
        "product-features-section",
        "ledajans-blog-hero",
        "Kullanım senaryoları",
        "la-kw",
        "blog/led-ekran-fiyatlari",
        "pitch-secim-rehberi",
        "cephe-led-ekran",
        "gob-led-ekran",
    ]
    hits = [m for m in markers if m in raw]
    print(f"{slug} id={pid} raw={len(raw)} hits={hits}")
