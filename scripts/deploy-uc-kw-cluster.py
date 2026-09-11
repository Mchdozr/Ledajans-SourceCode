#!/usr/bin/env python3
"""Üç KW cluster canlı deploy: Elementor HTML widget + yeni REST sayfalar (publish)."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-UcKw-Cluster-Deploy/1.0"

WIDGET_TARGETS: list[tuple[str, str, str, str]] = [
    # slug, relpath, unique marker in NEW html, unique marker in LIVE html (fallback)
    ("ic-mekan-led-ekran", "Urunlerimiz/Ic-Mekan-Led-Ekran/hero-banner.html", "İç Mekan LED Ekran", "ledajans-blog-hero"),
    ("ic-mekan-led-ekran", "Urunlerimiz/Ic-Mekan-Led-Ekran/ic-mekan-led-ekran-text.html", "İç Mekan LED Ekran – Indoor LED Ekran", "control-cards-content"),
    ("ic-mekan-led-ekran", "Urunlerimiz/Ic-Mekan-Led-Ekran/urun-ozellikleri.html", "Fansız SMPS", "product-features"),
    ("ic-mekan-led-ekran", "Urunlerimiz/Ic-Mekan-Led-Ekran/sss.html", "İç Mekan LED Ekran Hakkında Sık Sorulan Sorular", "la-faq-wrap"),
    ("dis-mekan-led-ekran", "Urunlerimiz/Dis-Mekan-Led-Ekran/hero-banner.html", "Dış Mekan LED Ekran", "ledajans-blog-hero"),
    ("dis-mekan-led-ekran", "Urunlerimiz/Dis-Mekan-Led-Ekran/dis-mekan-led-ekran-text.html", "Dış mekan LED ekran", "control-cards-content"),
    ("dis-mekan-led-ekran", "Urunlerimiz/Dis-Mekan-Led-Ekran/urun-ozellikleri.html", "IP65 koruma", "product-features"),
    ("dis-mekan-led-ekran", "Urunlerimiz/Dis-Mekan-Led-Ekran/ofc-serisi-outdoor.html", "la-ofc-hub", "la-ofc-hub"),
    ("dis-mekan-led-ekran", "Urunlerimiz/Dis-Mekan-Led-Ekran/sss.html", "Dış Mekan LED Ekran Hakkında Sık Sorulan Sorular", "la-faq-wrap"),
    ("", "Anasayfa/widget-3.html", "ledajans-about", "ledajans-about"),
    ("", "Anasayfa/widget-4-Ic-Mekan.html", "ledajans-indoor", "ledajans-indoor"),
    ("", "Anasayfa/widget-5-Dis-Mekan.html", "ledajans-outdoor", "ledajans-outdoor"),
    ("", "Anasayfa/widget-6-Urunlerimiz-Slider.html", "products-slider-section", "products-slider-section"),
    ("", "Anasayfa/widget-7-projeler.html", "ledajans-projects-page", "ledajans-projects-page"),
    ("led-ekran", "LED Ekran/led-ekran.html", "la-gradient-title", "la-wrapper"),
    ("ic-mekan-rgb-panel", "Urunlerimiz/Ic-Mekan-RGB-Panel/ic-mekan-icin-rgb-panel-text.html", "indoor-content-wrapper", "indoor-content-wrapper"),
    ("ic-mekan-rgb-panel", "Urunlerimiz/Ic-Mekan-RGB-Panel/tablo-ic-mekan-rgb-gob-led-paneller.html", "la-gob-hub", "la-gob-hub"),
    ("program-indir", "Teknik-Destek-Bilgi/Program-indir/hero-banner.html", "pi-hub-links", "ledajans-blog-hero"),
]

REST_PAGES = [
    ("Urunlerimiz/Gob-Led-Ekran/page.html", "gob-led-ekran", "GOB LED Ekran", "page"),
    ("SEO-Icerik-Widgets/karsilastirmalar/gob-vs-cob-smd.html", "gob-vs-cob-smd", "GOB vs COB vs SMD LED Ekran", "page"),
    ("SEO-Icerik-Widgets/sozluk/gob-led-nedir.html", "gob-led-nedir", "GOB LED Nedir?", "page"),
    ("SEO-Icerik-Widgets/karsilastirmalar/cob-led-ne-zaman.html", "cob-led-ne-zaman", "COB LED Ne Zaman Tercih Edilmeli?", "page"),
    ("Blog/gob-led-ekran-ne-zaman-tercih-edilir.html", "gob-led-ekran-ne-zaman-tercih-edilir", "GOB LED Ekran Ne Zaman Tercih Edilir?", "post"),
]


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    path = ROOT / ".env"
    for line in path.read_text(encoding="utf-8-sig").splitlines():
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


def walk_html_widgets(nodes: Any) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(nodes, list):
        for n in nodes:
            out.extend(walk_html_widgets(n))
        return out
    if not isinstance(nodes, dict):
        return []
    if nodes.get("widgetType") == "html":
        html = (nodes.get("settings") or {}).get("html") or ""
        if isinstance(html, str):
            out.append((str(nodes.get("id")), html))
    for key in ("elements", "content"):
        if key in nodes:
            out.extend(walk_html_widgets(nodes[key]))
    return out


def find_page(site: str, slug: str, auth: tuple[str, str], headers: dict, post_type: str = "page") -> dict | None:
    endpoint = "pages" if post_type == "page" else "posts"
    r = requests.get(
        f"{site}/wp-json/wp/v2/{endpoint}",
        params={"slug": slug, "status": "any", "context": "edit"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    if r.status_code != 200 or not r.json():
        return None
    return r.json()[0]


def get_page_edit(site: str, page_id: int, auth: tuple[str, str], headers: dict) -> dict:
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/{page_id}",
        params={"context": "edit"},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def match_widget(widgets: list[tuple[str, str]], new_html: str, live_marker: str) -> str | None:
    hits = []
    for wid, html in widgets:
        if live_marker and live_marker in html:
            hits.append(wid)
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        # prefer widget whose live html shares a distinctive new snippet
        for snippet in ("Fansız SMPS", "pi-hub-links", "gob-led-ekran", "İç mekan RGB panel"):
            if snippet in new_html:
                for wid, html in widgets:
                    if snippet in html:
                        return wid
        return hits[0]
    return None


def extract_meta_description(html: str) -> str:
    import re

    m = re.search(r"<!-- SEO Meta Description:\s*(.+?)\s*-->", html)
    return m.group(1).strip() if m else ""


def extract_focus(html: str) -> str:
    import re

    m = re.search(r"<!-- SEO Focus Keyword:\s*(.+?)\s*-->", html)
    return m.group(1).strip() if m else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--discover", action="store_true")
    args = parser.parse_args()
    site, user, pw = load_env()
    if not user or pw == "":
        print("HATA: .env")
        return 1
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    me = requests.get(f"{site}/wp-json/wp/v2/users/me", auth=auth, headers=headers, timeout=30)
    print("auth", me.status_code)
    if me.status_code != 200:
        print(me.text[:300])
        return 1

    home = find_page(site, "", auth, headers)
    # homepage is page_on_front 1248
    slug_ids: dict[str, int] = {"": 1248}
    for slug in {
        "ic-mekan-led-ekran",
        "dis-mekan-led-ekran",
        "led-ekran",
        "ic-mekan-rgb-panel",
        "program-indir",
        "cob-led-ne-zaman",
        "gob-led-nedir",
    }:
        p = find_page(site, slug, auth, headers)
        if p:
            slug_ids[slug] = int(p["id"])
            print(f"page {slug} id={p['id']} status={p.get('status')}")
        else:
            print(f"page {slug} YOK")

    cache: dict[int, list[tuple[str, str]]] = {}

    def widgets_for(slug: str) -> list[tuple[str, str]]:
        pid = slug_ids[slug]
        if pid not in cache:
            page = get_page_edit(site, pid, auth, headers)
            raw = (page.get("meta") or {}).get("_elementor_data")
            if not raw:
                cache[pid] = [("__content__", str(page.get("content", {}).get("raw") or ""))]
            else:
                data = json.loads(raw) if isinstance(raw, str) else raw
                cache[pid] = walk_html_widgets(data)
            print(f"  widgets {slug or 'home'} n={len(cache[pid])}")
            if args.discover:
                for wid, html in cache[pid]:
                    preview = html.replace("\n", " ")[:90].encode("ascii", "replace").decode()
                    print(f"    {wid} {len(html):6d} {preview}")
        return cache[pid]

    pairs: list[tuple[int, str, str, Path]] = []
    misses = 0
    for slug, rel, _new_m, live_m in WIDGET_TARGETS:
        path = ROOT / rel.replace("/", os.sep)
        html = path.read_text(encoding="utf-8")
        wlist = widgets_for(slug)
        wid = None
        if wlist and wlist[0][0] == "__content__":
            pairs.append((slug_ids[slug], "__content__", html, path))
            print(f"MAP content {slug} <- {path.name}")
            continue
        wid = match_widget(wlist, html, live_m)
        if not wid:
            print(f"MISS {slug or 'home'} {path.name} marker={live_m}")
            misses += 1
            continue
        pairs.append((slug_ids[slug], wid, html, path))
        print(f"MAP {slug or 'home'} {wid} <- {path.name} ({len(html)})")

    if args.discover:
        return 0 if misses == 0 else 1

    print(f"\nwidget maps={len(pairs)} misses={misses}")
    if misses:
        print("NO-GO: widget eşleşmesi eksik")
        return 1

    if not args.apply:
        print("DRY-RUN: yazılmadı")
        for file_path, slug, title, ptype in REST_PAGES:
            existing = find_page(site, slug, auth, headers, "page" if ptype == "page" else "post")
            print(f"  REST {'GÜNCELLE' if existing else 'YENİ'} {slug} ({ptype})")
        return 0

    ok = True
    for pid, wid, html, path in pairs:
        if wid == "__content__":
            r = requests.post(
                f"{site}/wp-json/wp/v2/pages/{pid}",
                json={"content": html, "status": "publish"},
                auth=auth,
                headers=headers,
                timeout=180,
            )
            print("content", pid, path.name, r.status_code)
            if r.status_code not in (200, 201):
                ok = False
                print(r.text[:300])
            continue
        r = requests.post(
            f"{site}/wp-json/ledajans/v1/hero-widget",
            json={"html": html, "page_id": pid, "widget_id": wid},
            auth=auth,
            headers=headers,
            timeout=180,
        )
        print("widget", pid, wid, path.name, r.status_code, r.text[:120])
        if r.status_code not in (200, 201):
            ok = False

    for file_path, slug, title, ptype in REST_PAGES:
        content = (ROOT / file_path.replace("/", os.sep)).read_text(encoding="utf-8")
        meta_desc = extract_meta_description(content)
        focus = extract_focus(content)
        existing = find_page(site, slug, auth, headers, ptype)
        endpoint = "pages" if ptype == "page" else "posts"
        payload: dict[str, Any] = {
            "title": title,
            "slug": slug,
            "content": content,
            "status": "publish",
        }
        if meta_desc:
            payload["excerpt"] = meta_desc
            payload["meta"] = {
                "rank_math_description": meta_desc,
                "rank_math_title": title,
            }
            if focus:
                payload["meta"]["rank_math_focus_keyword"] = focus
        if existing:
            url = f"{site}/wp-json/wp/v2/{endpoint}/{existing['id']}"
        else:
            url = f"{site}/wp-json/wp/v2/{endpoint}"
        r = requests.post(url, json=payload, auth=auth, headers=headers, timeout=180)
        print("REST", slug, r.status_code, "id", (r.json() or {}).get("id") if r.headers.get("content-type", "").startswith("application/json") else "")
        if r.status_code not in (200, 201):
            ok = False
            print(r.text[:400])

    csv_path = ROOT / "AGENT-HUB" / "cluster-301.csv"
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        redir_ok = 0
        for row in rows:
            src = row["source"].replace(site, "")
            dst = row["target"].replace(site, "")
            body = {"url_from": src, "url_to": dst, "header_code": "301"}
            rr = requests.post(
                f"{site}/wp-json/rankmath/v1/redirections",
                json=body,
                auth=auth,
                headers=headers,
                timeout=30,
            )
            if rr.status_code in (200, 201):
                redir_ok += 1
            else:
                print("301 skip", src, rr.status_code)
        print(f"rankmath 301 ok={redir_ok}/{len(rows)}")

    requests.post(f"{site}/wp-json/ledajans/v1/purge", auth=auth, headers=headers, timeout=60)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
