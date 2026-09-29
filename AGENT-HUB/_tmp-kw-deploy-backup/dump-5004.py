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

p = requests.get(f"{site}/wp-json/wp/v2/pages/5004", params={"context": "edit"}, auth=auth, timeout=60).json()
m = p["meta"]
out = Path(__file__).resolve().parent / "rental-5004"
out.mkdir(exist_ok=True)
(out / "elementor.json").write_text(m["_elementor_data"], encoding="utf-8")
print("page_settings", m.get("_elementor_page_settings"), "conditions", m.get("_elementor_conditions"))
d = json.loads(m["_elementor_data"])
for i, sec in enumerate(d):
    print(i, "section", json.dumps(sec.get("settings"), ensure_ascii=False)[:300])
    for c in sec["elements"]:
        print("   col", json.dumps(c.get("settings"), ensure_ascii=False)[:200])
        for w in c["elements"]:
            (out / f"{i}-{w['id']}.html").write_text(w["settings"].get("html", ""), encoding="utf-8")
