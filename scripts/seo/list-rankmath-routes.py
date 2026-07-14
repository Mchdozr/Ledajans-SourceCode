#!/usr/bin/env python3
from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import os, requests, json
data = {}
with open(ROOT / ".env", encoding="utf-8-sig") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
site = data["WP_SITE_URL"].rstrip("/")
auth = (data["WP_USERNAME"], data["WP_APP_PASSWORD"].replace(" ", ""))
r = requests.get(f"{site}/wp-json/rankmath/v1", auth=auth, timeout=30)
routes = r.json().get("routes", {})
for path in sorted(routes):
    m = routes[path].get("methods", [])
    if any(x in m for x in ("POST", "PUT", "PATCH")):
        print(path, m)
