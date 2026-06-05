#!/usr/bin/env python3
"""GSC index adaylari icin RankMath meta guncelle."""
from __future__ import annotations

import argparse
import os
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    {
        "slug": "program-indir",
        "title": "LED Ekran Programları İndir | Kontrol Yazılımları - LEDAJANS",
        "description": (
            "LED ekran programları indir: Novastar, Huidu, kontrol kartı yazılımları ve "
            "uzaktan destek dosyaları. LEDAJANS teknik destek arşivi."
        ),
        "focus": "led ekran program indir,led ekran yazılımı,kontrol kartı programı",
    },
    {
        "slug": "dis-mekan-rgb-panel",
        "title": "Dış Mekan RGB LED Panel | IP65 Modül - LEDAJANS",
        "description": (
            "Dış mekan RGB LED panel ve IP65 modül çözümleri. Reklam panosu, tabela ve "
            "açık hava uygulamaları için üretici desteği ve teklif."
        ),
        "focus": "dış mekan rgb panel,rgb led panel,dış mekan led panel,ip65 led panel",
    },
]


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    with open(os.path.join(ROOT, ".env"), encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data.get("WP_USERNAME", ""),
        data.get("WP_APP_PASSWORD", "").replace(" ", ""),
    )


def find_page_id(site: str, slug: str, auth: tuple[str, str], headers: dict[str, str]) -> int | None:
    response = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": slug, "status": "publish,draft,private"},
        auth=auth,
        headers=headers,
        timeout=30,
    )
    if response.status_code != 200 or not response.json():
        return None
    return int(response.json()[0]["id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    site, user, password = load_env()
    if not user or not password:
        print("HATA: .env gerekli")
        return 1

    auth = (user, password)
    headers = {"User-Agent": "LEDAJANS-Index-Candidates/1.0", "Content-Type": "application/json"}
    ok = 0

    print("Index adaylari RankMath — " + ("APPLY" if args.apply else "DRY-RUN"))
    for target in TARGETS:
        print(f"\n>> /{target['slug']}/")
        page_id = find_page_id(site, target["slug"], auth, headers)
        if not page_id:
            print("  sayfa bulunamadi")
            continue
        print(f"  id={page_id}")
        if not args.apply:
            ok += 1
            continue
        meta = {
            "rank_math_title": target["title"],
            "rank_math_description": target["description"],
            "rank_math_focus_keyword": target["focus"],
        }
        response = requests.post(
            f"{site}/wp-json/wp/v2/pages/{page_id}",
            json={"meta": meta},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        body = response.json() if response.status_code in (200, 201) else {}
        if response.status_code in (200, 201) and (body.get("meta") or {}).get("rank_math_title"):
            print("  OK")
            ok += 1
        else:
            print(f"  HATA HTTP {response.status_code}: {response.text[:200]}")

    print(f"\nTamam: {ok}/{len(TARGETS)}")
    return 0 if ok == len(TARGETS) else 1


if __name__ == "__main__":
    sys.exit(main())
