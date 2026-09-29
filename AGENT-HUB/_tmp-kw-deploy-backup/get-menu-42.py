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
h = {"User-Agent": "Mozilla/5.0 LEDAJANS-MENU42"}
out = Path(__file__).resolve().parent

r = requests.get(
    f"{site}/wp-json/wp/v2/menu-items",
    params={"menus": 42, "per_page": 100, "context": "edit"},
    auth=auth,
    headers=h,
    timeout=40,
)
print("menu42", r.status_code, "n", len(r.json()) if r.status_code == 200 else r.text[:400])
items = r.json() if r.status_code == 200 else []
(out / "menu-42.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
for it in items:
    title = it.get("title")
    if isinstance(title, dict):
        title = title.get("rendered") or title.get("raw")
    print(
        f"id={it.get('id'):5} parent={it.get('parent'):5} order={it.get('menu_order'):3} "
        f"type={it.get('type'):12} {title!s:40} {it.get('url')}"
    )

# locations
r = requests.get(f"{site}/wp-json/wp/v2/menu-locations", auth=auth, headers=h, timeout=20)
print("\nlocations", r.status_code, r.text[:800] if r.status_code != 200 else json.dumps(r.json(), ensure_ascii=False)[:800])
