#!/usr/bin/env python3
"""Sertifikalar + Markalarimiz: widget 3204fc4 uzerinden hero-widget API."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PAGE_ID = 1248
CERTS_WIDGET = "3204fc4"
CERTS_FILE = ROOT / "Anasayfa" / "sertifikalar-anasayfa.html"
BRANDS_FILE = ROOT / "Anasayfa" / "Marka-logolar.html"
UA = "LEDAJANS-Deploy-Certs-Brands/1.0"


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


def remove_orphan_brands_sections(nodes) -> int:
    """Onceki basarisiz ayri section'lari temizle (icerik certs widget'ta olacak)."""
    removed = 0
    if isinstance(nodes, list):
        keep = []
        for n in nodes:
            blob = json.dumps(n, ensure_ascii=False)
            # sadece brands (certs yok) ve hero class CSS referansi olan orphan
            if (
                "ledajans-brands" in blob
                and "ledajans-home-certs" not in blob
                and "ledajans-btn-primary" not in blob
            ):
                removed += 1
                continue
            removed += remove_orphan_brands_sections(n)
            keep.append(n)
        nodes[:] = keep
        return removed
    if isinstance(nodes, dict):
        for key in ("elements", "content"):
            if key in nodes and isinstance(nodes[key], list):
                removed += remove_orphan_brands_sections(nodes[key])
    return removed


def main() -> int:
    dry = "--dry-run" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    certs = CERTS_FILE.read_text(encoding="utf-8")
    brands = BRANDS_FILE.read_text(encoding="utf-8")
    if "ledajans-home-certs" not in certs or "ledajans-brands" not in brands:
        print("HATA: kaynak HTML gecersiz")
        return 1

    combined = certs.rstrip() + "\n\n" + brands.lstrip()
    print("combined_bytes", len(combined.encode("utf-8")))

    if dry:
        print("DRY_RUN")
        return 0

    # 1) Resmi endpoint (purge dahil)
    r = requests.post(
        f"{site}/wp-json/ledajans/v1/hero-widget",
        json={"html": combined, "page_id": PAGE_ID, "widget_id": CERTS_WIDGET},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print("hero-widget", r.status_code, r.text[:500])
    if r.status_code not in (200, 201):
        return 1

    # 2) Orphan ayri brands section temizle
    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    if rp.status_code != 200:
        print("page_get", rp.status_code)
        return 0  # asil deploy oldu

    raw = (rp.json().get("meta") or {}).get("_elementor_data")
    data = json.loads(raw) if isinstance(raw, str) else raw
    removed = remove_orphan_brands_sections(data)
    print("orphan_removed", removed)
    if removed:
        ru = requests.post(
            f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
            json={
                "meta": {
                    "_elementor_data": json.dumps(
                        data, ensure_ascii=False, separators=(",", ":")
                    )
                }
            },
            auth=auth,
            headers=headers,
            timeout=120,
        )
        print("cleanup_update", ru.status_code)

        # purge tekrar
        requests.post(
            f"{site}/wp-json/ledajans/v1/hero-widget",
            json={"html": combined, "page_id": PAGE_ID, "widget_id": CERTS_WIDGET},
            auth=auth,
            headers=headers,
            timeout=120,
        )

    home = requests.get(
        site + "/",
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone)",
            "Cache-Control": "no-cache",
        },
        timeout=45,
    ).text
    i_c = home.find("ledajans-home-certs")
    i_b = home.find("ledajans-brands")
    print("live_certs", i_c >= 0)
    print("live_brands", i_b >= 0)
    print("order_ok", i_c >= 0 and i_b > i_c)
    print("markalar_title", "Markalarımız" in home)
    return 0 if i_b >= 0 else 2


if __name__ == "__main__":
    sys.exit(main())
