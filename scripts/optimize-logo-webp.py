#!/usr/bin/env python3
"""LedajansLogo.png -> WebP yukle, Elementor icinde URL degistir (header/home)."""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OLD = "https://ledajans.com/wp-content/uploads/2022/12/LedajansLogo.png"
UA = "LEDAJANS-Logo-WebP/1.0"


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


def walk_replace(nodes, old: str, new: str) -> int:
    n = 0
    if isinstance(nodes, list):
        for x in nodes:
            n += walk_replace(x, old, new)
        return n
    if isinstance(nodes, dict):
        for k, v in list(nodes.items()):
            if isinstance(v, str) and old in v:
                nodes[k] = v.replace(old, new)
                n += 1
            else:
                n += walk_replace(v, old, new)
    return n


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    h = {"User-Agent": UA}

    # 1) indir + webp
    r = requests.get(OLD, headers=h, timeout=60)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGBA")
    # header logo ~182x36 — retina icin 364x72 max
    img.thumbnail((364, 72), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=82, method=6)
    webp = buf.getvalue()
    print(f"webp_bytes={len(webp)} from_png={len(r.content)}")

    # 2) media upload
    files = {
        "file": ("LedajansLogo.webp", webp, "image/webp"),
    }
    up = requests.post(
        f"{site}/wp-json/wp/v2/media",
        auth=auth,
        headers={"User-Agent": UA, "Content-Disposition": 'attachment; filename="LedajansLogo.webp"'},
        files=files,
        timeout=120,
    )
    print("media", up.status_code, up.text[:300])
    if up.status_code not in (200, 201):
        return 1
    new_url = up.json().get("source_url")
    print("new_url", new_url)
    if not new_url:
        return 1

    # 3) ana sayfa elementor data
    page_id = 1248
    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{page_id}",
        params={"context": "edit"},
        auth=auth,
        headers=h,
        timeout=60,
    )
    print("page", rp.status_code)
    if rp.status_code != 200:
        return 1
    meta = (rp.json().get("meta") or {})
    raw = meta.get("_elementor_data")
    if not raw:
        print("no elementor data")
        return 2
    data = json.loads(raw) if isinstance(raw, str) else raw
    changed = walk_replace(data, OLD, new_url)
    print("replacements", changed)
    if changed == 0:
        print("WARN: ana sayfada eski logo URL yok (header theme olabilir)")
        print("MANUEL: Header/logo widget'ta yeni URL kullan:", new_url)
        return 0

    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{page_id}",
        json={"meta": {"_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":"))}},
        auth=auth,
        headers={**h, "Content-Type": "application/json"},
        timeout=90,
    )
    print("update", ru.status_code, ru.text[:200])
    return 0 if ru.status_code in (200, 201) else 1


if __name__ == "__main__":
    sys.exit(main())
