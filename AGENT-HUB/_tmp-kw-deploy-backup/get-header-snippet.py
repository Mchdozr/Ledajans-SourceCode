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
h = {"User-Agent": "Mozilla/5.0 LEDAJANS-HDR-GET"}
out = Path(__file__).resolve().parent

r = requests.get(f"{site}/wp-json/wp/v2/elementor_snippet/5026", auth=auth, headers=h, timeout=40)
print("snippet 5026", r.status_code)
if r.status_code == 200:
    data = r.json()
    (out / "snippet-5026.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("keys", list(data.keys()))
    content = data.get("content", {})
    raw = content.get("raw") if isinstance(content, dict) else ""
    rendered = content.get("rendered") if isinstance(content, dict) else ""
    print("raw_len", len(raw or ""), "rendered_len", len(rendered or ""))
    print("slug", data.get("slug"), "status", data.get("status"))
    meta = data.get("meta") or {}
    print("meta_keys", list(meta.keys())[:40])
    (out / "snippet-5026.html").write_text(raw or rendered or "", encoding="utf-8")

r = requests.get(f"{site}/wp-json/wp/v2/elementor_snippet/5024", auth=auth, headers=h, timeout=40)
print("snippet 5024", r.status_code)

r = requests.get(f"{site}/wp-json/wp/v2/menus", auth=auth, headers=h, timeout=30)
print("\nmenus", r.status_code, r.text[:500] if r.status_code != 200 else "")
if r.status_code == 200:
    for m in r.json():
        print(" MENU", m.get("id"), m.get("slug"), m.get("name"), m.get("count"))

r = requests.get(f"{site}/wp-json/wp/v2/menu-items", params={"per_page": 100}, auth=auth, headers=h, timeout=40)
print("menu-items", r.status_code, "n", len(r.json()) if r.status_code == 200 else r.text[:240])
if r.status_code == 200:
    for it in r.json():
        print(
            f"  id={it.get('id')} parent={it.get('parent')} menu_order={it.get('menu_order')} "
            f"title={it.get('title',{}).get('rendered') if isinstance(it.get('title'), dict) else it.get('title')} "
            f"url={it.get('url')}"
        )

# custom css
r = requests.get(f"{site}/wp-json/wp/v2/settings", auth=auth, headers=h, timeout=30)
print("\nsettings", r.status_code, list(r.json().keys())[:30] if r.status_code == 200 else r.text[:200])
