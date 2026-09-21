#!/usr/bin/env python3
"""P0 para sayfa hub icerigini (led-ekran.html) WP + Elementor widget'a yazar."""
from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-Money-Pages/1.1"

HUB = {
    "file": "LED Ekran/led-ekran.html",
    "slug": "led-ekran",
    "page_id": 5001,
}


def load_env() -> tuple[str, str, str]:
    path = os.path.join(ROOT, ".env")
    data: dict[str, str] = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip("\"'")
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    user = data.get("WP_USERNAME", "")
    pw = data.get("WP_APP_PASSWORD", "").replace(" ", "")
    return site, user, pw


def walk_set_html(nodes, new_html: str) -> list[str]:
    ids: list[str] = []
    if isinstance(nodes, list):
        for x in nodes:
            ids.extend(walk_set_html(x, new_html))
        return ids
    if not isinstance(nodes, dict):
        return ids
    settings = nodes.get("settings")
    if not isinstance(settings, dict):
        settings = None
    if settings is not None:
        wtype = nodes.get("widgetType")
        for field in ("html", "editor"):
            val = settings.get(field)
            if not isinstance(val, str):
                continue
            if "la-wrapper" in val or "la-card-img" in val:
                if wtype in ("html", "text-editor", None) or field in ("html", "editor"):
                    settings[field] = new_html
                    ids.append(f"{nodes.get('id')}:{field}")
                    break
    for key in ("elements", "content"):
        if key in nodes:
            ids.extend(walk_set_html(nodes[key], new_html))
    return ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1

    path = os.path.join(ROOT, HUB["file"].replace("/", os.sep))
    with open(path, encoding="utf-8") as f:
        content = f.read()

    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    if not args.apply:
        print(f"DRY-RUN: {HUB['slug']} id={HUB['page_id']} ({len(content)} karakter)")
        return 0

    r = requests.post(
        f"{site}/wp-json/wp/v2/pages/{HUB['page_id']}",
        json={"content": content},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    if r.status_code not in (200, 201):
        print(f"HATA HTTP {r.status_code}: {r.text[:400]}")
        return 1
    print(f"OK content: /{HUB['slug']}/ (id={HUB['page_id']})")

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{HUB['page_id']}",
        params={"context": "edit"},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    if rp.status_code != 200:
        print(f"HATA page_get {rp.status_code}: {rp.text[:400]}")
        return 1
    raw = (rp.json().get("meta") or {}).get("_elementor_data")
    if not raw:
        print("UYARI: _elementor_data yok")
        return 0
    data = json.loads(raw) if isinstance(raw, str) else raw
    ids = walk_set_html(data, content)
    print("elementor_widgets", ids)
    if not ids:
        print("HATA: HTML widget bulunamadi")
        return 2
    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{HUB['page_id']}",
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
    if ru.status_code not in (200, 201):
        print(f"HATA elementor {ru.status_code}: {ru.text[:400]}")
        return 1
    print(f"OK elementor: widgets={ids}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
