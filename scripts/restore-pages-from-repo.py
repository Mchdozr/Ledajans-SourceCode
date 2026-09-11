#!/usr/bin/env python3
"""Repo HTML sayfa/yazılarını WP'de publish et (projeler Elementor sayfası hariç)."""
from __future__ import annotations

import importlib.util
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
SKIP_SLUGS = {"projeler"}  # Elementor sayfa — content REST ile ezme
EXTRA = [
    ("LED Ekran/led-ekran.html", "led-ekran", "LED Ekran", "page"),
]


def load_env():
    data = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data["WP_USERNAME"],
        data["WP_APP_PASSWORD"].replace(" ", ""),
    )


def catalog():
    spec = importlib.util.spec_from_file_location("deploy_wp", ROOT / "deploy-to-wordpress.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = list(mod.PAGES_TO_DEPLOY) + EXTRA
    return [r for r in rows if r[1] not in SKIP_SLUGS]


def meta_of(html: str) -> tuple[str, str]:
    desc = re.search(r"<!-- SEO Meta Description:\s*(.+?)\s*-->", html)
    kw = re.search(r"<!-- SEO Focus Keyword:\s*(.+?)\s*-->", html)
    return (desc.group(1).strip() if desc else "", kw.group(1).strip() if kw else "")


def main() -> int:
    apply = "--apply" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    rows = catalog()
    print("items", len(rows), "apply", apply)
    ok = 0
    fail = 0
    for rel, slug, title, ptype in rows:
        path = ROOT / rel.replace("/", os.sep)
        if not path.is_file():
            print("MISSFILE", rel)
            fail += 1
            continue
        html = path.read_text(encoding="utf-8")
        endpoint = "posts" if ptype == "post" else "pages"
        if not apply:
            print(f"DRY {ptype} /{slug}/ bytes={len(html)}")
            ok += 1
            continue
        desc, focus = meta_of(html)
        payload = {"title": title, "slug": slug, "content": html, "status": "publish", "parent": 0}
        if desc:
            payload["excerpt"] = desc
            payload["meta"] = {"rank_math_description": desc, "rank_math_title": title}
            if focus:
                payload["meta"]["rank_math_focus_keyword"] = focus
        r = requests.get(
            f"{site}/wp-json/wp/v2/{endpoint}",
            params={"slug": slug, "status": "any"},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        existing = r.json()[0] if r.status_code == 200 and r.json() else None
        url = f"{site}/wp-json/wp/v2/{endpoint}/{existing['id']}" if existing else f"{site}/wp-json/wp/v2/{endpoint}"
        u = requests.post(url, json=payload, auth=auth, headers=headers, timeout=180)
        if u.status_code in (200, 201):
            print("OK", slug, u.json().get("id"), u.json().get("link"))
            ok += 1
        else:
            print("HATA", slug, u.status_code, (u.text or "")[:180].replace("\n", " "))
            fail += 1
        time.sleep(0.35)
    print(f"done ok={ok} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
