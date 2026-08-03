#!/usr/bin/env python3
"""Anasayfa Elementor'da tekrarlayan ledajans-hero HTML widget'larini temizle.

Varsayilan: ee08c77 kalsin; diger ledajans-hero HTML widget'lari bosaltilsin / kaldirilsin.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
PAGE_ID = 1248
KEEP_WIDGET_ID = "ee08c77"
MARKER = "ledajans-hero"
UA = "LEDAJANS-Fix-Duplicate-Heroes/1.0"


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


def find_heroes(nodes: Any, path: str = "") -> list[dict]:
    found = []
    if isinstance(nodes, list):
        for i, n in enumerate(nodes):
            found.extend(find_heroes(n, f"{path}/{i}"))
        return found
    if not isinstance(nodes, dict):
        return []
    wid = nodes.get("id", "?")
    wtype = nodes.get("widgetType") or nodes.get("elType")
    settings = nodes.get("settings") or {}
    html = settings.get("html") if isinstance(settings, dict) else None
    if wtype == "html" and isinstance(html, str) and MARKER in html:
        found.append(
            {
                "id": wid,
                "path": path,
                "bytes": len(html),
                "has_picture": "<picture>" in html,
            }
        )
    for key in ("elements", "content"):
        if key in nodes:
            found.extend(find_heroes(nodes[key], f"{path}/{key}"))
    return found


def clear_duplicates(nodes: Any, keep_id: str) -> int:
    """keep_id disindaki ledajans-hero HTML iceriklerini bosalt. Donus: temizlenen adet."""
    cleared = 0
    if isinstance(nodes, list):
        # element listesinde tamamen silmek daha temiz
        keep = []
        for n in nodes:
            if isinstance(n, dict):
                wtype = n.get("widgetType") or n.get("elType")
                settings = n.get("settings") or {}
                html = settings.get("html") if isinstance(settings, dict) else None
                wid = n.get("id")
                if (
                    wtype == "html"
                    and isinstance(html, str)
                    and MARKER in html
                    and wid != keep_id
                ):
                    cleared += 1
                    continue  # widget'i listeden cikar
                cleared += clear_duplicates(n, keep_id)
            keep.append(n)
        nodes[:] = keep
        return cleared
    if not isinstance(nodes, dict):
        return 0
    for key in ("elements", "content"):
        if key in nodes and isinstance(nodes[key], list):
            cleared += clear_duplicates(nodes[key], keep_id)
    return cleared


def remove_empty_sections(nodes: Any) -> int:
    """Icinde hic element kalmayan section'lari kaldir."""
    removed = 0
    if isinstance(nodes, list):
        keep = []
        for n in nodes:
            if isinstance(n, dict):
                removed += remove_empty_sections(n)
                eltype = n.get("elType")
                els = n.get("elements")
                if eltype == "section" and isinstance(els, list) and len(els) == 0:
                    removed += 1
                    continue
                # column with empty elements
                if eltype == "column" and isinstance(els, list) and len(els) == 0:
                    removed += 1
                    continue
            keep.append(n)
        nodes[:] = keep
        return removed
    if isinstance(nodes, dict):
        for key in ("elements", "content"):
            if key in nodes and isinstance(nodes[key], list):
                removed += remove_empty_sections(nodes[key])
    return removed


def main() -> int:
    dry = "--dry-run" in sys.argv
    remove_all = "--remove-all" in sys.argv
    keep_id = "" if remove_all else KEEP_WIDGET_ID

    site, user, pw = load_env()
    auth = (user, pw)
    h = {"User-Agent": UA}

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers=h,
        timeout=60,
    )
    print("page_get", rp.status_code)
    if rp.status_code != 200:
        print(rp.text[:400])
        return 1

    page = rp.json()
    raw = (page.get("meta") or {}).get("_elementor_data")
    if not raw:
        print("HATA: _elementor_data yok")
        return 1
    data = json.loads(raw) if isinstance(raw, str) else raw

    before = find_heroes(data)
    print("BEFORE heroes:")
    for x in before:
        print(" ", x)

    if not before:
        print("Hero yok")
        return 0

    if remove_all:
        cleared = clear_duplicates(data, keep_id="__none__")
    else:
        # keep ee08c77; if missing keep first
        ids = [x["id"] for x in before]
        if keep_id not in ids:
            keep_id = ids[0]
            print("WARN: ee08c77 yok, tutulan:", keep_id)
        cleared = clear_duplicates(data, keep_id=keep_id)

    empty_removed = remove_empty_sections(data)
    # nested empty cleanup second pass
    empty_removed += remove_empty_sections(data)

    after = find_heroes(data)
    print(f"cleared_widgets={cleared} empty_sections_removed={empty_removed}")
    print("AFTER heroes:")
    for x in after:
        print(" ", x)

    if dry:
        print("DRY_RUN")
        return 0

    payload = {
        "meta": {
            "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        }
    }
    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        json=payload,
        auth=auth,
        headers={**h, "Content-Type": "application/json"},
        timeout=90,
    )
    print("page_update", ru.status_code, ru.text[:250])
    if ru.status_code not in (200, 201):
        return 1

    # resmi hero endpoint ile cache purge (tek kalan hero)
    if after and not remove_all:
        hero_html = None

        def extract(nodes):
            nonlocal hero_html
            if hero_html is not None:
                return
            if isinstance(nodes, list):
                for n in nodes:
                    extract(n)
                return
            if isinstance(nodes, dict):
                if nodes.get("id") == keep_id:
                    hero_html = (nodes.get("settings") or {}).get("html")
                    return
                for key in ("elements", "content"):
                    if key in nodes:
                        extract(nodes[key])

        extract(data)
        if hero_html:
            rh = requests.post(
                f"{site}/wp-json/ledajans/v1/hero-widget",
                json={"html": hero_html, "page_id": PAGE_ID, "widget_id": keep_id},
                auth=auth,
                headers={**h, "Content-Type": "application/json"},
                timeout=120,
            )
            print("hero-widget purge", rh.status_code, rh.text[:200])

    return 0


if __name__ == "__main__":
    sys.exit(main())
