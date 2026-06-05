#!/usr/bin/env python3
"""P1 SEO sayfa icerigini WP'ye yazar."""
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

PAGES = [
    (
        "SEO-Icerik-Widgets/sektor-rehberleri/magaza-vitrin-led-rehberi.html",
        "magaza-vitrin-led-ekran",
    ),
    (
        "SEO-Icerik-Widgets/sehir-sayfalari/istanbul-led-ekran.html",
        "istanbul-led-ekran",
    ),
]


def load_env() -> tuple[str, str, str]:
    path = os.path.join(ROOT, ".env")
    data: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data.get("WP_USERNAME", ""),
        data.get("WP_APP_PASSWORD", "").replace(" ", ""),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env")
        return 1

    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-P1-Deploy/1.0", "Content-Type": "application/json"}
    ok = 0

    for rel, slug in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        with open(path, encoding="utf-8") as f:
            content = f.read()
        print(f">> /{slug}/ ({len(content)} char)")
        if not args.apply:
            ok += 1
            continue
        r = requests.get(
            f"{site}/wp-json/wp/v2/pages",
            params={"slug": slug},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        if r.status_code != 200 or not r.json():
            print("  sayfa bulunamadi")
            continue
        pid = r.json()[0]["id"]
        u = requests.post(
            f"{site}/wp-json/wp/v2/pages/{pid}",
            json={"content": content},
            auth=auth,
            headers=headers,
            timeout=120,
        )
        if u.status_code in (200, 201):
            print(f"  OK id={pid}")
            ok += 1
        else:
            print(f"  HATA {u.status_code}")

    print(f"\n{'DRY-RUN' if not args.apply else 'APPLY'}: {ok}/{len(PAGES)}")
    return 0 if ok == len(PAGES) else 1


if __name__ == "__main__":
    sys.exit(main())
