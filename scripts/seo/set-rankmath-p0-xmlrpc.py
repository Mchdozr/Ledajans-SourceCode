#!/usr/bin/env python3
"""XML-RPC ile RankMath post meta (REST kayitsiz sayfalar icin)."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import os
import sys
import xmlrpc.client


PAGES = [
    (
        5557,
        {
            "rank_math_title": "LED Ekran ve Fiyatları 2026 | İç-Dış Mekan - LEDAJANS",
            "rank_math_description": (
                "LED ekran, fiyatları ve m² hesaplama. İç mekan, dış mekan, rental modeller. "
                "25 yıl tecrübe, 2 yıl garanti. Ücretsiz keşif — Türkiye geneli teklif alın."
            ),
            "rank_math_focus_keyword": "led ekran,led ekran fiyatları,led ekran m2 fiyatı,led ekran firmaları",
        },
    ),
    (
        6012,
        {
            "rank_math_title": "Dış Mekan LED Ekran | Outdoor IP65 P4-P10 - LEDAJANS",
            "rank_math_description": (
                "Dış mekan ve açık hava LED ekran. IP65, yüksek parlaklık, reklam panosu ve cephe için. "
                "Outdoor LED çözümleri. Ücretsiz keşif ve teklif."
            ),
            "rank_math_focus_keyword": "dış mekan led ekran,outdoor led ekran,açık hava led ekran,ip65 led ekran",
        },
    ),
    (
        6083,
        {
            "rank_math_title": "LED Ekran Kiralama | Rental Ekran 2026 - LEDAJANS",
            "rank_math_description": (
                "LED ekran kiralama ve rental LED ekran. Konser, fuar, düğün için hızlı kurulum, "
                "teknik ekip, flight case. Kiralık LED ekran fiyat teklifi alın."
            ),
            "rank_math_focus_keyword": "led ekran kiralama,rental led ekran,kiralık led ekran,led ekran kiralama fiyatları",
        },
    ),
    (
        6004,
        {
            "rank_math_title": "İç Mekan LED Ekran | Indoor P2-P3 Fiyat - LEDAJANS",
            "rank_math_description": (
                "İç mekan ve indoor LED ekran. P2, P2.5, P3 modeller; mağaza, stüdyo, toplantı odası. "
                "3840Hz, 2 yıl garanti. Ücretsiz danışmanlık."
            ),
            "rank_math_focus_keyword": "iç mekan led ekran,indoor led ekran,p2 led ekran,p3 led ekran",
        },
    ),
]


def load_env() -> tuple[str, str, str]:
    path = ROOT / ".env"
    data: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip("\"'")
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    return site, data.get("WP_USERNAME", ""), data.get("WP_APP_PASSWORD", "").replace(" ", "")


def main() -> int:
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1

    endpoint = f"{site}/xmlrpc.php"
    wp = xmlrpc.client.ServerProxy(endpoint, allow_none=True)
    try:
        wp.system.listMethods()
    except Exception as e:
        print("XML-RPC kapali veya erisilemiyor:", e)
        return 1

    ok = 0
    for post_id, fields in PAGES:
        custom_fields = [{"key": k, "value": v} for k, v in fields.items()]
        try:
            # Mevcut icerigi koru; sadece custom_fields guncelle
            post = wp.wp.getPost(post_id, 1, user, pw)
            content = post.get("post_content") or ""
            title = post.get("post_title") or ""
            result = wp.wp.editPost(
                0,
                post_id,
                user,
                pw,
                {
                    "post_title": title,
                    "post_content": content,
                    "custom_fields": custom_fields,
                },
            )
            print(f"OK id={post_id} editPost={result}")
            ok += 1
        except xmlrpc.client.Fault as fault:
            print(f"HATA id={post_id}: {fault.faultString}")
        except Exception as e:
            print(f"HATA id={post_id}: {e}")

    print(f"\nTamam: {ok}/{len(PAGES)}")
    return 0 if ok == len(PAGES) else 1


if __name__ == "__main__":
    sys.exit(main())
