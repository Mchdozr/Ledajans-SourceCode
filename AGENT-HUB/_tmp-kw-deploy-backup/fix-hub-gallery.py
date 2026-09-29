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
headers = {"User-Agent": "LEDAJANS-HUB-GAL/1.0", "Content-Type": "application/json"}

r = requests.get(
    f"{site}/wp-json/wp/v2/pages/5001",
    params={"context": "edit"},
    auth=auth,
    headers=headers,
    timeout=60,
)
r.raise_for_status()
raw = (r.json().get("meta") or {}).get("_elementor_data")
if isinstance(raw, str):
    data = json.loads(raw)
else:
    data = raw
blob = json.dumps(data, ensure_ascii=False)
old = "https://ledajans.com/wp-content/uploads/2023/01/P2.5-550x632.jpg"
new = "https://ledajans.com/wp-content/uploads/2023/01/P2.5.jpg"
print("gallery_thumb", old in blob)
if old in blob:
    blob2 = blob.replace(old, new)
    data = json.loads(blob2)
    payload = {
        "meta": {
            "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            "_elementor_edit_mode": "builder",
        }
    }
    u = requests.post(f"{site}/wp-json/wp/v2/pages/5001", json=payload, auth=auth, headers=headers, timeout=120)
    print("POST", u.status_code)
    c = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("cache", c.status_code)
