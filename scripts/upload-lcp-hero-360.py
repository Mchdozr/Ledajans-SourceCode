#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "AGENT-HUB" / "ldajsn2-mobile-360-q50.webp"
UA = "LEDAJANS-LCP-Upload/1.0"


def load_env():
    data = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data["WP_USERNAME"],
        data["WP_APP_PASSWORD"].replace(" ", ""),
    )


def main() -> int:
    site, user, pw = load_env()
    webp = FILE.read_bytes()
    print("local_bytes", len(webp))
    up = requests.post(
        f"{site}/wp-json/wp/v2/media",
        auth=(user, pw),
        headers={
            "User-Agent": UA,
            "Content-Disposition": 'attachment; filename="ldajsn2-mobile-360-q50.webp"',
        },
        files={"file": ("ldajsn2-mobile-360-q50.webp", webp, "image/webp")},
        timeout=120,
    )
    print("media", up.status_code, up.text[:400])
    if up.status_code not in (200, 201):
        return 1
    print("URL", up.json().get("source_url"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
