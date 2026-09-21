#!/usr/bin/env python3
"""led ekran SERP: site title + RankMath + WP sayfa basliklari."""
from __future__ import annotations

import argparse
import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE_TITLE = "LEDAJANS"
SITE_TAGLINE = "LED Ekran Satış, Kiralama ve Kurulum"

PAGES = [
    {
        "id": 1248,
        "slug": "(homepage)",
        "wp_title": "LED Ekran",
        "rank_title": "LED Ekran | Satış, Kiralama, Kurulum | LEDAJANS",
        "rank_desc": (
            "LED ekran satış, kiralama ve kurulum. İç-dış mekan, rental. "
            "25 yıl tecrübe, 2 yıl garanti. Ücretsiz keşif — LEDAJANS İstanbul."
        ),
        "focus": "led ekran,led ekran satış,led ekran kiralama,led ekran kurulum",
    },
    {
        "id": 5001,
        "slug": "led-ekran",
        "wp_title": "LED Ekran Fiyatları ve Modelleri",
        "rank_title": "LED Ekran Fiyatları ve Modelleri | İç-Dış Mekan | LEDAJANS",
        "rank_desc": (
            "LED ekran fiyatları, modelleri ve m² hesaplama. İç mekan, dış mekan, rental. "
            "25 yıl tecrübe, 2 yıl garanti. Ücretsiz keşif — Türkiye geneli teklif alın."
        ),
        "focus": "led ekran fiyatları,led ekran,led ekran modelleri,led ekran m2 fiyatı",
    },
    {
        "slug": "ic-mekan-led-ekran",
        "wp_title": "İç Mekan LED Ekran",
        "rank_title": "İç Mekan LED Ekran | Indoor P2-P3 Fiyat | LEDAJANS",
        "rank_desc": (
            "İç mekan LED ekran. P2, P2.5, P3 modeller; mağaza, stüdyo, toplantı odası. "
            "3840Hz, 2 yıl garanti. Ücretsiz danışmanlık."
        ),
        "focus": "iç mekan led ekran,indoor led ekran,p2 led ekran,p3 led ekran",
    },
    {
        "slug": "dis-mekan-led-ekran",
        "wp_title": "Dış Mekan LED Ekran",
        "rank_title": "Dış Mekan LED Ekran | Outdoor IP65 P4-P10 | LEDAJANS",
        "rank_desc": (
            "Dış mekan LED ekran. IP65, yüksek parlaklık, reklam panosu ve cephe. "
            "Outdoor LED çözümleri. Ücretsiz keşif ve teklif."
        ),
        "focus": "dış mekan led ekran,outdoor led ekran,açık hava led ekran,ip65 led ekran",
    },
    {
        "slug": "rental-ekran",
        "wp_title": "LED Ekran Kiralama",
        "rank_title": "LED Ekran Kiralama | Rental Ekran 2026 | LEDAJANS",
        "rank_desc": (
            "LED ekran kiralama ve rental LED ekran. Konser, fuar, düğün için hızlı kurulum, "
            "teknik ekip, flight case. Kiralık LED ekran fiyat teklifi alın."
        ),
        "focus": "led ekran kiralama,rental led ekran,kiralık led ekran,led ekran kiralama fiyatları",
    },
]


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


def find_page_id(site: str, slug: str, auth: tuple[str, str], headers: dict) -> int | None:
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": slug, "status": "publish,draft,private"},
        auth=auth,
        headers=headers,
        timeout=30,
    )
    if r.status_code != 200 or not r.json():
        return None
    return int(r.json()[0]["id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry = not args.apply

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env içinde WP_USERNAME ve WP_APP_PASSWORD gerekli")
        return 1

    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-SERP-Meta/1.0", "Content-Type": "application/json"}
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"{mode} — {site}\n")

    print(">> site title")
    print(f"  title={SITE_TITLE}")
    print(f"  tagline={SITE_TAGLINE}")
    if not dry:
        rs = requests.post(
            f"{site}/wp-json/wp/v2/settings",
            json={"title": SITE_TITLE, "description": SITE_TAGLINE},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        print(f"  settings HTTP {rs.status_code}")
        if rs.status_code not in (200, 201):
            print(f"  UYARI: {rs.text[:240]}")

    ok = 0
    for page in PAGES:
        slug = page["slug"]
        pid = page.get("id")
        if not pid:
            pid = find_page_id(site, slug, auth, headers)
        print(f">> {slug} id={pid}")
        if not pid:
            print("  ATLANDI: sayfa yok")
            continue
        payload = {
            "title": page["wp_title"],
            "meta": {
                "rank_math_title": page["rank_title"],
                "rank_math_description": page["rank_desc"],
                "rank_math_focus_keyword": page["focus"],
            },
        }
        print(f"  wp_title={page['wp_title']}")
        print(f"  rank_title={page['rank_title']}")
        if dry:
            ok += 1
            continue
        r = requests.post(
            f"{site}/wp-json/wp/v2/pages/{pid}",
            json=payload,
            auth=auth,
            headers=headers,
            timeout=45,
        )
        print(f"  HTTP {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"  HATA: {r.text[:300]}")
            continue
        ok += 1

    print(f"\nTamam: {ok}/{len(PAGES)}")
    return 0 if ok == len(PAGES) else 1


if __name__ == "__main__":
    sys.exit(main())
