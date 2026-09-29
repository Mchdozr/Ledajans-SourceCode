from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path(__file__).resolve().parent / "media"
MAP = Path(__file__).resolve().parent / "media-urls.json"
name = "magaza-vitrin-led-cadde.webp"
alt = "Mağaza vitrin LED ekran cadde uygulaması"

env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")

site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
auth = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
path = MEDIA / name
with path.open("rb") as fh:
    r = requests.post(
        f"{site}/wp-json/wp/v2/media",
        auth=auth,
        headers={
            "User-Agent": "LEDAJANS-VITRIN/1.0",
            "Content-Disposition": f'attachment; filename="{name}"',
        },
        files={"file": (name, fh, "image/webp")},
        data={"alt_text": alt, "title": alt},
        timeout=180,
    )
print(name, r.status_code)
if r.status_code not in (200, 201):
    print(r.text[:400])
    raise SystemExit(1)
js = r.json()
url = js.get("source_url") or ""
mid = str(js.get("id") or "")
print(url, "id", mid)
existing = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
existing[name] = url
existing[name + ":id"] = mid
MAP.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
