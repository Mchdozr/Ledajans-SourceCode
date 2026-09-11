#!/usr/bin/env python3
"""Kurumsal / teknik / kalan blog sayfalarını repo HTML ile canlıya yazar."""
from __future__ import annotations

import json
import os
import re
import secrets
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
BACKUP_DIR = ROOT / "AGENT-HUB" / "BACKUPS"

# slug, title, files, marker, existing_page_id (0=create)
PAGES: list[tuple[str, str, list[str], str, int]] = [
    (
        "sertifikalarimiz",
        "Sertifikalarımız",
        ["Kurumsal/Sertifikalarimiz/sertifikalarimiz.html"],
        "ledajans-cert-page",
        0,
    ),
    (
        "markalarimiz",
        "Markalarımız",
        ["Anasayfa/Marka-logolar.html"],
        "ledajans-brands",
        0,
    ),
    (
        "hakkimizda",
        "Hakkımızda",
        [
            "Kurumsal/Hakkimizda/hero-banner.html",
            "Kurumsal/Hakkimizda/hakkimizda.html",
            "Kurumsal/Hakkimizda/satis-kanallarimiz.html",
        ],
        "ledajans-about-who",
        1242,
    ),
    (
        "firma-bilgilerimiz",
        "Firma Bilgilerimiz",
        [
            "Kurumsal/Firma-Bilgilerimiz/hero-banner-firma-bilgileri.html",
            "Kurumsal/Firma-Bilgilerimiz/firma-bilgilerimiz.html",
        ],
        "ledajans-company",
        1238,
    ),
    (
        "iletisim",
        "İletişim",
        [
            "İletisim/hero-banner.html",
            "İletisim/body.html",
        ],
        "ledajans-iletisim-hero",
        1262,
    ),
    (
        "program-indir",
        "Program İndir",
        [
            "Teknik-Destek-Bilgi/Program-indir/hero-banner.html",
            "Teknik-Destek-Bilgi/Program-indir/indirme-dosyalari.html",
            "Teknik-Destek-Bilgi/Program-indir/uzak-masaustu.html",
            "Teknik-Destek-Bilgi/Program-indir/satis-kanallari.html",
        ],
        "program-downloads-section",
        786,
    ),
    (
        "colorlight",
        "Colorlight",
        [
            "Teknik-Destek-Bilgi/Colorlight/hero-banner.html",
            "Teknik-Destek-Bilgi/Colorlight/slider.html",
            "Teknik-Destek-Bilgi/Colorlight/colorlight.html",
        ],
        "la-pmtr-page",
        4081,
    ),
    (
        "huidu",
        "HUIDU",
        [
            "Teknik-Destek-Bilgi/Huidu/hero-banner-body.html",
            "Teknik-Destek-Bilgi/Huidu/tablo-hd.html",
        ],
        "ledajans-huidu-hero",
        4214,
    ),
    (
        "huidu-processor-hdplayer-indir",
        "Huidu Processor HDPlayer İndir",
        [
            "Teknik-Destek-Bilgi/Huidu/hero-banner-body.html",
            "Teknik-Destek-Bilgi/Huidu/tablo-hd.html",
        ],
        "ledajans-huidu-hero",
        0,
    ),
    (
        "teknik-destek-videolari",
        "Teknik Destek Videoları",
        [
            "Teknik-Destek-Bilgi/Teknik-Destek-Videolari/hero-banner.html",
            "Teknik-Destek-Bilgi/Teknik-Destek-Videolari/body.html",
        ],
        "ld-td-wrap",
        195,
    ),
    (
        "teknik-destek-videolari-2",
        "Teknik Destek Videoları",
        [
            "Teknik-Destek-Bilgi/Teknik-Destek-Videolari/hero-banner.html",
            "Teknik-Destek-Bilgi/Teknik-Destek-Videolari/body.html",
        ],
        "ld-td-wrap",
        848,
    ),
    (
        "projeler",
        "LED Ekran Projeleri",
        [
            "Anasayfa/widget-projeler-hero.html",
            "Anasayfa/widget-7-projeler.html",
        ],
        "ledajans-projects-hero",
        4956,
    ),
]

POSTS: list[tuple[str, str, str, str]] = [
    (
        "Blog/cob-led-ekran-nedir-avantajlari.html",
        "cob-led-ekran-nedir-avantajlari",
        "COB LED Ekran Nedir? Avantajları ve Ne Zaman Tercih Edilmeli",
        "ledajans-seo-article",
    ),
    (
        "Blog/huidu-wf1-wf2-wf4-led-kontrol-karti.html",
        "huidu-wf1-wf2-wf4-led-kontrol-karti",
        "Huidu LED Kontrol Kartı: WF1, WF2 ve WF4 Karşılaştırma Rehberi",
        "ledajans-seo-article",
    ),
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


def meta_of(html: str) -> tuple[str, str]:
    desc = re.search(r"<!-- SEO Meta Description:\s*(.+?)\s*-->", html)
    kw = re.search(r"<!-- SEO Focus Keyword:\s*(.+?)\s*-->", html)
    return (desc.group(1).strip() if desc else "", kw.group(1).strip() if kw else "")


def read_files(files: list[str]) -> list[str]:
    out = []
    for rel in files:
        path = ROOT / rel.replace("/", os.sep)
        if not path.is_file():
            raise FileNotFoundError(rel)
        out.append(path.read_text(encoding="utf-8"))
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")), None)
    if only:
        pages = [p for p in PAGES if p[0] == only]
        posts = [p for p in POSTS if p[1] == only]
        if not pages and not posts:
            print("HATA: unknown slug", only)
            return 1
    else:
        pages, posts = PAGES, POSTS
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    fail = 0

    for slug, title, files, marker, page_id in pages:
        blocks = read_files(files)
        blob = "".join(blocks)
        print(f"\n== /{slug}/ files={len(files)} bytes={len(blob)} id={page_id or 'NEW'}")
        if marker not in blob:
            print("  WARN marker yok", marker)
        if not apply:
            continue

        elem = [make_section(html) for html in blocks]
        payload = {
            "title": title,
            "slug": slug,
            "status": "publish",
            "parent": 0,
            "content": "\n".join(blocks),
            "meta": {
                "_elementor_data": json.dumps(elem, ensure_ascii=False, separators=(",", ":")),
                "_elementor_edit_mode": "builder",
            },
        }
        if page_id:
            rp = requests.get(
                f"{site}/wp-json/wp/v2/pages/{page_id}",
                params={"context": "edit"},
                auth=auth,
                headers={"User-Agent": UA},
                timeout=90,
            )
            if rp.status_code == 200:
                raw = (rp.json().get("meta") or {}).get("_elementor_data")
                if raw:
                    bp = BACKUP_DIR / f"2026-09-11-{slug}-{page_id}-elementor.json"
                    if not bp.exists():
                        parsed = json.loads(raw) if isinstance(raw, str) else raw
                        bp.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
                        print("  backup", bp.name)
            url = f"{site}/wp-json/wp/v2/pages/{page_id}"
        else:
            ex = requests.get(
                f"{site}/wp-json/wp/v2/pages",
                params={"slug": slug, "status": "any"},
                auth=auth,
                headers=headers,
                timeout=30,
            )
            if ex.status_code == 200 and ex.json():
                url = f"{site}/wp-json/wp/v2/pages/{ex.json()[0]['id']}"
            else:
                url = f"{site}/wp-json/wp/v2/pages"
        ru = requests.post(url, json=payload, auth=auth, headers=headers, timeout=180)
        if ru.status_code not in (200, 201):
            print("  HATA", ru.status_code, (ru.text or "")[:200].replace("\n", " "))
            fail += 1
        else:
            print("  OK", ru.json().get("id"), ru.json().get("link"))
        time.sleep(0.25)

    for rel, slug, title, marker in posts:
        path = ROOT / rel.replace("/", os.sep)
        html = path.read_text(encoding="utf-8")
        print(f"\n== POST /{slug}/ bytes={len(html)}")
        if not apply:
            continue
        desc, focus = meta_of(html)
        payload = {"title": title, "slug": slug, "content": html, "status": "publish"}
        if desc:
            payload["excerpt"] = desc
            payload["meta"] = {"rank_math_description": desc, "rank_math_title": title}
            if focus:
                payload["meta"]["rank_math_focus_keyword"] = focus
        ex = requests.get(
            f"{site}/wp-json/wp/v2/posts",
            params={"slug": slug, "status": "any"},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        url = (
            f"{site}/wp-json/wp/v2/posts/{ex.json()[0]['id']}"
            if ex.status_code == 200 and ex.json()
            else f"{site}/wp-json/wp/v2/posts"
        )
        ru = requests.post(url, json=payload, auth=auth, headers=headers, timeout=180)
        if ru.status_code not in (200, 201):
            print("  HATA", ru.status_code, (ru.text or "")[:200].replace("\n", " "))
            fail += 1
        else:
            print("  OK", ru.json().get("id"), ru.json().get("link"))
        time.sleep(0.25)

    if not apply:
        print("\nDRY_RUN")
        return 0

    rc = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("\nelementor_cache_del", rc.status_code)

    print("\n=== LIVE ===")
    ok = True
    checks = [(s, m) for s, _t, _f, m, _i in pages] + [(s, m) for _r, s, _t, m in posts]
    for slug, marker in checks:
        r = requests.get(
            f"{site}/{slug}/",
            headers={"User-Agent": UA, "Cache-Control": "no-cache"},
            timeout=40,
            allow_redirects=True,
        )
        hit = marker in r.text
        stay = f"/{slug}" in r.url
        print(f"  {r.status_code} {r.url.replace(site,'')} stay={stay} marker={hit}")
        if r.status_code != 200 or not stay or not hit:
            ok = False
            fail += 1
    return 0 if ok and fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
