#!/usr/bin/env python3
"""Ürünlerimiz sayfalarını repo HTML widget'larıyla canlıya yazar."""
from __future__ import annotations

import json
import os
import secrets
import sys
import time
import xmlrpc.client
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
BACKUP_DIR = ROOT / "AGENT-HUB" / "BACKUPS"

# slug, title, files (repo relative), verify marker, existing page_id or 0, xmlrpc steal ids
PRODUCTS: list[tuple[str, str, list[str], str, int, list[int]]] = [
    (
        "ic-mekan-led-ekran",
        "İç Mekan LED Ekran",
        [
            "Urunlerimiz/Ic-Mekan-Led-Ekran/hero-banner.html",
            "Urunlerimiz/Ic-Mekan-Led-Ekran/sol-menu-urunlerimiz.html",
            "Urunlerimiz/Ic-Mekan-Led-Ekran/slider.html",
            "Urunlerimiz/Ic-Mekan-Led-Ekran/ic-mekan-led-ekran-text.html",
            "Urunlerimiz/Ic-Mekan-Led-Ekran/urun-ozellikleri.html",
            "Urunlerimiz/Ic-Mekan-Led-Ekran/sss.html",
        ],
        "ledajans-blog-hero",
        0,
        [1168],
    ),
    (
        "dis-mekan-led-ekran",
        "Dış Mekan LED Ekran",
        [
            "Urunlerimiz/Dis-Mekan-Led-Ekran/hero-banner.html",
            "Urunlerimiz/Dis-Mekan-Led-Ekran/sol-menu-urunlerimiz.html",
            "Urunlerimiz/Dis-Mekan-Led-Ekran/slider.html",
            "Urunlerimiz/Dis-Mekan-Led-Ekran/dis-mekan-led-ekran-text.html",
            "Urunlerimiz/Dis-Mekan-Led-Ekran/urun-ozellikleri.html",
            "Urunlerimiz/Dis-Mekan-Led-Ekran/ofc-serisi-outdoor.html",
            "Urunlerimiz/Dis-Mekan-Led-Ekran/tayor-serisi.html",
            "Urunlerimiz/Dis-Mekan-Led-Ekran/sss.html",
        ],
        "la-ofc-hub",
        0,
        [75],
    ),
    (
        "rental-ekran",
        "Rental LED Ekran",
        [
            "Urunlerimiz/Rental-Ekran/hero-banner.html",
            "Urunlerimiz/Rental-Ekran/sol-menu-urunlerimiz.html",
            "Urunlerimiz/Rental-Ekran/slider.html",
            "Urunlerimiz/Rental-Ekran/rental-ekran-text.html",
            "Urunlerimiz/Rental-Ekran/urun-ozellikleri.html",
            "Urunlerimiz/Rental-Ekran/grand-air-serisi-indoor.html",
            "Urunlerimiz/Rental-Ekran/grand-air-serisi-outdoor.html",
            "Urunlerimiz/Rental-Ekran/tablo-indoor-rental-led-ekranlar.html",
            "Urunlerimiz/Rental-Ekran/tablo-outdoor-rental-led-ekranlar.html",
            "Urunlerimiz/Rental-Ekran/sss.html",
        ],
        "ledajans-blog-hero",
        0,
        [1198],
    ),
    (
        "cob-ekran",
        "COB – Smart Screen",
        [
            "Urunlerimiz/Cob-Smart-Screen/hero-banner-cob-ss.html",
            "Urunlerimiz/Cob-Smart-Screen/sol-menu-urunlerimiz.html",
            "Urunlerimiz/Cob-Smart-Screen/product-slider.html",
            "Urunlerimiz/Cob-Smart-Screen/cob-ve-smart-screen-led-ekran-modelleri.html",
            "Urunlerimiz/Cob-Smart-Screen/smart-screen.html",
            "Urunlerimiz/Cob-Smart-Screen/cob-kartlar.html",
            "Urunlerimiz/Cob-Smart-Screen/p1-56-cob-led-ekran-seo.html",
            "Urunlerimiz/Cob-Smart-Screen/sss.html",
        ],
        "ledajans-blog-hero",
        3958,
        [],
    ),
    (
        "ic-mekan-rgb-panel",
        "İç Mekan RGB Panel",
        [
            "Urunlerimiz/Ic-Mekan-RGB-Panel/hero-banner.html",
            "Urunlerimiz/Ic-Mekan-RGB-Panel/sol-menu-urunlerimiz.html",
            "Urunlerimiz/Ic-Mekan-RGB-Panel/slider.html",
            "Urunlerimiz/Ic-Mekan-RGB-Panel/ic-mekan-icin-rgb-panel-text.html",
            "Urunlerimiz/Ic-Mekan-RGB-Panel/urun-ozellikleri.html",
            "Urunlerimiz/Ic-Mekan-RGB-Panel/tablo-ic-mekan-rgb-led-paneller.html",
            "Urunlerimiz/Ic-Mekan-RGB-Panel/tablo-ic-mekan-rgb-gob-led-paneller.html",
            "Urunlerimiz/Ic-Mekan-RGB-Panel/tablo-ic-mekan-flexible-led-paneller.html",
            "Urunlerimiz/Ic-Mekan-RGB-Panel/sss.html",
        ],
        "indoor-content-wrapper",
        0,
        [1218],
    ),
    (
        "dis-mekan-rgb-panel",
        "Dış Mekan RGB Panel",
        [
            "Urunlerimiz/Dis-Mekan-RGB-Panel/hero-banner.html",
            "Urunlerimiz/Dis-Mekan-RGB-Panel/sol-menu-urunlerimiz.html",
            "Urunlerimiz/Dis-Mekan-RGB-Panel/slider.html",
            "Urunlerimiz/Dis-Mekan-RGB-Panel/outdoor-rgb-text.html",
            "Urunlerimiz/Dis-Mekan-RGB-Panel/urun-ozellikleri.html",
            "Urunlerimiz/Dis-Mekan-RGB-Panel/tablo-outdoor-rgb-led-paneller.html",
            "Urunlerimiz/Dis-Mekan-RGB-Panel/sss.html",
        ],
        "ledajans-blog-hero",
        3795,
        [],
    ),
    (
        "kontrol-kartlari",
        "Kontrol Kartları",
        [
            "Urunlerimiz/Kontrol-Kartlari/hero-banner.html",
            "Urunlerimiz/Kontrol-Kartlari/sol-menu-urunlerimiz.html",
            "Urunlerimiz/Kontrol-Kartlari/slider.html",
            "Urunlerimiz/Kontrol-Kartlari/kontrol-kartlari-text.html",
            "Urunlerimiz/Kontrol-Kartlari/urun-ozellikleri.html",
            "Urunlerimiz/Kontrol-Kartlari/tablo-nova-kk.html",
            "Urunlerimiz/Kontrol-Kartlari/tablo-huidu-serisi-kk.html",
            "Urunlerimiz/Kontrol-Kartlari/tablo-colorlight-serisi-kk.html",
            "Urunlerimiz/Kontrol-Kartlari/sss.html",
        ],
        "ledajans-blog-hero",
        0,
        [1182],
    ),
    (
        "guc-kaynaklari",
        "Güç Kaynakları",
        [
            "Urunlerimiz/Guc-Kaynaklari/hero-banner.html",
            "Urunlerimiz/Guc-Kaynaklari/sol-menu-urunlerimiz.html",
            "Urunlerimiz/Guc-Kaynaklari/slider.html",
            "Urunlerimiz/Guc-Kaynaklari/guc-kaynaklari-text.html",
            "Urunlerimiz/Guc-Kaynaklari/tablo-guc-kaynaklari.html",
            "Urunlerimiz/Guc-Kaynaklari/sss.html",
        ],
        "ledajans-blog-hero",
        0,
        [],
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


def load_blocks(files: list[str]) -> list[str]:
    out: list[str] = []
    for rel in files:
        path = ROOT / rel.replace("/", os.sep)
        if not path.is_file():
            raise FileNotFoundError(rel)
        out.append(path.read_text(encoding="utf-8"))
    return out


def rename_cpt(site: str, user: str, pw: str, post_id: int, new_slug: str) -> None:
    wp = xmlrpc.client.ServerProxy(f"{site}/xmlrpc.php", allow_none=True)
    old = wp.wp.getPost(0, user, pw, post_id)
    print(f"  cpt {post_id} {old.get('post_type')} slug={old.get('post_name')} -> {new_slug}")
    wp.wp.editPost(0, user, pw, post_id, {"post_name": new_slug})


def main() -> int:
    apply = "--apply" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    fail = 0
    for slug, title, files, marker, page_id, steal_ids in PRODUCTS:
        blocks = load_blocks(files)
        print(f"\n== /{slug}/ files={len(files)} bytes={sum(len(b) for b in blocks)} page_id={page_id or 'NEW'}")
        if marker not in "".join(blocks):
            print("  WARN marker missing in concat:", marker)
        if not apply:
            continue

        for sid in steal_ids:
            try:
                rename_cpt(site, user, pw, sid, f"{slug}-gva-eski")
            except Exception as exc:
                print("  steal_err", sid, type(exc).__name__, str(exc)[:160])

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
            existing = requests.get(
                f"{site}/wp-json/wp/v2/pages",
                params={"slug": slug, "status": "any"},
                auth=auth,
                headers=headers,
                timeout=30,
            )
            if existing.status_code == 200 and existing.json():
                url = f"{site}/wp-json/wp/v2/pages/{existing.json()[0]['id']}"
            else:
                url = f"{site}/wp-json/wp/v2/pages"

        ru = requests.post(url, json=payload, auth=auth, headers=headers, timeout=180)
        if ru.status_code not in (200, 201):
            print("  HATA", ru.status_code, (ru.text or "")[:220].replace("\n", " "))
            fail += 1
            continue
        got = ru.json()
        print("  OK id", got.get("id"), got.get("link"))
        time.sleep(0.3)

    if not apply:
        print("\nDRY_RUN: yazilmadi")
        return 0

    rc = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("\nelementor_cache_del", rc.status_code)

    print("\n=== LIVE ===")
    ok = True
    for slug, _title, _files, marker, _pid, _steal in PRODUCTS:
        r = requests.get(
            f"{site}/{slug}/",
            headers={"User-Agent": UA, "Cache-Control": "no-cache"},
            timeout=40,
            allow_redirects=True,
        )
        hit = marker in r.text
        print(f"  {r.status_code} {r.url.replace(site,'')} marker={hit}")
        if r.status_code != 200 or f"/{slug}" not in r.url or not hit:
            ok = False
            fail += 1
    return 0 if ok and fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
