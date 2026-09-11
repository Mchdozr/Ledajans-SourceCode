#!/usr/bin/env python3
from __future__ import annotations

import re
import time

import requests

UA = (
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
)


def main() -> int:
    for i in range(4):
        t0 = time.perf_counter()
        r = requests.get(
            "https://ledajans.com/",
            headers={"User-Agent": UA},
            timeout=45,
        )
        ms = (time.perf_counter() - t0) * 1000
        cache = (
            r.headers.get("x-litespeed-cache")
            or r.headers.get("x-qc-cache")
            or r.headers.get("x-cache")
            or "-"
        )
        print(f"warm {i} {ms:.0f}ms cache={cache} bytes={len(r.content)}")

    h = r.text
    head = h.split("</head>")[0] if "</head>" in h else h[:20000]
    checks = {
        "360-q50": "360-q50" in h,
        "decoding_sync": 'decoding="sync"' in h,
        "lcp_critical": "ledajans-lcp-critical" in h,
        "idle": "ledajansRunWhenIdle" in h,
        "inter_in_head": "Inter:wght" in head,
        "preload360": "360-q50" in head and "preload" in head,
        "q60_preload": "ldajsn2-mobile-q60.webp" in head and "preload" in head,
    }
    for k, v in checks.items():
        print(f"{k}: {v}")

    m = re.search(r"<script[^>]+jquery\.min\.js[^>]*>", h)
    print("jquery_tag:", m.group(0) if m else None)
    m2 = re.search(r"<script[^>]+jquery-migrate[^>]*>", h)
    print("migrate_tag:", m2.group(0) if m2 else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
