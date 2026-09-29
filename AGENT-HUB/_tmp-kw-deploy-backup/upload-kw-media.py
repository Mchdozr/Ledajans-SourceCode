from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path(__file__).resolve().parent / "media"
OUT = Path(__file__).resolve().parent / "media-urls.json"

env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")

site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
auth = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
headers = {"User-Agent": "LEDAJANS-KW-Media/1.0"}

alts = {
    "cephe-led-ekran-bina.webp": "Cephe LED ekran IP65 bina uygulaması",
    "led-billboard-otoyol.webp": "LED billboard otoyol panosu",
    "istanbul-cephe-led-kurulum.webp": "İstanbul cephe LED ekran kurulum",
    "pitch-dis-mekan-p10.webp": "P4 P10 dış mekan LED ekran",
    "rental-led-sahne.webp": "Rental LED ekran sahne kabini",
    "gob-led-yuzey.webp": "GOB LED ekran Glue on Board yüzey",
    "cob-led-lobi.webp": "COB LED ekran lobi uygulaması",
    "fuar-led-stand.webp": "Fuar LED ekran stand duvarı",
    "fuar-fuaye-led.webp": "Fuar fuaye LED ekran",
    "magaza-vitrin-led.webp": "Mağaza vitrin LED ekran",
    "avm-led-ekran.webp": "AVM LED ekran atrium",
}

urls: dict[str, str] = {}
for name, alt in alts.items():
    path = MEDIA / name
    with path.open("rb") as fh:
        r = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                **headers,
                "Content-Disposition": f'attachment; filename="{name}"',
            },
            files={"file": (name, fh, "image/webp")},
            data={"alt_text": alt, "title": alt},
            timeout=180,
        )
    print(name, r.status_code, path.stat().st_size)
    if r.status_code not in (200, 201):
        print("ERR", r.text[:300])
        raise SystemExit(1)
    js = r.json()
    urls[name] = js.get("source_url") or ""
    urls[name + ":id"] = str(js.get("id") or "")
    print(" ", urls[name])

OUT.write_text(json.dumps(urls, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", OUT)
