#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"c:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode"
    r"\assets\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_7dfb9ce5533c561a018b26f3b896825b_images_eme25sgn-logo-5c161a3e-0955-4eda-b7e9-ee5f1b563ad0.png"
)
OUT = ROOT / "Anasayfa" / "signistanbul-logo.webp"
UA = "LEDAJANS-Sign-Logo-Upload/1.0"


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


def knock_black(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            is_red = r > 80 and r > g + 30 and r > b + 30
            if is_red:
                continue
            if luma < 28:
                px[x, y] = (r, g, b, 0)
            elif luma < 50:
                na = int(a * ((luma - 28) / 22.0))
                px[x, y] = (r, g, b, max(0, min(255, na)))
    bbox = im.getbbox()
    print("bbox", bbox)
    if not bbox:
        return im
    pad = 6
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(w, right + pad)
    bottom = min(h, bottom + pad)
    return im.crop((left, top, right, bottom))


def main() -> int:
    im = knock_black(Image.open(SRC))
    print("cropped", im.size)
    im.save(OUT, format="WEBP", quality=92, method=6)
    webp = OUT.read_bytes()
    print("webp_bytes", len(webp), "path", OUT)

    site, user, pw = load_env()
    up = requests.post(
        f"{site}/wp-json/wp/v2/media",
        auth=(user, pw),
        headers={
            "User-Agent": UA,
            "Content-Disposition": 'attachment; filename="signistanbul-logo.webp"',
        },
        files={"file": ("signistanbul-logo.webp", webp, "image/webp")},
        timeout=120,
    )
    print("media", up.status_code)
    if up.status_code not in (200, 201):
        print(up.text[:500])
        return 1
    payload = up.json()
    print("id", payload.get("id"))
    print("url", payload.get("source_url"))
    print("mime", payload.get("mime_type"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
