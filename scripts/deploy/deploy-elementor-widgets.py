#!/usr/bin/env python3
"""Elementor HTML widget deploy — ledajans/v1/hero-widget + _elementor_data insert."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import argparse
import json
import os
import secrets
import sys
import time

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)


WIDGETS = [
    {
        "label": "Anasayfa Hero",
        "page_id": 1248,
        "widget_id": "ee08c77",
        "file": "Anasayfa/Hero.html",
    },
    {
        "label": "/led-ekran/ hub",
        "page_id": 5557,
        "widget_id": "25a1bb2",
        "file": "LED Ekran/led-ekran.html",
    },
    {
        "label": "Anasayfa Hakkımızda",
        "page_id": 1248,
        "widget_id": "48f4925",
        "file": "Anasayfa/widget-3.html",
    },
    {
        "label": "Anasayfa Blog",
        "page_id": 1248,
        "widget_id": "7551f23",
        "file": "Anasayfa/widget-9-Blog.html",
    },
    {
        "label": "/ic-mekan-led-ekran/ SEO",
        "page_id": 6004,
        "widget_id": "9247047",
        "file": "Urunlerimiz/Ic-Mekan-Led-Ekran/ic-mekan-led-ekran-text.html",
    },
    {
        "label": "/ic-mekan-led-ekran/ FAQ",
        "page_id": 6004,
        "widget_id": "2ff9b0d",
        "file": "Urunlerimiz/Ic-Mekan-Led-Ekran/sss.html",
    },
    {
        "label": "/rental-ekran/ SEO",
        "page_id": 6083,
        "widget_id": "2a70be1",
        "file": "Urunlerimiz/Rental-Ekran/rental-ekran-text.html",
    },
    {
        "label": "/rental-ekran/ FAQ",
        "page_id": 6083,
        "widget_id": "2bd89fe",
        "file": "Urunlerimiz/Rental-Ekran/sss.html",
    },
    {
        "label": "/dis-mekan-led-ekran/ FAQ",
        "page_id": 6012,
        "widget_id": "538c2a3",
        "file": "Urunlerimiz/Dis-Mekan-Led-Ekran/sss.html",
    },
]

SEO_INSERT_PAGES = [
    {
        "label": "/dis-mekan-led-ekran/ SEO insert",
        "page_id": 6012,
        "before_widget": "538c2a3",
        "marker": "control-cards-content-wrapper",
        "file": "Urunlerimiz/Dis-Mekan-Led-Ekran/dis-mekan-led-ekran-text.html",
        "known_widget_id": "7b76b791",
    },
]


def load_env() -> tuple[str, str, str]:
    path = ROOT / ".env"
    data: dict[str, str] = {}
    if path.is_file():
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


def read_html(rel: str) -> str:
    return content_path(rel).read_text(encoding="utf-8")


def deploy_widget(
    site: str,
    auth: tuple[str, str],
    page_id: int,
    widget_id: str,
    html: str,
    apply: bool,
) -> bool:
    if not apply:
        print(f"  [dry-run] page={page_id} widget={widget_id} ({len(html)} char)")
        return True
    for attempt in range(4):
        r = requests.post(
            f"{site}/wp-json/ledajans/v1/hero-widget",
            json={"page_id": page_id, "widget_id": widget_id, "html": html},
            auth=auth,
            timeout=120,
            headers={"User-Agent": "LEDAJANS-Elementor-Deploy/1.0"},
        )
        if r.status_code == 200:
            print(f"  OK widget {widget_id} ({r.json().get('bytes', len(html))} byte)")
            return True
        if r.status_code == 403:
            time.sleep(3 * (attempt + 1))
            continue
        print(f"  HATA HTTP {r.status_code}: {r.text[:300]}")
        return False
    print("  HATA: 403 — WAF/rate limit")
    return False


def walk_find(el: dict, target: str, path: list | None = None) -> list | None:
    path = path or []
    cur = path + [el]
    if el.get("id") == target:
        return cur
    for c in el.get("elements") or []:
        r = walk_find(c, target, cur)
        if r:
            return r
    return None


def ensure_seo_widget(site: str, auth: tuple[str, str], cfg: dict, apply: bool) -> str | None:
    """SEO metin widget yoksa FAQ'dan once ekle; widget id dondur."""
    html = read_html(cfg["file"])
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/{cfg['page_id']}?context=edit",
        auth=auth,
        timeout=60,
        headers={"User-Agent": "LEDAJANS-Elementor-Deploy/1.0"},
    )
    if r.status_code != 200:
        known = cfg.get("known_widget_id")
        if known:
            return known
        print(f"  HATA page fetch {r.status_code}")
        return None
    raw = r.json()["meta"]["_elementor_data"]
    if cfg["marker"] in raw:
        data = json.loads(raw)
        for top in data:
            stack = [top]
            while stack:
                el = stack.pop()
                if el.get("widgetType") == "html":
                    h = el.get("settings", {}).get("html", "")
                    if cfg["marker"] in h:
                        return el.get("id")
                stack.extend(el.get("elements") or [])
        return cfg.get("known_widget_id")

    if not apply:
        print(f"  [dry-run] SEO widget eklenecek (FAQ oncesi)")
        return "new-seo-widget"

    data = json.loads(raw)
    path = None
    for top in data:
        path = walk_find(top, cfg["before_widget"], [])
        if path:
            break
    if not path or len(path) < 2:
        print("  HATA: FAQ widget bulunamadi")
        return None
    parent = path[-2]
    target = path[-1]
    elements = parent.setdefault("elements", [])
    idx = elements.index(target)
    new_id = secrets.token_hex(4)
    elements.insert(
        idx,
        {
            "id": new_id,
            "elType": "widget",
            "widgetType": "html",
            "settings": {"html": html},
            "elements": [],
        },
    )
    payload = {"meta": {"_elementor_data": json.dumps(data, ensure_ascii=False)}}
    r2 = requests.post(
        f"{site}/wp-json/wp/v2/pages/{cfg['page_id']}",
        json=payload,
        auth=auth,
        timeout=120,
        headers={"User-Agent": "LEDAJANS-Elementor-Deploy/1.0"},
    )
    if r2.status_code != 200:
        print(f"  HATA insert {r2.status_code}: {r2.text[:200]}")
        return None
    print(f"  OK SEO widget eklendi id={new_id}")
    return new_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Yalnızca eşleşen label, widget id veya dosyayı deploy et (tekrarlanabilir)",
    )
    args = parser.parse_args()

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1

    auth = (user, pw)
    ok = 0
    selectors = [value.casefold() for value in args.only]

    def selected(config: dict) -> bool:
        if not selectors:
            return True
        haystack = " ".join(
            str(config.get(key, ""))
            for key in ("label", "widget_id", "known_widget_id", "file")
        ).casefold()
        return any(selector in haystack for selector in selectors)

    selected_inserts = [config for config in SEO_INSERT_PAGES if selected(config)]
    selected_widgets = [config for config in WIDGETS if selected(config)]
    total = len(selected_widgets) + len(selected_inserts)
    if total == 0:
        print("HATA: --only eslesmesi bulunamadi")
        return 1

    print(f"Elementor widget deploy — {'APPLY' if args.apply else 'DRY-RUN'}\n")

    for cfg in selected_inserts:
        print(f"\n>> {cfg['label']}")
        seo_id = ensure_seo_widget(site, auth, cfg, args.apply)
        if seo_id and seo_id not in ("new-seo-widget", None):
            html = read_html(cfg["file"])
            if deploy_widget(site, auth, cfg["page_id"], seo_id, html, args.apply):
                ok += 1
        elif seo_id == "new-seo-widget":
            ok += 1
        time.sleep(2)

    for item in selected_widgets:
        print(f"\n>> {item['label']}")
        html = read_html(item["file"])
        if deploy_widget(site, auth, item["page_id"], item["widget_id"], html, args.apply):
            ok += 1
        time.sleep(2)

    print(f"\nSonuc: {ok}/{total}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
