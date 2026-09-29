from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")

site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
auth = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
headers = {"User-Agent": "LEDAJANS-Meta/1.0"}

for pid in (5001, 3958, 5002):
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        params={"context": "edit"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    p = r.json()
    meta = p.get("meta") or {}
    print(f"\n=== {pid} {p.get('slug')} meta_keys={list(meta.keys())[:40]}")
    for k, v in meta.items():
        vs = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        if vs and ("elementor" in k.lower() or "html" in k.lower() or len(str(vs)) > 200):
            print(f"  {k} type={type(v).__name__} len={len(vs)} head={str(vs)[:80].replace(chr(10),' ')}")
    el = meta.get("_elementor_data")
    if el:
        (OUT / f"el-{pid}.json").write_text(el if isinstance(el, str) else json.dumps(el), encoding="utf-8")
        print("  saved elementor")
