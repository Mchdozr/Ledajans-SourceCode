#!/usr/bin/env python3
"""Ana sayfa ve COB RankMath description kisaltma."""
from __future__ import annotations

import argparse
import os
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    {
        "label": "Ana sayfa",
        "slug": None,
        "description": (
            "LED ekran satış, kiralama ve kurulum. İç mekan, dış mekan, rental çözümler. "
            "25 yıl tecrübe, 2 yıl garanti. Ücretsiz keşif ve teklif."
        ),
    },
    {
        "label": "COB",
        "slug": "cob-ekran",
        "description": (
            "COB LED ekran ve Smart Screen modelleri. Yüksek kontrast, dayanıklı yüzey, "
            "premium iç mekanlar için üretici desteği ve teklif."
        ),
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


def get_front_page_id(site: str, auth: tuple[str, str], headers: dict[str, str]) -> int | None:
    response = requests.get(f"{site}/wp-json/wp/v2/settings", auth=auth, headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"  Ayarlar okunamadı: HTTP {response.status_code}")
        return None
    page_id = response.json().get("page_on_front")
    return int(page_id) if page_id else None


def get_page_id(site: str, slug: str, auth: tuple[str, str], headers: dict[str, str]) -> int | None:
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
        print("HATA: .env içinde WP_USERNAME ve WP_APP_PASSWORD gerekli")
        return 1

    auth = (user, password)
    headers = {"User-Agent": "LEDAJANS-RankMath-Cleanup/1.0", "Content-Type": "application/json"}
    ok = 0

    print("RankMath meta cleanup — " + ("APPLY" if args.apply else "DRY-RUN"))
    for target in TARGETS:
        print(f"\n>> {target['label']}")
        page_id = (
            get_page_id(site, target["slug"], auth, headers)
            if target["slug"]
            else get_front_page_id(site, auth, headers)
        )
        if not page_id:
            print("  Sayfa ID bulunamadı")
            continue

        description = target["description"]
        print(f"  id={page_id} description_len={len(description)}")
        if not args.apply:
            ok += 1
            continue

        response = requests.post(
            f"{site}/wp-json/wp/v2/pages/{page_id}",
            json={"meta": {"rank_math_description": description}},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        body = response.json() if response.status_code in (200, 201) else {}
        saved = (body.get("meta") or {}).get("rank_math_description")
        if response.status_code in (200, 201) and saved == description:
            print("  OK")
            ok += 1
        else:
            print(f"  HATA HTTP {response.status_code}: {response.text[:200]}")

    print(f"\nTamam: {ok}/{len(TARGETS)}")
    return 0 if ok == len(TARGETS) else 1


if __name__ == "__main__":
    sys.exit(main())
