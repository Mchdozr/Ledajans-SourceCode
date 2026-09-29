from __future__ import annotations

import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
out_dir = ROOT / "AGENT-HUB/_tmp-kw-deploy-backup"
ua = {
    "User-Agent": "Mozilla/5.0 LEDAJANS-KW-Verify",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}
bust = str(int(time.time()))
site = "https://ledajans.com"

checks = {
    "/magaza-vitrin-led-ekran/": ["la-kw", "vitrin"],
    "/rental-ekran/": ["fuar-led-ekran", "pitch-secim-rehberi"],
    "/led-ekran/": ["Kullanım senaryoları", "pitch-secim-rehberi", "page-id-5001"],
    "/dis-mekan-led-ekran/": ["cephe-led-ekran", "dis-mekan-led-ekran-fiyatlari-2026"],
}

for path, needles in checks.items():
    url = f"{site}{path}?nocache={bust}"
    rr = requests.get(url, headers=ua, timeout=40, allow_redirects=True)
    html = rr.text
    slug = path.strip("/").replace("/", "-")
    (out_dir / f"verify-{slug}.html").write_text(html, encoding="utf-8")
    found = {n: (n in html) for n in needles}
    print(rr.status_code, rr.url.split("?")[0], found, "final_len", len(html))
