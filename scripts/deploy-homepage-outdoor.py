#!/usr/bin/env python3
"""Ana sayfa dış mekan HTML — Elementor _elementor_data walk_replace (ledajans-outdoor)."""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDOOR_PATH = os.path.join(ROOT, "Anasayfa", "widget-5-Dis-Mekan.html")
UA = "LEDAJANS-Deploy-Homepage-Outdoor/1.0"
MARKER = "ledajans-outdoor"
DEFAULT_PAGE_ID = 1248


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


def walk_replace(nodes: Any, new_html: str) -> int:
    changed = 0
    if isinstance(nodes, list):
        for n in nodes:
            changed += walk_replace(n, new_html)
        return changed
    if not isinstance(nodes, dict):
        return 0

    widget_type = nodes.get("widgetType") or nodes.get("elType")
    settings = nodes.get("settings") or {}
    html_val = settings.get("html")
    if widget_type == "html" and isinstance(html_val, str) and MARKER in html_val:
        settings["html"] = new_html
        nodes["settings"] = settings
        changed += 1

    for key in ("elements", "content"):
        if key in nodes:
            changed += walk_replace(nodes[key], new_html)
    return changed


def main() -> int:
    dry = "--dry-run" in sys.argv
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1
    if not os.path.isfile(OUTDOOR_PATH):
        print("HATA: widget-5-Dis-Mekan.html yok")
        return 1

    new_html = open(OUTDOOR_PATH, encoding="utf-8").read()
    if MARKER not in new_html:
        print("HATA: outdoor marker yok")
        return 1
    if "Basliksiz-5" in new_html:
        print("HATA: eski Basliksiz-5 src duruyor")
        return 1
    if "dis-mekan-led-cephe.webp" not in new_html:
        print("HATA: yeni cephe webp yok")
        return 1
    if "@keyframes" in new_html or "animation:" in new_html:
        print("HATA: outdoor animasyon olmamali")
        return 1
    if "max-height: 420px" not in new_html or "max-height: 480px" not in new_html:
        print("HATA: indoor max-height 420/480 yok")
        return 1
    if "max-height: 500px" not in new_html:
        print("HATA: indoor max-height 500 yok")
        return 1
    if "width: 70%" not in new_html or "max-width: 480px" not in new_html:
        print("HATA: indoor width/max-width yok")
        return 1
    if "object-fit: contain" not in new_html:
        print("HATA: object-fit contain yok")
        return 1
    if "max-height: none" in new_html or "height: 560px" in new_html:
        print("HATA: eski buyuk boyut duruyor")
        return 1
    if "box-shadow: 0 25px" in new_html:
        print("HATA: kutu golgesi duruyor")
        return 1
    if "ledajans-indoor" in new_html or "ledajans-hero" in new_html:
        print("HATA: indoor/hero karisti")
        return 1

    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    if dry:
        print("DRY_RUN: yazilmadi")
        return 0

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{DEFAULT_PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers={"User-Agent": UA},
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

    backup_dir = os.path.join(ROOT, "AGENT-HUB", "BACKUPS")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, "2026-09-11-home-1248-elementor-pre-outdoor.json")
    with open(backup_path, "w", encoding="utf-8") as bf:
        bf.write(raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False))
    print("backup", backup_path)

    data = json.loads(raw) if isinstance(raw, str) else raw
    changed = walk_replace(data, new_html)
    print(f"widgets_updated={changed}")
    if changed == 0:
        return 2
    if changed > 1:
        print("HATA: birden fazla outdoor widget")
        return 2

    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{DEFAULT_PAGE_ID}",
        json={"meta": {"_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":"))}},
        auth=auth,
        headers=headers,
        timeout=90,
    )
    print(f"page_update={ru.status_code} {ru.text[:300]}")
    if ru.status_code not in (200, 201):
        return 1
    rc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    print("elementor_cache_del", rc.status_code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
