#!/usr/bin/env python3
"""Hub /led-ekran/ RankMath cornerstone (pillar) isaretle."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import argparse
import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

HUB_SLUG = "led-ekran"
HUB_PAGE_ID = 5557
CORNERSTONE_META = "rank_math_pillar_content"


def load_env() -> tuple[str, str, str]:
    path = ROOT / ".env"
    data: dict[str, str] = {}
    if path.is_file():
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip("\"'")
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    return site, data.get("WP_USERNAME", ""), data.get("WP_APP_PASSWORD", "").replace(" ", "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1
    auth = (user, pw)
    page_id = None
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": HUB_SLUG, "status": "publish"},
        auth=auth,
        timeout=30,
    )
    if r.status_code == 200 and r.json():
        page_id = int(r.json()[0]["id"])
    else:
        page_id = HUB_PAGE_ID
        print(f"UYARI: slug lookup basarisiz, fallback page_id={page_id}")
    if not args.apply:
        print(f"DRY-RUN: page_id={page_id} {CORNERSTONE_META}=on")
        return 0
    u = requests.post(
        f"{site}/wp-json/wp/v2/pages/{page_id}",
        json={"meta": {CORNERSTONE_META: "on"}},
        auth=auth,
        timeout=60,
    )
    if u.status_code not in (200, 201):
        print(f"HATA HTTP {u.status_code}: {u.text[:300]}")
        return 1
    print(f"OK: /{HUB_SLUG}/ cornerstone isaretlendi (id={page_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
