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
headers = {"User-Agent": "LEDAJANS-Diag/1.0"}


def get(path: str, **params):
    r = requests.get(f"{site}{path}", params=params, auth=auth, headers=headers, timeout=30)
    return r.status_code, r.text


for ns in ("ledajans/v1", "wp-abilities/v1", "mcp"):
    code, body = get(f"/wp-json/{ns}")
    print("==", ns, code)
    try:
        data = json.loads(body)
        routes = data.get("routes", {})
        for route, info in routes.items():
            print("  ", route, [e.get("methods") for e in info.get("endpoints", [])])
    except Exception:
        print(body[:300])

code, body = get("/wp-json/wp-abilities/v1/abilities", per_page=100)
print("== abilities", code)
try:
    for a in json.loads(body):
        print("  ", a.get("name"), "-", (a.get("description") or "")[:90])
except Exception:
    print(body[:300])

code, body = get("/wp-json/wp/v2/plugins", context="edit")
print("== plugins", code)
try:
    for p in json.loads(body):
        if "updraft" in p.get("plugin", "").lower() or "backup" in p.get("name", "").lower():
            print("  ", p.get("plugin"), p.get("status"), p.get("version"))
except Exception:
    print(body[:300])
