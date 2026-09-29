#!/usr/bin/env python3
"""WP Media: stant 1920 mp4 + poster WebP. Secret yazdırmaz."""
from __future__ import annotations

from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
ANASAYFA = ROOT / "Anasayfa"
UA = "LEDAJANS-Hero-Media/1.0"


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
        data.get("WP_USERNAME", ""),
        data.get("WP_APP_PASSWORD", "").replace(" ", ""),
    )


def upload(site: str, user: str, pw: str, path: Path, mime: str) -> str:
    with path.open("rb") as fh:
        r = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=(user, pw),
            headers={
                "User-Agent": UA,
                "Content-Disposition": f'attachment; filename="{path.name}"',
            },
            files={"file": (path.name, fh, mime)},
            timeout=180,
        )
    print(f"{path.name} status={r.status_code} bytes={path.stat().st_size}")
    if r.status_code not in (200, 201):
        print("ERR", r.text[:240])
        raise SystemExit(1)
    url = r.json().get("source_url") or ""
    print(f"{path.name} url={url}")
    return url


def main() -> int:
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1
    items = [
        (ANASAYFA / "hero-stant-1920.mp4", "video/mp4"),
        (ANASAYFA / "hero-stant-poster.webp", "image/webp"),
        (ANASAYFA / "hero-stant-poster-mobile.webp", "image/webp"),
    ]
    for path, mime in items:
        if not path.is_file():
            print("HATA: yok", path.name)
            return 1
        upload(site, user, pw, path, mime)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
