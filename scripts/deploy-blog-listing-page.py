#!/usr/bin/env python3
"""Blog/blog.html (+ header-banner) -> WP sayfa 27 Elementor widget."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Deploy-Blog-Listing/1.0"
PAGE_ID = 27
POSTS_WIDGET_ID = "9678132"
BREADCRUMB_WIDGET_ID = "c198af0"
BLOG_FILE = ROOT / "Blog" / "blog.html"
HERO_FILE = ROOT / "Blog" / "header-banner.html"


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


def walk_replace(nodes, widget_id: str, html: str) -> int:
    n = 0
    if isinstance(nodes, list):
        for x in nodes:
            n += walk_replace(x, widget_id, html)
        return n
    if not isinstance(nodes, dict):
        return 0
    if nodes.get("id") == widget_id:
        nodes["elType"] = "widget"
        nodes["widgetType"] = "html"
        nodes["elements"] = []
        nodes["settings"] = {"html": html}
        n += 1
    if nodes.get("id") == "2ac74c4" and nodes.get("elType") == "section":
        settings = nodes.get("settings") or {}
        settings["padding"] = {
            "unit": "px",
            "top": "0",
            "right": "0",
            "bottom": "0",
            "left": "0",
            "isLinked": True,
        }
        settings["padding_tablet"] = {
            "unit": "px",
            "top": "0",
            "right": "0",
            "bottom": "0",
            "left": "0",
            "isLinked": True,
        }
        nodes["settings"] = settings
    for key in ("elements", "content"):
        if key in nodes:
            n += walk_replace(nodes[key], widget_id, html)
    return n


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    blog_html = BLOG_FILE.read_text(encoding="utf-8")
    hero_html = HERO_FILE.read_text(encoding="utf-8")
    if "ledajans-blog-section" not in blog_html:
        print("HATA: blog.html grid yok")
        return 1
    if "ledajans-blog-hero" not in hero_html:
        print("HATA: header-banner.html hero yok")
        return 1

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
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
    raw = (page.get("meta") or {}).get("_elementor_data")
    if not raw:
        print("HATA: _elementor_data yok")
        return 2
    data = json.loads(raw) if isinstance(raw, str) else raw
    n_posts = walk_replace(data, POSTS_WIDGET_ID, blog_html)
    n_hero = walk_replace(data, BREADCRUMB_WIDGET_ID, hero_html)
    print(f"replaced_posts={n_posts} replaced_hero={n_hero}")
    if n_posts != 1 or n_hero != 1:
        return 2

    dump = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if "ledajans-blog-section" not in dump or "ledajans-blog-hero" not in dump:
        print("HATA: dump icinde grid/hero yok")
        return 2
    if '"widgetType":"gva-posts"' in dump:
        print("HATA: gva-posts hala var")
        return 2

    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        json={
            "content": "",
            "meta": {"_elementor_data": dump},
        },
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print(f"page_update={ru.status_code} {ru.text[:250]}")
    if ru.status_code not in (200, 201):
        return 1

    dc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=30,
    )
    print("elementor_cache_delete", dc.status_code)

    live = requests.get(
        f"{site}/blog/?nocache=bloggrid1",
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=45,
    )
    html = live.text
    print(f"live_status={live.status_code} bytes={len(html)}")
    print(f"has_grid={'ledajans-blog-section' in html}")
    print(f"has_search={'ledajans-blog-search' in html}")
    print(f"has_hero={'ledajans-blog-hero' in html}")
    print(f"has_gva_posts={'gva-posts' in html or 'gva_posts' in html}")
    ok = (
        live.status_code == 200
        and "ledajans-blog-section" in html
        and "ledajans-blog-search" in html
        and "ledajans-blog-hero" in html
    )
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
