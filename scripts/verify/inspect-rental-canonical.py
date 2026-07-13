#!/usr/bin/env python3
"""Rental URL canonical/redirect durumunu inceler."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import re
from html import unescape
from urllib.parse import urljoin

import requests

URLS = [
    "https://ledajans.com/rental-ekran/",
    "https://ledajans.com/case/rental-ekran/",
]


def extract(pattern: str, html: str) -> str:
    match = re.search(pattern, html, re.I | re.S)
    return unescape(re.sub(r"\s+", " ", match.group(1)).strip()) if match else ""


def inspect(url: str) -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": "LEDAJANS-Rental-Canonical-Audit/1.0"})
    response = session.get(url, timeout=30, allow_redirects=True)
    html = response.text
    print(f"\nURL: {url}")
    print(f"HTTP: {response.status_code}")
    print(f"Final: {response.url}")
    if response.history:
        print("Redirect chain:")
        for item in response.history:
            print(f"  {item.status_code} {item.url} -> {urljoin(item.url, item.headers.get('Location', ''))}")
    else:
        print("Redirect chain: yok")
    print("Title:", extract(r"<title[^>]*>(.*?)</title>", html)[:140] or "-")
    print("Canonical:", extract(r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)", html) or "-")
    print("Robots:", extract(r"<meta[^>]+name=[\"']robots[\"'][^>]+content=[\"']([^\"']+)", html) or "-")
    print("H1:", extract(r"<h1[^>]*>(.*?)</h1>", html)[:140] or "-")
    print("Has rental phrase:", "LED Ekran Kiralama" in html or "Rental Ekran" in html)


def main() -> int:
    for url in URLS:
        inspect(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
