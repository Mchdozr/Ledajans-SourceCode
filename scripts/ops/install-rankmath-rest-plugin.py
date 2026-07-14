#!/usr/bin/env python3
"""RankMath REST enable eklentisini zip ile yukler ve etkinlestirir."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import io
import os
import sys
import zipfile

import requests



def load_env() -> tuple[str, str, str]:
    path = ROOT / ".env"
    data: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data.get("WP_USERNAME", ""),
        data.get("WP_APP_PASSWORD", "").replace(" ", ""),
    )


def make_zip() -> bytes:
    src = OPS_WORDPRESS / "rankmath-rest-enable.php"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(src, "ledajans-rankmath-rest/ledajans-rankmath-rest.php")
    return buf.getvalue()


def main() -> int:
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-Install-RankMath-REST/1.0"}
    slug = "ledajans-rankmath-rest/ledajans-rankmath-rest"

    r = requests.post(
        f"{site}/wp-json/wp/v2/plugins",
        headers=headers,
        auth=auth,
        files={"file": ("ledajans-rankmath-rest.zip", make_zip(), "application/zip")},
        data={"status": "active"},
        timeout=120,
    )
    print("install", r.status_code, r.text[:400])
    if r.status_code not in (200, 201):
        return 1

  # activate if uploaded inactive
    r2 = requests.post(
        f"{site}/wp-json/wp/v2/plugins/{slug}",
        json={"status": "active"},
        auth=auth,
        headers={**headers, "Content-Type": "application/json"},
        timeout=60,
    )
    print("activate", r2.status_code, r2.text[:200])
    return 0 if r2.status_code in (200, 201) else 1


if __name__ == "__main__":
    sys.exit(main())
