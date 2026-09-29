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
headers = {"User-Agent": "LEDAJANS-Rendered/1.0", "Cache-Control": "no-cache"}

r = requests.get(f"{site}/wp-json/wp/v2/pages/5001", auth=auth, headers=headers, timeout=60)
rendered = (r.json().get("content") or {}).get("rendered") or ""
print("rendered", len(rendered), "senaryo", "Kullanım senaryoları" in rendered, "blog", "/blog/led-ekran-fiyatlari-2026/" in rendered)

# public fetch bypass cookies
rp = requests.get(
    f"{site}/led-ekran/",
    headers={"User-Agent": "Mozilla/5.0 KW-Bypass", "Cache-Control": "no-cache", "Pragma": "no-cache"},
    timeout=60,
)
html = rp.text
print("public", rp.status_code, "age", rp.headers.get("Age"), "cc", rp.headers.get("Cache-Control"))
print("public senaryo", "Kullanım senaryoları" in html, "blog", "/blog/led-ekran-fiyatlari-2026/" in html)

# nginx cache purge typical
for u in (
    f"{site}/led-ekran/",
    f"{site}/cob-ekran/",
    f"{site}/ic-mekan-led-ekran/",
    f"{site}/dis-mekan-led-ekran/",
    f"{site}/rental-ekran/",
):
    rr = requests.request(
        "PURGE",
        u,
        headers={"User-Agent": "LEDAJANS-PURGE/1.0", "X-Purge-Method": "regex"},
        timeout=20,
    )
    print("PURGE", u, rr.status_code)
