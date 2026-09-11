#!/usr/bin/env python3
"""P1 SEO sayfalarina RankMath meta yazar."""
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

P1_PAGES = [
    {
        "slug": "magaza-vitrin-led-ekran",
        "title": "Vitrin LED Ekran | Mağaza ve Şeffaf Cam - LEDAJANS",
        "description": (
            "Vitrin LED ekran ve mağaza vitrin çözümleri. Şeffaf cam LED, ince pitch, "
            "göz hizası mesafe. İç mekan vitrin için ücretsiz keşif ve teklif."
        ),
        "focus": "vitrin led ekran,mağaza vitrin led ekran,şeffaf led ekran,mağaza led ekran",
    },
    {
        "slug": "istanbul-led-ekran",
        "title": "İstanbul LED Ekran | Kurulum ve Fiyat 2026 - LEDAJANS",
        "description": (
            "İstanbul LED ekran satış, kurulum ve kiralama. AVM, cephe, metro, etkinlik. "
            "Ücretsiz keşif, 2 yıl garanti. LEDAJANS İstanbul."
        ),
        "focus": "istanbul led ekran,led ekran istanbul,istanbul led ekran fiyat,istanbul led ekran kiralama",
    },
    {
        "slug": "gob-led-ekran",
        "title": "GOB LED Ekran | Glue on Board Dayanıklı - LEDAJANS",
        "description": (
            "GOB LED ekran (Glue on Board). Okul, spor salonu, alçak montaj. "
            "Darbe ve neme dayanıklı. Teklif: 0212 220 40 04."
        ),
        "focus": "gob led ekran,gob led,glue on board,gob led panel",
    },
    {
        "slug": "gob-led-nedir",
        "title": "GOB LED Nedir? Glue on Board Teknolojisi - LEDAJANS",
        "description": (
            "GOB LED nedir: SMD üzerine epoksi dökülerek darbe, nem ve toza karşı koruma. "
            "GOB LED ekran kullanım alanları. LEDAJANS teknik sözlük."
        ),
        "focus": "gob led nedir,gob led,glue on board",
    },
    {
        "slug": "gob-vs-cob-smd",
        "title": "GOB vs COB vs SMD LED Ekran Karşılaştırma - LEDAJANS",
        "description": (
            "GOB, COB ve SMD farkı. GOB LED ekran ne zaman, COB ne zaman. "
            "Temas riski ve pitch seçimi. LEDAJANS karşılaştırma."
        ),
        "focus": "gob vs cob,gob led ekran,cob vs smd",
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

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1

    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-RankMath-P1/1.0", "Content-Type": "application/json"}
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"RankMath P1 — {mode}\n")

    ok = 0
    for page in P1_PAGES:
        slug = page["slug"]
        print(f">> /{slug}/")
        pid = find_page_id(site, slug, auth, headers)
        if not pid:
            print("  ATLANDI: sayfa yok")
            continue
        meta = {
            "rank_math_title": page["title"],
            "rank_math_description": page["description"],
            "rank_math_focus_keyword": page["focus"],
        }
        if not args.apply:
            print(f"  [dry-run] id={pid}")
            ok += 1
            continue
        r = requests.post(
            f"{site}/wp-json/wp/v2/pages/{pid}",
            json={"meta": meta},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        body = r.json() if r.status_code in (200, 201) else {}
        saved = (body.get("meta") or {}).get("rank_math_title")
        if r.status_code in (200, 201) and saved:
            print(f"  OK id={pid}")
            ok += 1
        else:
            print(f"  HATA HTTP {r.status_code}")

    print(f"\nTamam: {ok}/{len(P1_PAGES)}")
    return 0 if ok == len(P1_PAGES) else 1


if __name__ == "__main__":
    sys.exit(main())
