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
headers = {"User-Agent": "LEDAJANS-Hub-Check/1.0"}

r = requests.get(
    f"{site}/wp-json/wp/v2/pages/5001",
    params={"context": "edit"},
    auth=auth,
    headers=headers,
    timeout=60,
)
raw = (r.json().get("content") or {}).get("raw") or ""
print("rest_raw", len(raw))
print("has_senaryo", "Kullanım senaryoları" in raw)
print("has_pitch", "pitch-secim-rehberi" in raw)
print("has_blog_price", "/blog/led-ekran-fiyatlari-2026/" in raw)
print("modified", r.json().get("modified"))

# LiteSpeed purge endpoints
for path in (
    "/wp-json/litespeed/v1/purge_all",
    "/litespeed/v1/purge_all",
    "/wp-json/litespeed/v1/purge",
):
    for method in ("POST", "GET"):
        fn = requests.post if method == "POST" else requests.get
        try:
            rr = fn(f"{site}{path}", auth=auth, headers=headers, timeout=20)
            print(method, path, rr.status_code, rr.text[:80].replace("\n", " "))
        except Exception as exc:
            print(method, path, type(exc).__name__)
