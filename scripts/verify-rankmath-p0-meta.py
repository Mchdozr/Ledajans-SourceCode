#!/usr/bin/env python3
"""Canlı sayfa <title> ve RankMath REST meta doğrulama."""
from __future__ import annotations

import os
import re
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SLUGS = ["led-ekran", "dis-mekan-led-ekran", "rental-ekran", "ic-mekan-led-ekran"]


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
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env içinde WP_USERNAME ve WP_APP_PASSWORD gerekli")
        return 1
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-Verify-RankMath/1.0"}
    fail = 0

    # Anasayfa: canlı <title> smoke kontrolü (marka + kapsam odaklı olmalı)
    hr = requests.get(f"{site}/", headers=headers, timeout=30)
    m = re.search(r"<title[^>]*>([^<]+)</title>", hr.text, re.I)
    print(f"/ (anasayfa): HTTP {hr.status_code}")
    print(f"  HTML <title>: {m.group(1).strip() if m else '(title bulunamadi)'}")
    print()

    for slug in SLUGS:
        url = f"{site}/{slug}/"
        pr = requests.get(
            f"{site}/wp-json/wp/v2/pages",
            params={"slug": slug},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        meta = {}
        if pr.status_code == 200 and pr.json():
            meta = pr.json()[0].get("meta") or {}
        hr = requests.get(url, headers=headers, timeout=30)
        m = re.search(r"<title[^>]*>([^<]+)</title>", hr.text, re.I)
        live_title = m.group(1).strip() if m else "(title bulunamadi)"
        rm_title = meta.get("rank_math_title") or "(REST meta yok)"
        ok = rm_title != "(REST meta yok)" and len(rm_title) > 10
        print(f"{slug}: HTTP {hr.status_code}")
        print(f"  REST rank_math_title: {rm_title}")
        print(f"  HTML <title>:         {live_title}")
        if not ok:
            fail += 1
        print()
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
