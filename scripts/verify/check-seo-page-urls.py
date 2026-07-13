#!/usr/bin/env python3
"""deploy-to-wordpress slug'larinin kok URL durumunu kontrol eder."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import sys
import time

import requests

SLUGS = [
    "led-ekran-nedir",
    "led-tabela",
    "led-ekran-kurulum",
    "led-ekran-bakim",
    "avm-led-ekran-rehberi",
    "stadyum-led-ekran",
    "magaza-vitrin-led-ekran",
    "belediye-bilgi-ekrani",
    "eczane-led-tabela",
    "cami-led-ekran",
    "p2-vs-p3-led-ekran",
    "ic-mekan-dis-mekan-led-farki",
    "cob-led-ne-zaman",
    "led-ekran-lcd-farki",
    "led-ekran-projeksiyon",
    "pitch-led-nedir",
    "refresh-hz-nedir",
    "nits-parlaklik-nedir",
    "ip-koruma-led-ekran",
    "led-panel-nedir",
    "smd-led-nedir",
    "gob-led-nedir",
    "istanbul-led-ekran",
    "ankara-led-ekran",
    "izmir-led-ekran",
    "havaalani-led-ekran",
    "otel-led-ekran",
    "fuar-led-ekran",
    "billboard-led-ekran",
    "toplanti-odasi-led-ekran",
]

SITE = "https://ledajans.com"


def main() -> int:
    s = requests.Session()
    s.headers["User-Agent"] = "LEDAJANS-URL-Check/1.0"
    missing = []
    rehber_only = []
    for slug in SLUGS:
        root = f"{SITE}/{slug}/"
        rehber = f"{SITE}/rehber/{slug}/"
        r_root = s.get(root, timeout=20, allow_redirects=True)
        time.sleep(0.15)
        r_reh = s.get(rehber, timeout=20, allow_redirects=True)
        time.sleep(0.15)
        ok_root = r_root.status_code == 200
        ok_reh = r_reh.status_code == 200
        if ok_root:
            continue
        if ok_reh and not ok_root:
            rehber_only.append(slug)
        elif r_root.status_code == 404:
            missing.append((slug, r_root.status_code, r_reh.status_code))
    print(f"Kok URL 200: {len(SLUGS) - len(rehber_only) - len(missing)}")
    if rehber_only:
        print("\nSadece /rehber/ altinda (kok 404):")
        for s in rehber_only:
            print(f"  /{s}/ -> /rehber/{s}/")
    if missing:
        print("\nKok ve rehber ikisi de sorunlu:")
        for row in missing:
            print(f"  {row}")
    return 1 if rehber_only or missing else 0


if __name__ == "__main__":
    sys.exit(main())
