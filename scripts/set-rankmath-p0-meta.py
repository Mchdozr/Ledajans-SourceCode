#!/usr/bin/env python3
"""P0 para sayfalarına RankMath title/description/focus keyword yazar."""
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

# Anasayfa: marka + kapsam odaklı (hub /led-ekran/ ile "led ekran" head-term
# yamyamlığını azaltmak için farklı niyet: "led ekran üreticisi/firmaları" + marka).
HOMEPAGE = {
    "title": "LED Ekran - RGB Panel - LED Görüntü Sistemleri",
    "description": (
        "LED ekran satış, kiralama ve kurulum. İç mekan, dış mekan, rental ve COB "
        "çözümler. 25 yıl tecrübe, 2 yıl garanti. Ücretsiz keşif ve teklif alın."
    ),
    "focus": "led ekran üreticisi,led ekran firmaları,ledajans,led ekran",
}

P0_PAGES = [
    {
        "slug": "led-ekran",
        "title": "LED Ekran ve Fiyatları 2026 | İç-Dış Mekan - LEDAJANS",
        "description": (
            "LED ekran, fiyatları ve m² hesaplama. İç mekan, dış mekan, rental modeller. "
            "25 yıl tecrübe, 2 yıl garanti. Ücretsiz keşif — Türkiye geneli teklif alın."
        ),
        "focus": "led ekran,led ekran fiyatları,led ekran m2 fiyatı,led ekran firmaları",
    },
    {
        "slug": "dis-mekan-led-ekran",
        "title": "Dış Mekan LED Ekran | Outdoor IP65 P4-P10 - LEDAJANS",
        "description": (
            "Dış mekan ve açık hava LED ekran. IP65, yüksek parlaklık, reklam panosu ve cephe için. "
            "Outdoor LED çözümleri. Ücretsiz keşif ve teklif."
        ),
        "focus": "dış mekan led ekran,outdoor led ekran,açık hava led ekran,ip65 led ekran",
    },
    {
        "slug": "rental-ekran",
        "title": "LED Ekran Kiralama | Rental Ekran 2026 - LEDAJANS",
        "description": (
            "LED ekran kiralama ve rental LED ekran. Konser, fuar, düğün için hızlı kurulum, "
            "teknik ekip, flight case. Kiralık LED ekran fiyat teklifi alın."
        ),
        "focus": "led ekran kiralama,rental led ekran,kiralık led ekran,led ekran kiralama fiyatları",
    },
    {
        "slug": "ic-mekan-led-ekran",
        "title": "İç Mekan LED Ekran | Indoor P2-P3 Fiyat - LEDAJANS",
        "description": (
            "İç mekan ve indoor LED ekran. P2, P2.5, P3 modeller; mağaza, stüdyo, toplantı odası. "
            "3840Hz, 2 yıl garanti. Ücretsiz danışmanlık."
        ),
        "focus": "iç mekan led ekran,indoor led ekran,p2 led ekran,p3 led ekran",
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
                v = v.strip().strip("\"'")
                data[k.strip()] = v
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    user = data.get("WP_USERNAME", "")
    pw = data.get("WP_APP_PASSWORD", "").replace(" ", "")
    return site, user, pw


def find_homepage_id(site: str, auth: tuple[str, str], headers: dict) -> int | None:
    """Statik anasayfa (page_on_front) id'sini WP settings'ten çözer."""
    try:
        r = requests.get(
            f"{site}/wp-json/wp/v2/settings",
            auth=auth,
            headers=headers,
            timeout=30,
        )
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("show_on_front") == "page" and data.get("page_on_front"):
        return int(data["page_on_front"])
    return None


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


def apply_meta(
    site: str,
    page_id: int,
    meta: dict[str, str],
    auth: tuple[str, str],
    headers: dict,
    dry_run: bool,
) -> bool:
    payload = {"meta": meta}
    if dry_run:
        print(f"  [dry-run] post_id={page_id} meta keys={list(meta.keys())}")
        return True
    r = requests.post(
        f"{site}/wp-json/wp/v2/pages/{page_id}",
        json=payload,
        auth=auth,
        headers=headers,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print(f"  HATA HTTP {r.status_code}: {r.text[:300]}")
        return False
    body = r.json()
    saved = (body.get("meta") or {}).get("rank_math_title")
    if not saved:
        print("  UYARI: REST yaniti rank_math_title icermiyor (mu-plugin gerekli olabilir)")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", help="Gerçek yazım")
    parser.add_argument("--no-homepage", action="store_true", help="Anasayfa metasını atla")
    args = parser.parse_args()
    dry_run = not args.apply

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env içinde WP_USERNAME ve WP_APP_PASSWORD gerekli")
        return 1

    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-RankMath-P0/1.0", "Content-Type": "application/json"}

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"RankMath P0 meta — {mode} — {site}\n")

    ok = 0
    total = len(P0_PAGES)

    if not args.no_homepage:
        total += 1
        print(">> / (anasayfa)")
        hp_id = find_homepage_id(site, auth, headers)
        if not hp_id:
            print("  ATLANDI: statik anasayfa id bulunamadı (show_on_front != page?)")
        else:
            hp_meta = {
                "rank_math_title": HOMEPAGE["title"],
                "rank_math_description": HOMEPAGE["description"],
                "rank_math_focus_keyword": HOMEPAGE["focus"],
            }
            if apply_meta(site, hp_id, hp_meta, auth, headers, dry_run):
                print(f"  OK id={hp_id} title={len(HOMEPAGE['title'])} desc={len(HOMEPAGE['description'])}")
                ok += 1

    for page in P0_PAGES:
        slug = page["slug"]
        print(f">> /{slug}/")
        pid = find_page_id(site, slug, auth, headers)
        if not pid:
            print(f"  ATLANDI: sayfa bulunamadı (slug={slug})")
            continue
        meta = {
            "rank_math_title": page["title"],
            "rank_math_description": page["description"],
            "rank_math_focus_keyword": page["focus"],
        }
        if apply_meta(site, pid, meta, auth, headers, dry_run):
            print(f"  OK id={pid} title={len(page['title'])} desc={len(page['description'])}")
            ok += 1

    print(f"\nTamam: {ok}/{total}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
