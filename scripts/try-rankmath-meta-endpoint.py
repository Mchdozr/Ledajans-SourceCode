#!/usr/bin/env python3
import os
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = {}
with open(os.path.join(ROOT, ".env"), encoding="utf-8-sig") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
site = data["WP_SITE_URL"].rstrip("/")
auth = (data["WP_USERNAME"], data["WP_APP_PASSWORD"].replace(" ", ""))
h = {"User-Agent": "test", "Content-Type": "application/json"}
pid = 5557
body = {
    "title": "LED Ekran ve Fiyatları 2026 | İç-Dış Mekan - LEDAJANS",
    "description": "LED ekran test",
    "focus": "led ekran",
}
for method in ("GET", "POST", "PUT", "PATCH"):
    r = requests.request(
        method,
        f"{site}/wp-json/rankmath/v1/meta/{pid}",
        json=body if method != "GET" else None,
        auth=auth,
        headers=h,
        timeout=30,
    )
    print(method, r.status_code, r.text[:180])
