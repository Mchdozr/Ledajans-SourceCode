from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path(__file__).resolve().parent / "media"
MAP = Path(__file__).resolve().parent / "media-urls.json"

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
existing = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}

items = {
    "ic-mekan-rgb-panel.webp": "İç mekan RGB LED panel",
    "dis-mekan-rgb-panel.webp": "Dış mekan RGB LED panel IP65",
}
for name, alt in items.items():
    path = MEDIA / name
    with path.open("rb") as fh:
        r = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={**headers, "Content-Disposition": f'attachment; filename="{name}"'},
            files={"file": (name, fh, "image/webp")},
            data={"alt_text": alt, "title": alt},
            timeout=180,
        )
    print(name, r.status_code)
    if r.status_code not in (200, 201):
        print(r.text[:300])
        raise SystemExit(1)
    js = r.json()
    existing[name] = js.get("source_url") or ""
    existing[name + ":id"] = str(js.get("id") or "")
    print(" ", existing[name])

MAP.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
