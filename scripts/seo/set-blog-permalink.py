"""
Tum blog yazilarini /blog/%postname%/ altina alir; 301 CSV uretir.

  python scripts/set-blog-permalink.py --redirects-csv blog-301.csv
  python scripts/set-blog-permalink.py --apply --redirects-csv blog-301.csv
"""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import argparse
import csv
import os
import sys

import requests

TARGET_STRUCTURE = "/blog/%postname%/"


def load_env() -> tuple[str, str, str]:
    path = ROOT / ".env"
    if not path.is_file():
        print("HATA: .env yok")
        sys.exit(1)
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
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data.get("WP_USERNAME", ""),
        data.get("WP_APP_PASSWORD", "").replace(" ", ""),
    )


def session(site: str, user: str, pw: str) -> requests.Session:
    s = requests.Session()
    s.auth = (user, pw)
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Permalink",
        "Content-Type": "application/json",
    })
    s.base = site  # type: ignore[attr-defined]
    return s


def fetch_all_posts(s: requests.Session) -> list[dict]:
    posts: list[dict] = []
    page = 1
    while True:
        r = s.get(
            f"{s.base}/wp-json/wp/v2/posts",
            params={
                "per_page": 100,
                "page": page,
                "status": "publish,draft,future,pending,private",
                "_fields": "id,slug,link,status,title",
            },
            timeout=60,
        )
        if r.status_code != 200:
            print(f"HATA: posts list HTTP {r.status_code}")
            break
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        total_pages = int(r.headers.get("X-WP-TotalPages", 1))
        if page >= total_pages:
            break
        page += 1
    return posts


def redirect_pairs(site: str, posts: list[dict]) -> list[tuple[str, str, str]]:
    pairs: list[tuple[str, str, str]] = []
    for p in posts:
        slug = p["slug"]
        old = p["link"].rstrip("/")
        if f"{site}/blog/" in old:
            continue
        new = f"{site}/blog/{slug}"
        if old != new:
            pairs.append((slug, old, new))
    return pairs


def try_rankmath_redirect(s: requests.Session, source: str, target: str) -> bool:
    """RankMath redirect API (varsa)."""
    body = {
        "url_from": source.replace(s.base, "").rstrip("/") or "/",
        "url_to": target.replace(s.base, "").rstrip("/") or "/",
        "header_code": "301",
    }
    for path in (
        "/wp-json/rankmath/v1/redirections",
        "/wp-json/rankmath/v1/updateRedirection",
    ):
        r = s.post(f"{s.base}{path}", json=body, timeout=30)
        if r.status_code in (200, 201):
            return True
    return False


def flush_rewrite_hint(s: requests.Session) -> None:
    """Permalink kaydet tetigi: settings tekrar POST."""
    s.post(
        f"{s.base}/wp-json/wp/v2/settings",
        json={"permalink_structure": TARGET_STRUCTURE},
        timeout=30,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--redirects-csv", metavar="FILE")
    parser.add_argument("--try-rankmath", action="store_true", help="RankMath API ile 301 dene")
    args = parser.parse_args()

    site, user, pw = load_env()
    s = session(site, user, pw)
    me = s.get(f"{site}/wp-json/wp/v2/users/me", timeout=30)
    if me.status_code != 200:
        print(f"HATA: API auth {me.status_code}")
        sys.exit(1)

    settings_r = s.get(f"{site}/wp-json/wp/v2/settings", timeout=30)
    current = settings_r.json().get("permalink_structure") if settings_r.status_code == 200 else None
    print(f"permalink_structure: {current!r} -> hedef {TARGET_STRUCTURE!r}\n")

    posts = fetch_all_posts(s)
    print(f"Toplam yazı: {len(posts)}")
    pairs = redirect_pairs(site, posts)
    print(f"Kokten /blog/ altina tasinacak: {len(pairs)}\n")

    for slug, old, new in pairs[:15]:
        print(f"  {slug}")
        print(f"    {old}/ -> {new}/")
    if len(pairs) > 15:
        print(f"  ... +{len(pairs) - 15} yazı daha")

    if args.redirects_csv:
        path = args.redirects_csv
        if not os.path.isabs(path):
            path = str(ROOT / path)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["source", "target"])
            for _slug, old, new in pairs:
                w.writerow([old + "/", new + "/"])
        print(f"\nCSV: {path} ({len(pairs)} yonlendirme)")

    if not args.apply:
        print("\nUygula: python scripts/set-blog-permalink.py --apply --redirects-csv blog-301.csv")
        return

    if current != TARGET_STRUCTURE:
        r = s.post(
            f"{site}/wp-json/wp/v2/settings",
            json={"permalink_structure": TARGET_STRUCTURE},
            timeout=30,
        )
        if r.status_code != 200:
            print(f"HATA: settings HTTP {r.status_code}")
            sys.exit(1)
        check = get_settings(s).get("permalink_structure")
        if check != TARGET_STRUCTURE:
            print("UYARI: REST API permalink_structure kaydetmiyor (bu sitede normal).")
            print("ZORUNLU 30 sn: WP Admin > Ayarlar > Kalici baglantilar")
            print(f"  Ozel yapi: {TARGET_STRUCTURE}  >  Kaydet")
            print("  veya sunucuda: bash scripts/flush-rewrite-wpcli.sh")
        else:
            print("OK: permalink_structure guncellendi.")
    else:
        print("permalink_structure zaten dogru.")

    flush_rewrite_hint(s)

    posts_after = fetch_all_posts(s)
    still_root = [p for p in posts_after if f"{site}/blog/" not in p["link"]]
    ok = len(posts_after) - len(still_root)
    print(f"\nSonuc: {ok}/{len(posts_after)} yazı /blog/ altında.")
    if still_root:
        print("UYARI: Asagidakiler hala kok URL — WP Admin > Ayarlar > Kalici baglantilar > Kaydet")
        for p in still_root[:10]:
            print(f"  {p['slug']}: {p['link']}")
        print("  veya sunucuda: wp rewrite flush")

    if args.try_rankmath and pairs:
        ok_rm = 0
        for _slug, old, new in pairs:
            if try_rankmath_redirect(s, old, new):
                ok_rm += 1
        print(f"RankMath API 301: {ok_rm}/{len(pairs)}")

    if pairs and not args.try_rankmath:
        print("\n301: RankMath > Redirects > blog-301.csv import (CSV olusturulduysa).")


if __name__ == "__main__":
    main()
