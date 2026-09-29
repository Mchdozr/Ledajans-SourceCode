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
h = {"User-Agent": "Mozilla/5.0 LEDAJANS-P43"}

# find post 43
for t in ["pages", "posts", "elementor_library", "elementor_snippet"]:
    r = requests.get(f"{site}/wp-json/wp/v2/{t}/43", auth=auth, headers=h, timeout=30)
    print(t, r.status_code, (r.text[:180] if r.status_code != 200 else r.json().get("slug") or r.json().get("type")))

r = requests.get(f"{site}/wp-json/wp/v2/types", auth=auth, headers=h, timeout=30)
print("\nALL TYPES:")
for k, v in sorted(r.json().items()):
    print(f"  {k:30} rest={v.get('rest_base')}")

# snippets
r = requests.get(
    f"{site}/wp-json/wp/v2/elementor_snippet",
    params={"per_page": 100},
    auth=auth,
    headers=h,
    timeout=30,
)
print("\nsnippets", r.status_code)
if r.status_code == 200:
    for it in r.json():
        print(" ", it.get("id"), it.get("slug"), (it.get("title") or {}).get("rendered"))
