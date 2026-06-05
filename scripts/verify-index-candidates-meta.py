#!/usr/bin/env python3
"""Index adaylari canli meta dogrulama."""
from __future__ import annotations

import re
import sys

import requests

PAGES = ["program-indir", "dis-mekan-rgb-panel"]


def meta_description(html: str) -> str:
    match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I)
    return match.group(1).strip() if match else ""


def title(html: str) -> str:
    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    return match.group(1).strip() if match else ""


def main() -> int:
    headers = {"User-Agent": "LEDAJANS-Verify-Index-Candidates/1.0", "Cache-Control": "no-cache"}
    failed = 0
    for slug in PAGES:
        url = f"https://ledajans.com/{slug}/"
        response = requests.get(url, headers=headers, timeout=45)
        t = title(response.text)
        d = meta_description(response.text)
        print(f"\n/{slug}/")
        print(f"HTTP {response.status_code}")
        print(f"title: {t}")
        print(f"description_len={len(d)}")
        print(d or "(description yok)")
        if response.status_code != 200 or not d:
            failed += 1
    print(f"\nSONUC: {'GECTI' if failed == 0 else 'BASARISIZ'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
