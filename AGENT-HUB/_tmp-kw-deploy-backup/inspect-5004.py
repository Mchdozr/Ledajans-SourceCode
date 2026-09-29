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

for pid in (5004, 5008):
    p = requests.get(f"{site}/wp-json/wp/v2/pages/{pid}", params={"context": "edit"}, auth=auth, headers=headers, timeout=60).json()
    meta = p.get("meta") or {}
    el = meta.get("_elementor_data")
    print(pid, p.get("slug"), "template=", p.get("template"), "parent=", p.get("parent"), "lang=", p.get("lang"), "translations=", p.get("translations"))
    print("  meta keys:", sorted(k for k in meta.keys()))
    print("  rank_math:", {k: v for k, v in meta.items() if k.startswith("rank_math")})
    print("  elementor_data len:", len(el) if isinstance(el, str) else type(el), "edit_mode:", meta.get("_elementor_edit_mode"), "tpl_type:", meta.get("_elementor_template_type"))
    print("  content raw len:", len((p.get("content") or {}).get("raw", "")))
    if isinstance(el, str) and el:
        data = json.loads(el)
        def walk(n, d=0):
            if isinstance(n, list):
                for x in n:
                    walk(x, d)
                return
            wt = n.get("widgetType") or n.get("elType")
            s = n.get("settings") or {}
            h = s.get("html") or s.get("editor") or ""
            print("   " + "  " * d + f"{wt} id={n.get('id')} html_len={len(h)} {h[:70]!r}")
            walk(n.get("elements") or [], d + 1)
        walk(data)
