"""Mevcut WP permalink ve blog post URL'lerini listeler (degistirmez)."""
from __future__ import annotations

import os
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env() -> tuple[str, str, str]:
    path = os.path.join(ROOT, ".env")
    data: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            data[k.strip()] = v
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    user = data.get("WP_USERNAME", "")
    pw = data.get("WP_APP_PASSWORD", "").replace(" ", "")
    return site, user, pw


def main() -> None:
    site, user, pw = load_env()
    headers = {"User-Agent": "Mozilla/5.0 LEDAJANS-Permalink-Audit"}
    auth = (user, pw)

    r = requests.get(f"{site}/wp-json/wp/v2/settings", auth=auth, headers=headers, timeout=30)
    print(f"settings HTTP {r.status_code}")
    if r.status_code == 200:
        print(f"permalink_structure={r.json().get('permalink_structure')!r}")

    slugs = [
        "led-ekran-fiyatlari-2026",
        "ic-mekan-led-ekran-fiyatlari-2026",
        "dis-mekan-led-ekran-fiyatlari-2026",
        "rental-led-ekran-kiralama-fiyatlari-2026",
        "led-ekran-nasil-secilir-rehber",
        "led-ekran-rehberi",
    ]
    print("\nposts:")
    for slug in slugs:
        pr = requests.get(
            f"{site}/wp-json/wp/v2/posts",
            params={"slug": slug, "status": "any"},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        if pr.status_code != 200 or not pr.json():
            print(f"  {slug}: (yok)")
            continue
        p = pr.json()[0]
        print(f"  {slug}: {p.get('link')} [{p.get('status')}]")


if __name__ == "__main__":
    main()
