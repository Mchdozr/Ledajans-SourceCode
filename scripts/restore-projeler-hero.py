#!/usr/bin/env python3
"""Restore /projeler/ hero widget overwritten by full grid HTML."""
from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "LEDAJANS-restore-hero/1"}
PAGE_ID = 4956
HERO_ID = "a0baf1e"
GRID_ID = "3f35913"
WIDGET_FILE = ROOT / "Anasayfa" / "widget-7-projeler.html"
NEW_URL = "https://ledajans.com/wp-content/uploads/2026/09/dis-mekan-led-ekran-referans.webp"
OLD_GIF = "https://ledajans.com/wp-content/uploads/2026/04/dis-mekan-led-ekran.gif"


def load_env():
    data = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    auth = (data["WP_USERNAME"], data["WP_APP_PASSWORD"].replace(" ", ""))
    return site, auth


def walk_set(nodes, widget_id: str, html: str) -> int:
    n = 0
    if isinstance(nodes, list):
        return sum(walk_set(x, widget_id, html) for x in nodes)
    if not isinstance(nodes, dict):
        return 0
    if str(nodes.get("id")) == widget_id and nodes.get("widgetType") == "html":
        nodes.setdefault("settings", {})["html"] = html
        n += 1
    for key in ("elements", "content"):
        if key in nodes:
            n += walk_set(nodes[key], widget_id, html)
    return n


def walk_get(nodes, widget_id: str) -> str | None:
    if isinstance(nodes, list):
        for x in nodes:
            found = walk_get(x, widget_id)
            if found is not None:
                return found
        return None
    if not isinstance(nodes, dict):
        return None
    if str(nodes.get("id")) == widget_id:
        return (nodes.get("settings") or {}).get("html")
    for key in ("elements", "content"):
        if key in nodes:
            found = walk_get(nodes[key], widget_id)
            if found is not None:
                return found
    return None


def main() -> int:
    site, auth = load_env()
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}/revisions",
        params={"per_page": 5, "context": "edit"},
        auth=auth,
        headers=UA,
        timeout=60,
    )
    local_hero = (ROOT / "Anasayfa" / "widget-projeler-hero.html").read_text(encoding="utf-8")
    revs = r.json()
    rev_hero = walk_get(json.loads(revs[0]["meta"]["_elementor_data"]), HERO_ID) or ""
    hero = local_hero if "ledajans-projects-hero" in local_hero else rev_hero
    if "ledajans-projects-hero" not in hero:
        print("HATA hero bulunamadi")
        return 2
    print("hero_len", len(hero), "rev_len", len(rev_hero), "source", "local" if hero == local_hero else "rev")

    grid = WIDGET_FILE.read_text(encoding="utf-8")
    print("grid_webp", NEW_URL in grid, "grid_gif", OLD_GIF in grid)

    p = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers=UA,
        timeout=60,
    )
    data = json.loads(p.json()["meta"]["_elementor_data"])
    n1 = walk_set(data, HERO_ID, hero)
    n2 = walk_set(data, GRID_ID, grid)
    print("set", n1, n2)
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
        headers={**UA, "Content-Type": "application/json"},
        timeout=120,
    )
    print("page_update", ru.status_code)
    dc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers=UA,
        timeout=30,
    )
    print("cache_delete", dc.status_code)
    live = requests.get(
        f"{site}/projeler/?nocache=projeref4",
        headers={**UA, "Cache-Control": "no-cache"},
        timeout=45,
    )
    print(
        "live",
        live.status_code,
        "heroes",
        live.text.count("ledajans-projects-hero"),
        "pages",
        live.text.count("ledajans-projects-page"),
        "webp",
        NEW_URL in live.text,
        "gif",
        OLD_GIF in live.text,
        "hero_comment",
        "Projeler Sayfası Hero" in live.text or "projects-hero" in live.text,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
