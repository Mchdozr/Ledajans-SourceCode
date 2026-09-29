from __future__ import annotations

import base64
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
user, pw = env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", "")
token = base64.b64encode(f"{user}:{pw}".encode()).decode("ascii")
auth = (user, pw)
headers = {
    "User-Agent": "LEDAJANS-KW-Verify/1.0",
    "Authorization": f"Basic {token}",
    "X-WP-Authorization": f"Basic {token}",
}

r = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
print("elementor_cache", r.status_code, r.text[:120])

r = requests.post(f"{site}/wp-json/ledajans/v1/purge", auth=auth, headers=headers, timeout=60)
print("ledajans_purge", r.status_code, r.text[:180])

try:
    r = requests.get(
        f"{site}/?LSCWP_CTRL=purge&litespeed_type=purge_all",
        headers={"User-Agent": "LEDAJANS-KW-Verify/1.0", "Cache-Control": "no-cache"},
        timeout=20,
    )
    print("lsc_purge", r.status_code)
except Exception as exc:
    print("lsc_purge ERR", type(exc).__name__)

# RankMath redirect for /dis-cephe-led-ekran/ -> /cephe-led-ekran/
body = {"url_from": "/dis-cephe-led-ekran", "url_to": "/cephe-led-ekran/", "header_code": "301"}
for path in ("/wp-json/rankmath/v1/redirections", "/wp-json/redirection/v1/redirect"):
    rr = requests.post(f"{site}{path}", json=body, auth=auth, headers=headers, timeout=30)
    print("redirect", path, rr.status_code, rr.text[:160])
