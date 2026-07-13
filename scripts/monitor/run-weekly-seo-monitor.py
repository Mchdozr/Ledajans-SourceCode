#!/usr/bin/env python3
"""Haftalik SEO monitor — smoke + money pages + baseline hatirlatma."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import os
import subprocess
import sys
from datetime import datetime, timezone



def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"LEDAJANS weekly SEO monitor — {ts}\n")
    rc = 0
    for script in [
        "AGENT-HUB/audit-money-pages.py",
        "scripts/verify/verify-rankmath-p0-meta.py",
        "scripts/verify/verify-money-pages-live.py",
    ]:
        path = ROOT / script
        if not path.is_file():
            print(f"ATLANDI: {script}")
            continue
        print(f">> python3 {script}")
        r = subprocess.run([sys.executable, path], cwd=ROOT)
        rc |= r.returncode
    print("\nManuel: GSC query-page export → scripts/seo/update-serp-baseline-from-gsc.py")
    print("Manuel: npx lighthouse https://ledajans.com/ --form-factor=mobile")
    return rc


if __name__ == "__main__":
    sys.exit(main())
