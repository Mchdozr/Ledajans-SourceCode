#!/usr/bin/env python3
"""Program İndir sayfası Elementor HTML widget deploy (page 786)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PAGE_ID = 786
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Deploy-ProgramIndir/1.0"
BASE = ROOT / "Teknik-Destek-Bilgi" / "Program-indir"

# widget_id -> (file, required_marker_in_new_html or None for empty)
WIDGET_MAP = {
    "25682f9": (BASE / "hero-banner.html", "ledajans-blog-hero"),
    "997a1eb": (BASE / "indirme-dosyalari.html", "program-downloads-section"),
    "46ed6aa": (BASE / "uzak-masaustu.html", None),  # rehber kaldırıldı → boş
    "553ceb0": (BASE / "satis-kanallari.html", "ledajans-channels"),
}


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


def walk_set(nodes, mapping: dict[str, str]) -> int:
    changed = 0
    if isinstance(nodes, list):
        for n in nodes:
            changed += walk_set(n, mapping)
        return changed
    if not isinstance(nodes, dict):
        return 0
    wid = nodes.get("id")
    if wid in mapping and nodes.get("widgetType") == "html":
        settings = nodes.get("settings") or {}
        settings["html"] = mapping[wid]
        nodes["settings"] = settings
        changed += 1
    for key in ("elements", "content"):
        if key in nodes:
            changed += walk_set(nodes[key], mapping)
    return changed


def main() -> int:
    dry = "--dry-run" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    mapping: dict[str, str] = {}
    for wid, (path, marker) in WIDGET_MAP.items():
        if not path.is_file():
            print(f"HATA: dosya yok {path}")
            return 1
        html = path.read_text(encoding="utf-8")
        if marker and marker not in html:
            print(f"HATA: {path.name} marker yok: {marker}")
            return 1
        mapping[wid] = html
        print(f"OK {wid} <- {path.name} ({len(html)} bytes)")

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print("GET", rp.status_code)
    if rp.status_code != 200:
        print(rp.text[:400])
        return 1

    meta = rp.json().get("meta") or {}
    raw = meta.get("_elementor_data")
    if not raw:
        print("HATA: _elementor_data yok")
        return 1
    data = json.loads(raw) if isinstance(raw, str) else raw
    n = walk_set(data, mapping)
    print(f"widgets_updated={n} expected={len(mapping)}")
    if n != len(mapping):
        print("HATA: bazı widget id bulunamadı")
        return 1

    if dry:
        print("DRY_RUN: yazılmadı")
        return 0

    # Resmi ledajans hero-widget endpoint (purge dahil)
    ok = True
    for wid, html in mapping.items():
        r = requests.post(
            f"{site}/wp-json/ledajans/v1/hero-widget",
            json={"html": html, "page_id": PAGE_ID, "widget_id": wid},
            auth=auth,
            headers=headers,
            timeout=180,
        )
        print("hero-widget", wid, r.status_code, r.text[:160])
        if r.status_code not in (200, 201):
            ok = False

    if ok:
        return 0

    print("FALLBACK: elementor meta")
    payload = {
        "meta": {
            "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            "_elementor_edit_mode": "builder",
        }
    }
    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        json=payload,
        auth=auth,
        headers=headers,
        timeout=180,
    )
    print("POST", ru.status_code, ru.text[:300])
    return 0 if ru.status_code in (200, 201) else 1


if __name__ == "__main__":
    raise SystemExit(main())
