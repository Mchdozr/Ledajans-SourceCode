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
headers = {"User-Agent": "LEDAJANS-Redir/1.0", "Content-Type": "application/json"}

r = requests.get(f"{site}/wp-json/redirection/v1", auth=auth, headers=headers, timeout=30)
print("index", r.status_code, r.text[:500])

payloads = [
    {
        "url": "/dis-cephe-led-ekran/",
        "match_type": "url",
        "action_type": "url",
        "action_code": 301,
        "action_data": {"url": "/cephe-led-ekran/"},
        "group_id": 1,
    }
]
for body in payloads:
    rr = requests.post(
        f"{site}/wp-json/redirection/v1/redirect",
        json=body,
        auth=auth,
        headers=headers,
        timeout=30,
    )
    print("create", rr.status_code, rr.text[:400])
