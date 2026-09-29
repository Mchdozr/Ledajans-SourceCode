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
H = {"User-Agent": "LEDAJANS-QA/1.0"}
F = "id,slug,status,link,modified,title,categories,lang"


def show(label, params):
    r = requests.get(f"{site}/wp-json/wp/v2/posts", params={"context": "edit", "per_page": 100, "_fields": F, **params}, auth=auth, headers=H, timeout=40)
    print(label, r.status_code, r.headers.get("X-WP-Total"))
    for i in r.json() if r.ok else []:
        print("   ", i["id"], i["status"], i["slug"], i["modified"], i.get("lang"), (i.get("title") or {}).get("raw"))


show("trash p2", {"status": "trash", "page": 2})
show("search mekan rgb", {"status": "any", "search": "Mekan RGB"})
show("search H2.5", {"status": "any", "search": "H2.5"})
show("search P10 4S", {"status": "any", "search": "4S"})
