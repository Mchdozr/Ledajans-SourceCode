#!/usr/bin/env python3
"""P0 para sayfa hub icerigini (led-ekran.html) WP sayfasina yazar."""
from __future__ import annotations

import argparse
import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HUB = {
    "file": "LED Ekran/led-ekran.html",
    "slug": "led-ekran",
    "page_id": 5557,
}


def load_env() -> tuple[str, str, str]:
    path = os.path.join(ROOT, ".env")
    data: dict[str, str] = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip("\"'")
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    user = data.get("WP_USERNAME", "")
    pw = data.get("WP_APP_PASSWORD", "").replace(" ", "")
    return site, user, pw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1

    path = os.path.join(ROOT, HUB["file"].replace("/", os.sep))
    with open(path, encoding="utf-8") as f:
        content = f.read()

    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-Money-Pages/1.0", "Content-Type": "application/json"}

    if not args.apply:
        print(f"DRY-RUN: {HUB['slug']} id={HUB['page_id']} ({len(content)} karakter)")
        return 0

    r = requests.post(
        f"{site}/wp-json/wp/v2/pages/{HUB['page_id']}",
        json={"content": content},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    if r.status_code not in (200, 201):
        print(f"HATA HTTP {r.status_code}: {r.text[:400]}")
        return 1
    print(f"OK: /{HUB['slug']}/ guncellendi (id={HUB['page_id']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
