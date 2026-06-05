#!/usr/bin/env python3
import os
import json
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(ROOT, ".env")
data = {}
with open(path, encoding="utf-8-sig") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
site = data["WP_SITE_URL"].rstrip("/")
auth = (data["WP_USERNAME"], data["WP_APP_PASSWORD"].replace(" ", ""))
h = {"User-Agent": "debug"}
for pid in (5557, 7491):
    print("---", pid)
kind = "pages" if pid == 5557 else "posts"
r = requests.get(
    f"{site}/wp-json/wp/v2/{kind}/{pid}",
    params={"context": "edit"},
    auth=auth,
    headers=h,
    timeout=30,
)
print("GET page", r.status_code)
j = r.json()
meta = j.get("meta") or {}
print("meta keys:", sorted(meta.keys())[:20], "count", len(meta))
for k in ("rank_math_title", "rank_math_description", "rank_math_focus_keyword"):
    print(k, ":", meta.get(k, "MISSING"))

# RankMath REST probe
for ep in ("/wp-json/rankmath/v1/", "/wp-json/rankmath/v1/updateMeta"):
    rr = requests.get(site + ep, auth=auth, headers=h, timeout=15)
    print(ep, rr.status_code, rr.text[:120])
