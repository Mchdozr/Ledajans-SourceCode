#!/usr/bin/env python3
"""Belirli SEO sayfalarini guncelle ve yayinla."""
from __future__ import annotations

import importlib.util
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_deploy_module():
    path = os.path.join(ROOT, "deploy-to-wordpress.py")
    spec = importlib.util.spec_from_file_location("deploy_wp", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TARGETS = [
    ("SEO-Icerik-Widgets/sehir-sayfalari/bursa-led-ekran.html", "bursa-led-ekran", "Bursa LED Ekran", "page"),
    ("SEO-Icerik-Widgets/sektor-rehberleri/seffaf-led-ekran.html", "seffaf-led-ekran", "Şeffaf LED Ekran (Cam LED)", "page"),
    ("SEO-Icerik-Widgets/kullanim-alanlari/sahne-led-ekran-kiralama.html", "sahne-led-ekran-kiralama", "Sahne LED Ekran Kiralama", "page"),
]


def main() -> int:
    os.chdir(ROOT)
    d = load_deploy_module()
    d.DRY_RUN = False
    ok = 0
    for file_path, slug, title, post_type in TARGETS:
        content = d.read_file(file_path)
        endpoint = f"{d.API_BASE}/{'posts' if post_type == 'post' else 'pages'}"
        existing = d.check_existing(slug, post_type)
        if not existing:
            print(f"HATA: /{slug}/ bulunamadi")
            continue
        payload = {
            "title": title,
            "content": content,
            "status": "publish",
            "meta": d.build_rankmath_meta(
                title,
                d.extract_meta_description(content),
                d.extract_focus_keyword(content),
            ),
        }
        r = d.session.post(f"{endpoint}/{existing['id']}", json=payload)
        if r.status_code in (200, 201):
            print(f"OK: /{slug}/ guncellendi ve yayinda (id={existing['id']})")
            ok += 1
        else:
            print(f"HATA /{slug}/ HTTP {r.status_code}: {r.text[:200]}")
        time.sleep(1)
    print(f"\nSonuc: {ok}/{len(TARGETS)}")
    return 0 if ok == len(TARGETS) else 1


if __name__ == "__main__":
    sys.exit(main())
