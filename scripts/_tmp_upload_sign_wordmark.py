#!/usr/bin/env python3
"""SIGN logosunu siyah-key + sıkı kırp, WebP/PNG kaydet, WP medyaya yükle."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Fair-SIGN-Logo/1.0"
SRC = Path(
    r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode"
    r"\assets\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"7dfb9ce5533c561a018b26f3b896825b_images_eme25sgn-logo-f59d0364-c530-4f32-9f7b-21a5b77df300.png"
)
OUT_WEBP = ROOT / "Anasayfa" / "signistanbul-sign-logo.webp"
OUT_PNG = ROOT / "Anasayfa" / "signistanbul-sign-logo.png"


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


def process() -> tuple[int, int]:
    im = Image.open(SRC).convert("RGBA")
    arr = np.array(im).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    mx = np.maximum(np.maximum(r, g), b)
    # Siyah zemin: parlakligi alpha yap (kirmizi harf kalir, anti-alias korunur)
    alpha = np.clip((mx - 10.0) * (255.0 / 210.0), 0, 255)
    arr[:, :, 3] = alpha
    # Yari seffaf piksellerde kirmiziyi koru (siyah premultiply yok)
    mask = alpha > 0
    scale = np.zeros_like(mx)
    scale[mask] = 255.0 / np.maximum(mx[mask], 1.0)
    scale = np.clip(scale, 1.0, 3.2)
    arr[:, :, 0] = np.clip(r * scale, 0, 255)
    arr[:, :, 1] = np.clip(g * scale, 0, 255)
    arr[:, :, 2] = np.clip(b * scale, 0, 255)

    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    bbox = out.getbbox()
    if not bbox:
        raise SystemExit("HATA: bbox bos")
    pad = 4
    l, t, rgt, btm = bbox
    l = max(0, l - pad)
    t = max(0, t - pad)
    rgt = min(out.width, rgt + pad)
    btm = min(out.height, btm + pad)
    out = out.crop((l, t, rgt, btm))
    OUT_WEBP.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT_WEBP, format="WEBP", quality=88, method=6, lossless=False)
    out.save(OUT_PNG, format="PNG", optimize=True)
    print(
        "processed",
        out.size,
        "webp",
        OUT_WEBP.stat().st_size,
        "png",
        OUT_PNG.stat().st_size,
        "bbox",
        (l, t, rgt, btm),
    )
    return out.size


def upload(site: str, auth: tuple[str, str], path: Path, mime: str) -> str:
    with path.open("rb") as fh:
        up = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                "User-Agent": UA,
                "Content-Disposition": f'attachment; filename="{path.name}"',
            },
            files={"file": (path.name, fh, mime)},
            data={
                "title": "SIGN ISTANBUL fuar karti logo",
                "alt_text": "SIGN ISTANBUL",
            },
            timeout=180,
        )
    print("upload", path.suffix, up.status_code)
    if up.status_code not in (200, 201):
        print(up.text[:500])
        raise SystemExit(1)
    url = up.json().get("source_url")
    print("url", url)
    return url


def main() -> int:
    process()
    site, user, pw = load_env()
    url = upload(site, (user, pw), OUT_WEBP, "image/webp")
    print("MEDIA_URL", url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
