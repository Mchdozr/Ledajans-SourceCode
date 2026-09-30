#!/usr/bin/env python3
"""Canlı ledajans.com Türkçe içeriğini widget bazında CANLI-SITE/ altına dışa aktarır (salt okunur).

python scripts/export-live-site.py            # tümü
python scripts/export-live-site.py --no-live  # canlı HTML kontrolü olmadan (hızlı)
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledajans_model_layout import wp_session  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "CANLI-SITE"
UA = "Mozilla/5.0 (LEDAJANS site export)"
FOREIGN = re.compile(r"^/(en|de)(/|$)")
TEXT_KEYS = {
    "html": "html",
    "text-editor": "editor",
    "heading": "title",
    "shortcode": "shortcode",
}
COLLECTIONS = [
    ("pages", "pages", True),
    ("posts", "posts", True),
    ("elementor_library", "templates/elementor", False),
    ("elementor_snippet", "templates/snippets", False),
    ("popups", "templates/popups", False),
]


def safe(name: str) -> str:
    name = unquote(name or "").strip().lower()
    return re.sub(r"[^0-9a-zçğıöşü._-]+", "-", name).strip("-") or "item"


def fetch_all(s: requests.Session, site: str, rest: str) -> list[dict[str, Any]]:
    out, page = [], 1
    while True:
        r = s.get(f"{site}/wp-json/wp/v2/{rest}",
                  params={"per_page": 100, "page": page, "status": "publish", "context": "edit"}, timeout=120)
        if r.status_code != 200:
            break
        data = r.json()
        out.extend(data)
        if not data or page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
    return out


def is_turkish(item: dict[str, Any]) -> bool:
    return not FOREIGN.match(urlparse(item.get("link") or "").path)


def widget_label(el: dict[str, Any]) -> str:
    s = el.get("settings") or {}
    for key in ("title", "_title", "text", "heading_title", "editor", "html"):
        v = s.get(key)
        if isinstance(v, str) and v.strip():
            txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<(style|script)[^>]*>.*?</\1>|<[^>]+>", " ", v, flags=re.S))).strip()
            if txt:
                return txt[:80]
    return ""


def walk(elements: list[dict[str, Any]], wdir: Path, prefix: str, depth: int, lines: list[str], stats: dict[str, int]) -> None:
    for i, el in enumerate(elements, 1):
        kind = el.get("elType", "?")
        wtype = el.get("widgetType", "")
        code = {"section": "s", "column": "c", "container": "k", "widget": "w"}.get(kind, "x")
        path = f"{prefix}{code}{i:02d}"
        indent = "  " * depth
        if kind == "widget":
            stats["widgets"] += 1
            settings = el.get("settings") or {}
            key = TEXT_KEYS.get(wtype)
            if key and isinstance(settings.get(key), str):
                fname = f"{path}-{wtype}-{el.get('id')}.html"
                (wdir / fname).write_text(settings[key], encoding="utf-8")
            else:
                fname = f"{path}-{wtype}-{el.get('id')}.json"
                (wdir / fname).write_text(json.dumps(settings, ensure_ascii=False, indent=1), encoding="utf-8")
            label = widget_label(el)
            lines.append(f"{indent}- **{wtype}** `{el.get('id')}` → [`widgets/{fname}`](widgets/{fname})"
                         + (f" — {label}" if label else ""))
        else:
            title = (el.get("settings") or {}).get("_title") or ""
            lines.append(f"{indent}- {kind} `{el.get('id')}`" + (f" ({title})" if title else ""))
            walk(el.get("elements") or [], wdir, f"{path}-", depth + 1, lines, stats)


def live_info(url: str, ua: str) -> dict[str, Any]:
    try:
        r = requests.get(url, headers={"User-Agent": ua}, timeout=45, allow_redirects=False)
    except requests.RequestException as exc:
        return {"status": f"ERR {type(exc).__name__}"}
    info: dict[str, Any] = {"status": r.status_code}
    if r.status_code in (301, 302, 307, 308):
        info["redirect"] = r.headers.get("Location")
        return info
    if r.status_code != 200:
        return info
    soup = BeautifulSoup(r.text, "html.parser")

    def meta(name: str, attr: str = "name") -> str:
        tag = soup.find("meta", attrs={attr: name})
        return tag.get("content", "") if tag else ""

    canon = soup.find("link", rel="canonical")
    info.update({
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "description": meta("description"),
        "robots": meta("robots"),
        "canonical": canon.get("href") if canon else "",
        "og_image": meta("og:image", "property"),
        "h1": [h.get_text(" ", strip=True) for h in soup.find_all("h1")],
        "h2": [h.get_text(" ", strip=True) for h in soup.find_all("h2")][:40],
        "schema_types": sorted({t for s in soup.find_all("script", type="application/ld+json")
                                for t in re.findall(r'"@type"\s*:\s*"([^"]+)"', s.string or "")}),
        "elementor_docs": [f"{d.get('data-elementor-id')}:{d.get('data-elementor-post-type')}"
                           for d in soup.select("[data-elementor-type]")
                           if not d.parent.find_parent(attrs={"data-elementor-type": True})],
    })
    return info


def export_item(item: dict[str, Any], base: Path, rest: str, do_live: bool) -> dict[str, Any]:
    path = urlparse(item.get("link") or "").path.strip("/") if rest in ("pages", "posts") else ""
    slug = "anasayfa" if rest == "pages" and not path else safe(path.replace("/", "__") or item.get("slug") or str(item["id"]))
    d = base / slug
    if d.exists():
        d = base / f"{slug}-{item['id']}"
    wdir = d / "widgets"
    wdir.mkdir(parents=True)
    meta = item.get("meta") or {}
    raw_el = meta.get("_elementor_data") or ""
    elements: list[dict[str, Any]] = []
    if isinstance(raw_el, str) and raw_el.strip().startswith("["):
        elements = json.loads(raw_el)
    elif isinstance(raw_el, list):
        elements = raw_el
    content = (item.get("content") or {}).get("raw") or ""
    if content:
        (d / "content.html").write_text(content, encoding="utf-8")
    if elements:
        (d / "elementor.json").write_text(json.dumps(elements, ensure_ascii=False, indent=1), encoding="utf-8")
    if rest == "elementor_snippet" and meta.get("_elementor_code"):
        (d / "snippet.html").write_text(meta["_elementor_code"], encoding="utf-8")

    stats = {"widgets": 0}
    tree: list[str] = []
    walk(elements, wdir, "", 0, tree, stats)
    if not stats["widgets"]:
        wdir.rmdir()

    title = (item.get("title") or {}).get("raw") or (item.get("title") or {}).get("rendered") or ""
    live = live_info(item["link"], UA) if do_live and item.get("link") else {}
    info = {
        "id": item["id"], "type": item.get("type"), "title": title, "slug": unquote(item.get("slug") or ""),
        "link": item.get("link"), "status": item.get("status"), "template": item.get("template"),
        "parent": item.get("parent"), "date": item.get("date"), "modified": item.get("modified"),
        "excerpt": (item.get("excerpt") or {}).get("raw"), "featured_media": item.get("featured_media"),
        "categories": item.get("categories"), "tags": item.get("tags"),
        "rank_math": {k: v for k, v in meta.items() if k.startswith("rank_math")},
        "elementor": {k: v for k, v in meta.items() if k.startswith("_elementor") and k != "_elementor_data"},
        "widget_count": stats["widgets"], "live": live,
    }
    (d / "page.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")

    rm = info["rank_math"]
    md = [
        f"# {title}", "",
        f"- **URL:** {item.get('link')}",
        f"- **WP ID:** {item['id']} · **Tür:** {item.get('type')} · **Şablon:** {item.get('template') or '-'}",
        f"- **Son değişiklik:** {item.get('modified')}",
        f"- **Rank Math başlık:** {rm.get('rank_math_title') or '-'}",
        f"- **Rank Math açıklama:** {rm.get('rank_math_description') or '-'}",
        f"- **Odak kelime:** {rm.get('rank_math_focus_keyword') or '-'}",
    ]
    if live:
        md += [f"- **Canlı durum:** {live.get('status')}" + (f" → {live['redirect']}" if live.get("redirect") else ""),
               f"- **Canlı H1:** {' | '.join(live.get('h1') or []) or '-'}",
               f"- **Robots:** {live.get('robots') or '-'} · **Canonical:** {live.get('canonical') or '-'}"]
    md += ["", "## Dosyalar", "",
           "- `page.json` — tüm meta (Rank Math, Elementor ayarları, canlı kontrol)"]
    if elements:
        md.append("- `elementor.json` — Elementor verisinin tamamı (WordPress'teki `_elementor_data`)")
    if content:
        md.append("- `content.html` — WordPress içerik alanı (post_content)")
    if tree:
        md += ["", f"## Yapı ({stats['widgets']} widget)", "", *tree]
    (d / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"folder": d.relative_to(OUT).as_posix(), **{k: info[k] for k in ("id", "type", "title", "link", "widget_count")},
            "live_status": live.get("status", ""), "focus": rm.get("rank_math_focus_keyword") or ""}


def export_menus(s: requests.Session, site: str) -> list[dict[str, Any]]:
    menus = s.get(f"{site}/wp-json/wp/v2/menus", params={"per_page": 100, "context": "edit"}, timeout=60)
    menus = menus.json() if menus.status_code == 200 else []
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        r = s.get(f"{site}/wp-json/wp/v2/menu-items", params={"per_page": 100, "page": page, "context": "edit"}, timeout=60)
        if r.status_code != 200 or not r.json():
            break
        items.extend(r.json())
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
    d = OUT / "menus"
    d.mkdir(parents=True)
    md = ["# Menüler", ""]
    summary = []
    for m in menus:
        mi = sorted([i for i in items if i.get("menus") == m["id"]], key=lambda i: i.get("menu_order", 0))
        (d / f"{safe(m.get('slug') or m['name'])}.json").write_text(json.dumps({"menu": m, "items": mi}, ensure_ascii=False, indent=1), encoding="utf-8")
        md += [f"## {m['name']} (id {m['id']}, konum: {', '.join(m.get('locations') or []) or '-'})", ""]
        by_parent: dict[int, list[dict[str, Any]]] = {}
        for i in mi:
            by_parent.setdefault(i.get("parent", 0), []).append(i)

        def emit(pid: int, depth: int) -> None:
            for i in by_parent.get(pid, []):
                md.append(f"{'  ' * depth}- {(i.get('title') or {}).get('rendered', '')} → {i.get('url')} (id {i['id']})")
                emit(i["id"], depth + 1)
        emit(0, 0)
        md.append("")
        summary.append({"id": m["id"], "name": m["name"], "items": len(mi)})
    (d / "README.md").write_text("\n".join(md), encoding="utf-8")
    return summary


def export_theme_parts(site: str) -> list[str]:
    r = requests.get(f"{site}/", headers={"User-Agent": UA}, timeout=60)
    soup = BeautifulSoup(r.text, "html.parser")
    d = OUT / "templates" / "theme-parts"
    d.mkdir(parents=True)
    saved = []
    for doc in soup.select('[data-elementor-post-type="gva__template"]'):
        if doc.find_parent(attrs={"data-elementor-type": True}):
            continue
        name = f"{doc.get('data-elementor-type', 'part')}-{doc.get('data-elementor-id')}.html"
        (d / name).write_text(doc.prettify(), encoding="utf-8")
        saved.append(name)
    (d / "README.md").write_text(
        "# Tema parçaları (header / footer)\n\nGavias `gva__template` şablonları REST'te açık değil; "
        "anasayfanın canlı HTML'inden alınan render çıktısıdır (yalnızca referans). Düzenleme: "
        "WP Admin → Gavias Templates → Elementor.\n\n" + "\n".join(f"- `{n}`" for n in saved) + "\n", encoding="utf-8")
    return saved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-live", action="store_true")
    args = ap.parse_args()
    s, site = wp_session(UA)
    s.headers.pop("Content-Type", None)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    started = time.time()
    index: dict[str, list[dict[str, Any]]] = {}
    for rest, folder, needs_tr in COLLECTIONS:
        items = [i for i in fetch_all(s, site, rest) if not needs_tr or is_turkish(i)]
        base = OUT / folder
        base.mkdir(parents=True)
        rows = []
        for n, it in enumerate(sorted(items, key=lambda x: x.get("link") or ""), 1):
            rows.append(export_item(it, base, rest, args.no_live is False and needs_tr))
            print(f"{rest} {n}/{len(items)} {rows[-1]['folder']} w={rows[-1]['widget_count']} live={rows[-1]['live_status']}", flush=True)
        index[folder] = rows
    menus = export_menus(s, site)
    parts = export_theme_parts(site)

    (OUT / "index.json").write_text(json.dumps({"exported_at": datetime.now().isoformat(timespec="seconds"),
                                                "site": site, "collections": index, "menus": menus,
                                                "theme_parts": parts}, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [
        "# CANLI-SITE — ledajans.com Türkçe içerik haritası", "",
        f"Dışa aktarım: {datetime.now():%Y-%m-%d %H:%M} · kaynak: {site} (yayındaki içerik, REST `context=edit`).",
        "Yeniden üretmek için: `python scripts/export-live-site.py` (klasörü baştan yazar, salt okunur).", "",
        "## Nasıl bulunur / değiştirilir", "",
        "- Her sayfa kendi klasöründe: `README.md` (özet + widget ağacı), `page.json` (Rank Math, ayarlar, canlı kontrol), "
        "`elementor.json` (tam Elementor verisi), `widgets/` (her widget ayrı dosya).",
        "- Widget dosya adı = konum + tür + Elementor ID: `s02-c01-w03-html-7a1b2c3.html` → 2. bölüm, 1. sütun, 3. widget. "
        "Elementor editöründe aynı ID ile bulunur.",
        "- Metin arama: `rg \"aranan metin\" CANLI-SITE` → dosya yolu hangi sayfa/widget olduğunu söyler.",
        "- Header/footer: `templates/theme-parts/`, menüler: `menus/`, Elementor şablonları: `templates/elementor/`.", "",
    ]
    for folder, rows in index.items():
        md += [f"## {folder} ({len(rows)})", "", "| Başlık | URL | Widget | Canlı | Odak | Klasör |", "|---|---|---|---|---|---|"]
        for r in rows:
            md.append(f"| {r['title'].replace('|', '/')} | {r['link']} | {r['widget_count']} | {r['live_status']} | "
                      f"{r['focus'].replace('|', '/')} | [`{r['folder']}`]({r['folder']}/README.md) |")
        md.append("")
    md += ["## Menüler", "", *[f"- {m['name']} ({m['items']} öğe)" for m in menus], "", "- Detay: [`menus/README.md`](menus/README.md)", ""]
    (OUT / "README.md").write_text("\n".join(md), encoding="utf-8")
    total_w = sum(r["widget_count"] for rows in index.values() for r in rows)
    print(f"DONE {sum(len(v) for v in index.values())} öğe, {total_w} widget, {len(menus)} menü, {len(parts)} tema parçası, {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
