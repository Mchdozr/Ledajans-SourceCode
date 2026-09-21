#!/usr/bin/env python3
"""Ana sayfa Hero HTML — ledajans/v1/hero-widget (fallback: Elementor meta)."""
from __future__ import annotations

import base64
import json
import os
import sys
from typing import Any

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERO_PATH = os.path.join(ROOT, "Anasayfa", "Hero.html")
UA = "LEDAJANS-Deploy-Homepage-Hero/1.2"
MARKER = "ledajans-hero"
DEFAULT_PAGE_ID = 1248
DEFAULT_WIDGET_ID = "ee08c77"


def load_env() -> tuple[str, str, str]:
    path = os.path.join(ROOT, ".env")
    data: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as f:
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


def walk_replace(nodes: Any, new_html: str, widget_id: str | None = None) -> int:
    changed = 0
    if isinstance(nodes, list):
        for n in nodes:
            changed += walk_replace(n, new_html, widget_id)
        return changed
    if not isinstance(nodes, dict):
        return 0

    widget_type = nodes.get("widgetType") or nodes.get("elType")
    settings = nodes.get("settings") or {}
    html_val = settings.get("html")
    nid = str(nodes.get("id") or "")
    if widget_type == "html" and isinstance(html_val, str) and MARKER in html_val:
        if widget_id is None or nid == widget_id:
            settings["html"] = new_html
            nodes["settings"] = settings
            changed += 1

    for key in ("elements", "content"):
        if key in nodes:
            changed += walk_replace(nodes[key], new_html, widget_id)
    return changed


def main() -> int:
    dry = "--dry-run" in sys.argv
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1
    if not os.path.isfile(HERO_PATH):
        print("HATA: Hero.html yok")
        return 1

    new_html = open(HERO_PATH, encoding="utf-8").read()
    if "<picture>" not in new_html or "hero-atrium-led" not in new_html:
        print("HATA: Hero.html beklenen picture/atrium gorseli icermiyor")
        return 1

    auth = (user, pw)
    token = base64.b64encode(f"{user}:{pw}".encode("utf-8")).decode("ascii")
    headers = {
        "User-Agent": UA,
        "Content-Type": "application/json",
        "Authorization": f"Basic {token}",
        "X-WP-Authorization": f"Basic {token}",
    }

    if dry:
        print("DRY_RUN: yazilmadi")
        return 0

    # 1) Resmi ledajans hero endpoint
    r = requests.post(
        f"{site}/wp-json/ledajans/v1/hero-widget",
        json={
            "html": new_html,
            "page_id": DEFAULT_PAGE_ID,
            "widget_id": DEFAULT_WIDGET_ID,
        },
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print("hero-widget", r.status_code, r.text[:500])
    if r.status_code in (200, 201):
        return 0

    # 2) Fallback: yalnizca Widget 1 (ee08c77); diger HTML widget'lara dokunma
    print("FALLBACK: elementor meta update")
    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{DEFAULT_PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers={
            "User-Agent": UA,
            "Authorization": f"Basic {token}",
            "X-WP-Authorization": f"Basic {token}",
        },
        timeout=60,
    )
    print(f"page_get={rp.status_code}")
    if rp.status_code != 200:
        print(rp.text[:400])
        return 1

    page = rp.json()
    meta = page.get("meta") or {}
    raw = meta.get("_elementor_data")
    if not raw:
        print("HATA: _elementor_data yok")
        return 2

    data = json.loads(raw) if isinstance(raw, str) else raw
    changed = walk_replace(data, new_html, DEFAULT_WIDGET_ID)
    print(f"widgets_updated={changed}")
    if changed == 0:
        return 2

    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{DEFAULT_PAGE_ID}",
        json={"meta": {"_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":"))}},
        auth=auth,
        headers=headers,
        timeout=90,
    )
    print(f"page_update={ru.status_code} {ru.text[:300]}")
    return 0 if ru.status_code in (200, 201) else 1


if __name__ == "__main__":
    sys.exit(main())
