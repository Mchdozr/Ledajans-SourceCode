#!/usr/bin/env python3
"""Anasayfa dış mekan bina/LED cephe fotoğrafını WebP olarak WP media'ya yükler. Kırpma yok."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"c:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode"
    r"\assets\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"7dfb9ce5533c561a018b26f3b896825b_images_dmle-112705e5-943b-443e-8f45-486943598df4.jpg"
)
FILENAME = "dis-mekan-led-cephe.webp"
UA = "LEDAJANS-Upload-Outdoor-Facade/1.0"
ALT = "Dış Mekan LED Ekran - Outdoor LED Ekran Çözümleri"


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    with open(ROOT / ".env", encoding="utf-8-sig") as f:
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


def to_webp(src: Path) -> tuple[bytes, int, int]:
    img = Image.open(src).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=84, method=6)
    return buf.getvalue(), img.width, img.height


def main() -> int:
    if not SRC.is_file():
        print("HATA: kaynak jpg yok")
        return 1
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1
    webp, w, h = to_webp(SRC)
    print("local", SRC.name, f"{w}x{h}", "webp_bytes", len(webp))

    up = requests.post(
        f"{site}/wp-json/wp/v2/media",
        auth=(user, pw),
        headers={
            "User-Agent": UA,
            "Content-Disposition": f'attachment; filename="{FILENAME}"',
        },
        files={"file": (FILENAME, webp, "image/webp")},
        data={"alt_text": ALT, "title": "Dış Mekan LED Cephe"},
        timeout=180,
    )
    print("media", up.status_code)
    if up.status_code not in (200, 201):
        print(up.text[:400])
        return 1
    body = up.json()
    print("id", body.get("id"))
    print("url", body.get("source_url"))
    print("mime", body.get("mime_type"))
    print("wh", w, h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
