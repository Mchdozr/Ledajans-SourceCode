#!/usr/bin/env python3
"""Mobil CWV proxy kontrolu — canli TTFB + hero preload dogrulama."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import json
import os
import sys
import time

import requests

REPORT = AGENT_HUB / "REPORTS" / "cwv-check-latest.json"
URLS = [
    "https://ledajans.com/",
    "https://ledajans.com/led-ekran/",
    "https://ledajans.com/dis-mekan-led-ekran/",
]


def check_url(url: str) -> dict:
    t0 = time.perf_counter()
    r = requests.get(url, timeout=60, headers={"User-Agent": "LEDAJANS-CWV-Check/1.0"})
    elapsed_ms = round((time.perf_counter() - t0) * 1000)
    html = r.text
    preload = "fetchpriority=high" in html or 'rel="preload"' in html
    webp_hero = "ldajsn2-mobile-q60.webp" in html or "hero-poster.webp" in html
    gtm_defer = "googletagmanager" in html.lower()
    return {
        "url": url,
        "status": r.status_code,
        "ttfb_proxy_ms": elapsed_ms,
        "size_kb": round(len(html) / 1024, 1),
        "preload_lcp_hints": preload,
        "webp_hero_refs": webp_hero,
        "gtm_present": gtm_defer,
    }


def main() -> int:
    results = [check_url(u) for u in URLS]
    baseline_path = DATA_BASELINES / "audit-mobile-full.json"
    baseline = {}
    if os.path.isfile(baseline_path):
        with open(baseline_path, encoding="utf-8") as f:
            data = json.load(f)
        audits = data.get("audits", {})
        baseline = {
            "perf_score": data.get("categories", {}).get("performance", {}).get("score"),
            "lcp_s": audits.get("largest-contentful-paint", {}).get("numericValue"),
        }
    out = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pages": results, "baseline_before": baseline}
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nOK: {REPORT}")
    print("Not: Tam Lighthouse cloud ortaminda crash — GSC Deneyim raporu ile LCP dogrula.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
