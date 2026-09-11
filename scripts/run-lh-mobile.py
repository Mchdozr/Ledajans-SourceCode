#!/usr/bin/env python3
"""Windows-safe-ish Lighthouse runner (ignores chrome-launcher EPERM cleanup)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "AGENT-HUB" / "lh-mobile-lcp-loop-r1.json"
TMP = ROOT / "AGENT-HUB" / "lh-tmp" / "chrome-run"
URL = "https://ledajans.com/"


def main() -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TEMP"] = str(ROOT / "AGENT-HUB" / "lh-tmp")
    env["TMP"] = env["TEMP"]
    flags = f"--headless --no-sandbox --disable-gpu --user-data-dir={TMP}"
    cmd = [
        "npx",
        "--yes",
        "lighthouse@12.2.1",
        URL,
        "--only-categories=performance,seo",
        "--form-factor=mobile",
        "--screenEmulation.mobile=true",
        "--throttling-method=simulate",
        f"--chrome-flags={flags}",
        "--output=json",
        f"--output-path={OUT}",
        "--quiet",
    ]
    print("running", " ".join(cmd[:6]), "...")
    p = subprocess.run(cmd, cwd=str(ROOT), env=env, shell=True)
    if not OUT.exists() or OUT.stat().st_size < 1000:
        print("NO_OUTPUT", p.returncode)
        return 1
    d = json.loads(OUT.read_text(encoding="utf-8"))
    cats = d.get("categories") or {}
    if not cats:
        print("EMPTY_CATEGORIES exit", p.returncode)
        return 1
    scores = {k: round((v.get("score") or 0) * 100) for k, v in cats.items()}
    a = d["audits"]
    print("EXIT", p.returncode, "SCORES", scores)
    for k in (
        "largest-contentful-paint",
        "first-contentful-paint",
        "total-blocking-time",
        "server-response-time",
        "render-blocking-resources",
        "speed-index",
    ):
        print(k, a.get(k, {}).get("displayValue"))
    return 0 if scores.get("performance", 0) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
