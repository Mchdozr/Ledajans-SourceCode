#!/usr/bin/env python3
"""Warm cache until TTFB stabilizes, then run Lighthouse mobile."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "AGENT-HUB" / "lh-mobile-lcp-loop-r2.json"
UA = (
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
)


def warm(n: int = 8) -> list[float]:
    times = []
    for i in range(n):
        t0 = time.perf_counter()
        r = requests.get(
            "https://ledajans.com/",
            headers={"User-Agent": UA},
            timeout=45,
        )
        ms = (time.perf_counter() - t0) * 1000
        times.append(ms)
        cache = (
            r.headers.get("x-litespeed-cache")
            or r.headers.get("x-qc-cache")
            or r.headers.get("x-cache")
            or "-"
        )
        print(f"warm {i} {ms:.0f}ms cache={cache} bytes={len(r.content)}")
        time.sleep(0.4)
    return times


def run_lh(out: Path) -> dict:
    tmp = ROOT / "AGENT-HUB" / "lh-tmp" / f"chrome-{out.stem}"
    tmp.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TEMP"] = str(ROOT / "AGENT-HUB" / "lh-tmp")
    env["TMP"] = env["TEMP"]
    flags = f"--headless --no-sandbox --disable-gpu --user-data-dir={tmp}"
    cmd = (
        f'npx --yes lighthouse@12.2.1 "https://ledajans.com/" '
        f"--only-categories=performance,seo --form-factor=mobile "
        f"--screenEmulation.mobile=true --throttling-method=simulate "
        f'--chrome-flags="{flags}" --output=json --output-path="{out}" --quiet'
    )
    subprocess.run(cmd, cwd=str(ROOT), env=env, shell=True)
    d = json.loads(out.read_text(encoding="utf-8"))
    cats = {k: round((v.get("score") or 0) * 100) for k, v in (d.get("categories") or {}).items()}
    a = d.get("audits") or {}
    row = {
        "perf": cats.get("performance"),
        "seo": cats.get("seo"),
        "lcp": a.get("largest-contentful-paint", {}).get("displayValue"),
        "fcp": a.get("first-contentful-paint", {}).get("displayValue"),
        "tbt": a.get("total-blocking-time", {}).get("displayValue"),
        "ttfb": a.get("server-response-time", {}).get("displayValue"),
        "rb": a.get("render-blocking-resources", {}).get("displayValue"),
        "si": a.get("speed-index", {}).get("displayValue"),
    }
    print("LH", row)
    return row


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "r2"
    out = ROOT / "AGENT-HUB" / f"lh-mobile-lcp-loop-{label}.json"
    times = warm(8)
    print(f"warm_median_approx={sorted(times)[len(times)//2]:.0f}ms")
    run_lh(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
