#!/usr/bin/env python3
"""WP'de 'rehber' alt sayfalarini kok URL'ye tasir (parent=0)."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import argparse
import os
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

REHBER_PARENT_ID = 7552


def load_env() -> tuple[str, str, str]:
    path = ROOT / ".env"
    data: dict[str, str] = {}
    if path.is_file():
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--slug", action="append", help="Sadece bu slug(lar)")
    args = parser.parse_args()

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env icinde WP_USERNAME / WP_APP_PASSWORD gerekli")
        return 1

    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-Rehber-Flat/1.0", "Content-Type": "application/json"}

    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"parent": REHBER_PARENT_ID, "per_page": 100, "status": "publish"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    if r.status_code != 200:
        print(f"HATA list HTTP {r.status_code}: {r.text[:300]}")
        return 1

    pages = r.json()
    if args.slug:
        want = set(args.slug)
        pages = [p for p in pages if p.get("slug") in want]

    if not pages:
        print("Islenecek sayfa yok.")
        return 0

    print(f"{'APPLY' if args.apply else 'DRY-RUN'}: {len(pages)} sayfa parent -> 0\n")
    ok = 0
    for p in pages:
        pid = p["id"]
        slug = p["slug"]
        old = p.get("link", "")
        clash = requests.get(
            f"{site}/wp-json/wp/v2/pages",
            params={"slug": slug, "parent": 0, "per_page": 5},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        if clash.status_code == 200:
            others = [x for x in clash.json() if x["id"] != pid]
            if others:
                print(f"  ATLA [{pid}] /{slug}/ — kokte zaten id={others[0]['id']} ({others[0]['link']})")
                continue
        if not args.apply:
            print(f"  [{pid}] /{slug}/  (simdi: {old})")
            ok += 1
            continue
        u = requests.post(
            f"{site}/wp-json/wp/v2/pages/{pid}",
            json={"parent": 0},
            auth=auth,
            headers=headers,
            timeout=60,
        )
        if u.status_code not in (200, 201):
            print(f"  HATA [{pid}] {slug}: HTTP {u.status_code} {u.text[:200]}")
            continue
        new = u.json().get("link", "")
        print(f"  OK [{pid}] /{slug}/ -> {new}")
        ok += 1

    print(f"\nTamam: {ok}/{len(pages)}")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    sys.exit(main())
