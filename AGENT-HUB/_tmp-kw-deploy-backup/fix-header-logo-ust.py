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
SITE = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
AUTH = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
H = {"User-Agent": "Mozilla/5.0 LEDAJANS-LOGO-UST", "Content-Type": "application/json"}
OLD = "https://ledajans.com/wp-content/uploads/2026/09/ledajans-logo.webp"
NEW = "https://ledajans.com/wp-content/uploads/2026/09/ledajans-ust-menu-logo.webp"

r = requests.get(f"{SITE}/wp-json/wp/v2/elementor_snippet/5026", auth=AUTH, headers=H, timeout=40)
r.raise_for_status()
code = (r.json().get("meta") or {}).get("_elementor_code") or ""
print("old_count", code.count(OLD))
print("head", requests.head(NEW, timeout=20, allow_redirects=True, headers={"User-Agent": H["User-Agent"]}).status_code)
code2 = code.replace(OLD, NEW)
pr = requests.post(
    f"{SITE}/wp-json/wp/v2/elementor_snippet/5026",
    auth=AUTH,
    headers=H,
    data=json.dumps({"meta": {"_elementor_code": code2}}),
    timeout=60,
)
print("snippet", pr.status_code)
r2 = requests.get(f"{SITE}/wp-json/wp/v2/elementor_snippet/5026", auth=AUTH, headers=H, timeout=40)
newc = (r2.json().get("meta") or {}).get("_elementor_code") or ""
print("has_ust", NEW in newc, "still_old", OLD in newc)
requests.delete(f"{SITE}/wp-json/elementor/v1/cache", auth=AUTH, headers=H, timeout=40)
requests.get(f"{SITE}/?LSCWP_CTRL=purge&litespeed_type=purge_all", headers={"User-Agent": H["User-Agent"]}, timeout=25)
