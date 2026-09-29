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
F = "id,slug,status,link,modified,title,parent"

for base in ("pages", "posts"):
    for status in ("trash", "draft", "private", "pending"):
        r = requests.get(
            f"{site}/wp-json/wp/v2/{base}",
            params={"status": status, "context": "edit", "per_page": 100, "_fields": F},
            auth=auth, headers=H, timeout=40,
        )
        items = r.json() if r.ok else []
        hits = [i for i in items if "rgb" in i["slug"] or "rental" in i["slug"] or "panel" in i["slug"]]
        print(base, status, r.status_code, "total", len(items), "total_hdr", r.headers.get("X-WP-Total"))
        for i in hits:
            print("   ", i["id"], i["status"], i["slug"], i["modified"], i.get("parent"))

r = requests.get(
    f"{site}/wp-json/wp/v2/pages",
    params={"search": "Dış Mekan RGB", "status": "any", "context": "edit", "per_page": 100, "_fields": F},
    auth=auth, headers=H, timeout=40,
)
print("search", r.status_code)
for i in r.json():
    print("   ", i["id"], i["status"], i["slug"], i["modified"], i.get("parent"), i["link"])
