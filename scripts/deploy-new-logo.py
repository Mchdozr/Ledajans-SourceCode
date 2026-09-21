#!/usr/bin/env python3
"""Yeni LEDAJANS logosunu WP medyaya yükler; --apply ile HTML/plugin URL remap."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-New-Logo/1.0"
PNG_PATH = ROOT / "assets" / "brand" / "ledajans-logo.png"
WEBP_PATH = ROOT / "assets" / "brand" / "ledajans-logo.webp"
URLS_JSON = ROOT / "assets" / "brand" / "logo-urls.json"

OLD_URLS = [
    "https://ledajans.com/wp-content/uploads/2022/12/LedajansLogo.png",
    "https://ledajans.com/wp-content/uploads/2026/08/LedajansLogo.webp",
    "https://ledajans.com/wp-content/uploads/2022/12/ledajans-logo-web.jpg",
    "https://ledajans.com/wp-content/uploads/2026/02/ledajans-logo.png",
]


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


def upload(site: str, auth: tuple[str, str], path: Path, mime: str) -> dict:
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
                "title": "LEDAJANS Logo",
                "alt_text": "LEDAJANS",
                "caption": "LEDAJANS resmi logo",
            },
            timeout=120,
        )
    print(f"upload_{path.suffix} status={up.status_code}")
    if up.status_code not in (200, 201):
        print(up.text[:400])
        raise SystemExit(1)
    body = up.json()
    return {
        "id": body.get("id"),
        "source_url": body.get("source_url"),
        "mime": body.get("mime_type"),
    }


def walk_replace(nodes, mapping: dict[str, str]) -> int:
    n = 0
    if isinstance(nodes, list):
        for x in nodes:
            n += walk_replace(x, mapping)
        return n
    if isinstance(nodes, dict):
        for k, v in list(nodes.items()):
            if isinstance(v, str):
                nv = v
                for old, new in mapping.items():
                    if old in nv:
                        nv = nv.replace(old, new)
                if nv != v:
                    nodes[k] = nv
                    n += 1
            else:
                n += walk_replace(v, mapping)
    return n


def replace_in_collection(site: str, auth: tuple[str, str], collection: str, mapping: dict[str, str]) -> int:
    total = 0
    page = 1
    headers = {"User-Agent": UA}
    while True:
        r = requests.get(
            f"{site}/wp-json/wp/v2/{collection}",
            params={"per_page": 50, "page": page, "context": "edit", "status": "any"},
            auth=auth,
            headers=headers,
            timeout=60,
        )
        if r.status_code == 400 and page > 1:
            break
        if r.status_code != 200:
            print(f"{collection} list={r.status_code}")
            break
        items = r.json()
        if not items:
            break
        for item in items:
            meta = item.get("meta") or {}
            raw = meta.get("_elementor_data")
            if not raw:
                continue
            data = json.loads(raw) if isinstance(raw, str) else raw
            changed = walk_replace(data, mapping)
            if changed == 0:
                continue
            pid = item["id"]
            ru = requests.post(
                f"{site}/wp-json/wp/v2/{collection}/{pid}",
                json={"meta": {"_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":"))}},
                auth=auth,
                headers={**headers, "Content-Type": "application/json"},
                timeout=90,
            )
            print(f"elementor {collection}/{pid} changed={changed} update={ru.status_code}")
            if ru.status_code in (200, 201):
                total += changed
        if len(items) < 50:
            break
        page += 1
    return total


def main() -> int:
    dry = "--dry-run" in sys.argv
    apply_wp = "--apply" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    print(f"png_bytes={PNG_PATH.stat().st_size} webp_bytes={WEBP_PATH.stat().st_size}")
    print(f"old_urls={len(OLD_URLS)}")
    if dry:
        print("DRY_RUN: upload/yazma yok")
        return 0

    png = upload(site, auth, PNG_PATH, "image/png")
    webp = upload(site, auth, WEBP_PATH, "image/webp")
    urls = {"png": png["source_url"], "webp": webp["source_url"], "png_id": png["id"], "webp_id": webp["id"]}
    URLS_JSON.write_text(json.dumps(urls, indent=2), encoding="utf-8")
    print("png_url", urls["png"])
    print("webp_url", urls["webp"])

    if not apply_wp:
        print("UPLOAD_OK (Elementor remap icin --apply)")
        return 0

    mapping = {old: urls["webp"] for old in OLD_URLS}
    n = 0
    for coll in ("pages", "posts", "elementor_library"):
        n += replace_in_collection(site, auth, coll, mapping)
    print(f"elementor_replacements={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
