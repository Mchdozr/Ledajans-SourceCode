#!/usr/bin/env python3
"""Haftalik SEO monitor — smoke + money pages + baseline hatirlatma."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"LEDAJANS weekly SEO monitor — {ts}\n")
    rc = 0
    for script in [
        "AGENT-HUB/audit-money-pages.py",
        "scripts/verify-rankmath-p0-meta.py",
        "scripts/verify-money-pages-live.py",
    ]:
        path = os.path.join(ROOT, script)
        if not os.path.isfile(path):
            print(f"ATLANDI: {script}")
            continue
        print(f">> python3 {script}")
        r = subprocess.run([sys.executable, path], cwd=ROOT)
        rc |= r.returncode
    print("\nManuel: GSC query-page export → scripts/update-serp-baseline-from-gsc.py")
    print("Manuel: npx lighthouse https://ledajans.com/ --form-factor=mobile")
    return rc


if __name__ == "__main__":
    sys.exit(main())
