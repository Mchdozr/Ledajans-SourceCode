#!/usr/bin/env python3
"""Anasayfa Elementor içeriğini repo Anasayfa/*.html widget'larıyla değiştir."""
from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PAGE_ID = 1248
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
BACKUP = ROOT / "AGENT-HUB" / "BACKUPS" / "2026-09-11-home-1248-elementor.json"

HOME_WIDGETS: list[tuple[str, str]] = [
    ("Anasayfa/Hero.html", "ledajans-hero"),
    ("Anasayfa/widget-3.html", "ledajans-about"),
    ("Anasayfa/widget-4-Ic-Mekan.html", "ledajans-indoor"),
    ("Anasayfa/widget-5-Dis-Mekan.html", "ledajans-outdoor"),
    ("Anasayfa/widget-6-Urunlerimiz-Slider.html", "products-slider-section"),
    ("Anasayfa/widget-7-projeler.html", "ledajans-projects-page"),
    ("Anasayfa/widget-8-Yorumlar.html", "ledajans-reviews"),
    ("Anasayfa/widget-9-Blog.html", "ledajans-blog"),
    ("Anasayfa/homepage-schema.html", "application/ld+json"),
]


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


def eid() -> str:
    return secrets.token_hex(4)[:7]


def make_section(html: str) -> dict:
    return {
        "id": eid(),
        "elType": "section",
        "isInner": False,
        "settings": {"layout": "full_width", "gap": "no"},
        "elements": [
            {
                "id": eid(),
                "elType": "column",
                "isInner": False,
                "settings": {"_column_size": 100},
                "elements": [
                    {
                        "id": eid(),
                        "elType": "widget",
                        "widgetType": "html",
                        "settings": {"html": html},
                        "elements": [],
                    }
                ],
            }
        ],
    }


def load_home_html() -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for rel, marker in HOME_WIDGETS:
        path = ROOT / rel.replace("/", "\\")
        html = path.read_text(encoding="utf-8")
        if marker not in html:
            raise SystemExit(f"HATA: {rel} marker yok: {marker}")
        blocks.append((rel, html))

    certs = (ROOT / "Anasayfa" / "sertifikalar-anasayfa.html").read_text(encoding="utf-8")
    brands = (ROOT / "Anasayfa" / "Marka-logolar.html").read_text(encoding="utf-8")
    if "ledajans-home-certs" not in certs or "ledajans-brands" not in brands:
        raise SystemExit("HATA: certs/brands HTML gecersiz")
    combined = certs.rstrip() + "\n\n" + brands.lstrip()
    # certs+brands: Hero'dan hemen sonra, about'tan once
    insert_at = 1
    blocks.insert(insert_at, ("Anasayfa/sertifikalar+marka", combined))
    return blocks


def main() -> int:
    apply = "--apply" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    blocks = load_home_html()
    hero = blocks[0][1]
    if "<picture>" not in hero or "ldajsn2-mobile-q60" not in hero:
        print("HATA: Hero.html picture/q60 yok")
        return 1

    print("widgets", len(blocks))
    for rel, html in blocks:
        print(f"  {rel} bytes={len(html)}")

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=90,
    )
    print("page_get", rp.status_code)
    if rp.status_code != 200:
        print(rp.text[:300])
        return 1

    page = rp.json()
    raw = (page.get("meta") or {}).get("_elementor_data")
    old = json.loads(raw) if isinstance(raw, str) else raw
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        BACKUP.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
        print("backup_wrote", BACKUP.name)
    else:
        print("backup_exists", BACKUP.name)

    new_data = [make_section(html) for _, html in blocks]
    print("new_sections", len(new_data), "old_sections", len(old) if isinstance(old, list) else "?")

    if not apply:
        print("DRY_RUN: yazilmadi")
        return 0

    payload = {
        "meta": {
            "_elementor_data": json.dumps(new_data, ensure_ascii=False, separators=(",", ":")),
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
    print("page_update", ru.status_code, (ru.text or "")[:250].replace("\n", " "))
    if ru.status_code not in (200, 201):
        return 1

    rc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers=headers,
        timeout=60,
    )
    print("elementor_cache_del", rc.status_code)

    live = requests.get(
        site + "/",
        headers={"User-Agent": "Mozilla/5.0 (iPhone)", "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    checks = [
        "ledajans-hero",
        "ldajsn2-mobile-q60",
        "ledajans-about",
        "ledajans-indoor",
        "ledajans-outdoor",
        "products-slider-section",
        "ledajans-home-certs",
        "ledajans-brands",
        "ledajans-reviews",
        "ledajans-blog",
        "min(450px, 38vw)",
        "signistanbul-logo.webp",
        "fair-reveal-active",
        "fuar-kart-arkaplan.webp",
    ]
    ok = True
    for m in checks:
        hit = m in live
        print(f"live {m}={hit}")
        if not hit:
            ok = False
    certs_i = live.find("ledajans-home-certs")
    about_i = live.find("ledajans-about")
    fuar = "la-fuar-popup" in live
    poster = "ledajans-hero-poster" in live
    vh_band = "max(600px, 100vh)" in live or "max(600px, 100dvh)" in live
    print("certs_before_about", certs_i != -1 and about_i != -1 and certs_i < about_i, certs_i, about_i)
    print("fuar_gone", not fuar)
    print("poster_gone", not poster)
    print("no_100vh_min", not vh_band)
    if certs_i == -1 or about_i == -1 or certs_i > about_i or fuar or poster or vh_band:
        ok = False
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
