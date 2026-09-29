from __future__ import annotations

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
r = requests.get(
    f"{site}/wp-json/wp/v2/posts",
    params={"include": "5913,5914,5915,5916,5917", "context": "edit", "_fields": "id,slug,status,meta"},
    auth=auth, timeout=60,
)
for p in r.json():
    m = p["meta"]
    print(p["id"], p["slug"], p["status"], "| focus:", m["rank_math_focus_keyword"].encode("ascii", "replace").decode(), "| desc", len(m["rank_math_description"]))
