#!/usr/bin/env python3
"""Ana sayfa ve COB canli meta description dogrulama."""
from __future__ import annotations

import re
import sys

import requests

PAGES = [
    ("https://ledajans.com/", 160),
    ("https://ledajans.com/cob-ekran/", 160),
]


def extract_meta_description(html: str) -> str:
    match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
        html,
        re.I,
    )
    return match.group(1).strip() if match else ""


def main() -> int:
    headers = {"User-Agent": "LEDAJANS-Verify-Meta-Cleanup/1.0", "Cache-Control": "no-cache"}
    failed = 0
    for url, max_len in PAGES:
        response = requests.get(url, headers=headers, timeout=45)
        description = extract_meta_description(response.text)
        print(f"\n{url}")
        print(f"HTTP {response.status_code}")
        print(f"description_len={len(description)}")
        print(description or "(description yok)")
        if response.status_code != 200 or not description or len(description) > max_len:
            failed += 1
    print(f"\nSONUC: {'GECTI' if failed == 0 else 'BASARISIZ'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
