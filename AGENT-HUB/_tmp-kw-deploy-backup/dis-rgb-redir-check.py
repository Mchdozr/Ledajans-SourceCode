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

for term in ("dis-mekan-rgb", "rgb-panel", "outdoor-rgb"):
    r = requests.get(
        f"{site}/wp-json/redirection/v1/redirect",
        params={"filterBy[url]": term, "per_page": 100},
        auth=auth, headers=H, timeout=40,
    )
    print(term, r.status_code)
    if r.ok:
        for i in r.json().get("items", []):
            print("   ", i["id"], i["url"], "->", i.get("action_data"), i.get("action_code"), "enabled" if i.get("enabled") else "disabled", "hits", i.get("hits"), "grp", i.get("group_id"))

r = requests.get(f"{site}/wp-json/redirection/v1/redirect", params={"per_page": 1}, auth=auth, headers=H, timeout=40)
print("total redirects", r.json().get("total") if r.ok else r.status_code)
r = requests.get(f"{site}/wp-json/rankmath/v1/redirections", auth=auth, headers=H, timeout=40)
print("rankmath redirections route", r.status_code, r.text[:200])
