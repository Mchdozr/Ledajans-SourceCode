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
out = Path(__file__).parent
for pid in (630, 628):
    r = requests.get(f"{site}/wp-json/wp/v2/posts/{pid}", params={"context": "edit"}, auth=auth, headers=H, timeout=60)
    j = r.json()
    (out / f"post-{pid}-full.json").write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = j.get("meta") or {}
    print(pid, r.status_code, j.get("slug"), j.get("status"), "cats", j.get("categories"), "tags", j.get("tags"), "tpl", j.get("template"), "fmt", j.get("format"), "fm", j.get("featured_media"), "lang", j.get("lang"), "trans", j.get("translations"))
    print("  meta keys", list(meta.keys()))
    print("  content len", len(j["content"]["raw"]), "el len", len(str(meta.get("_elementor_data") or "")))
    print("  keys", [k for k in j.keys()])
