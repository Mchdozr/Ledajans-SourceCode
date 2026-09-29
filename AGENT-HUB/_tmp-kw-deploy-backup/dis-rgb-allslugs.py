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
H = {"User-Agent": "LEDAJANS-QA/1.0"}
out = []
for base in ("posts", "pages"):
    page = 1
    while True:
        r = requests.get(
            f"{site}/wp-json/wp/v2/{base}",
            params={"status": "publish,draft,private,pending,future,trash", "context": "edit", "per_page": 100, "page": page, "_fields": "id,slug,status,modified,title"},
            auth=auth, headers=H, timeout=60,
        )
        if not r.ok:
            print(base, page, r.status_code, r.text[:200])
            break
        items = r.json()
        for i in items:
            out.append({"type": base, "id": i["id"], "slug": i["slug"], "status": i["status"], "modified": i["modified"], "title": i["title"]["raw"]})
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
Path(__file__).with_name("all-slugs.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("total", len(out))
for i in out:
    s = i["slug"]
    if any(k in s for k in ("dis-mekan", "outdoor", "h2-5", "h3", "h4", "h5", "4s", "rgb")):
        print(i["type"], i["id"], i["status"], s, i["modified"], i["title"].encode("ascii", "replace").decode())
