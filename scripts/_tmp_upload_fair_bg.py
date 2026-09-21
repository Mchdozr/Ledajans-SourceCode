#!/usr/bin/env python3
"""Geçici: SIGNISTANBUL fuar kartı WebP arka planını WP medyaya yükle."""
from __future__ import annotations

from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Fair-BG/1.0"
WEBP = ROOT / "Anasayfa" / "signistanbul-fair-bg.webp"


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
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
    with WEBP.open("rb") as fh:
        up = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=(user, pw),
            headers={
                "User-Agent": UA,
                "Content-Disposition": 'attachment; filename="signistanbul-fair-bg.webp"',
            },
            files={"file": (WEBP.name, fh, "image/webp")},
            data={
                "title": "SIGNISTANBUL fuar karti arka plan",
                "alt_text": "SIGNISTANBUL fuar duyurusu arka plan",
            },
            timeout=180,
        )
    print("status", up.status_code)
    if up.status_code not in (200, 201):
        print(up.text[:600])
        return 1
    body = up.json()
    print("id", body.get("id"))
    print("url", body.get("source_url"))
    print("mime", body.get("mime_type"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
