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

for pid in (5898, 5899, 5901, 5902, 5903, 5904, 5905):
    p = requests.get(f"{site}/wp-json/wp/v2/pages/{pid}", params={"context": "edit", "_fields": "id,slug,status,template,meta"}, auth=auth, timeout=60).json()
    m = p["meta"]
    print(pid, p["slug"], p["status"], p["template"], "| focus:", m.get("rank_math_focus_keyword"), "| robots:", m.get("rank_math_robots"))
