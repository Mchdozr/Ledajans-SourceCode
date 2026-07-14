#!/usr/bin/env python3
"""Rank recovery degisikliklerini canliya al (REST API).

Gereksinim: repo kokunde .env veya ortam degiskenleri WP_USERNAME + WP_APP_PASSWORD

Kullanim:
  python3 scripts/deploy-rank-recovery-live.py           # dry-run
  python3 scripts/deploy-rank-recovery-live.py --apply   # canli yaz
"""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import argparse
import os
import subprocess
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)


BLOG_UPDATES = [
    (
        "Blog/dis-mekan-led-ekran-fiyatlari-2026-rehber.html",
        "dis-mekan-led-ekran-fiyatlari-2026",
        "Dış Mekan LED Ekran Fiyatları 2026",
        "post",
    ),
]

MANUAL_PLESK = """
=== Plesk / Elementor ile MANUEL (REST disinda) ===
1) wp-content/mu-plugins/ledajans-perf-patch.php
   -> Repodaki ops/wordpress/mobil-hiz-patch.php TAMAMINI yapistir (mobil CWV).
2) httpdocs/robots.txt
   -> Repodaki ops/robots.txt (crawl-budget kurallari).
3) Anasayfa Elementor -> widget-3 (Hakkimizda)
   -> Anasayfa/widget-3.html icerigini ilgili HTML widget'a yapistir.
4) /dis-mekan-led-ekran/ Elementor -> SEO metin widget'i
   -> Urunlerimiz/Dis-Mekan-Led-Ekran/dis-mekan-led-ekran-text.html yapistir.
5) LiteSpeed / WP cache temizle.
"""


def _parse_env_text(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    return data


def load_env() -> tuple[str, str, str]:
    path = ROOT / ".env"
    data: dict[str, str] = {}
    if path.is_file():
        with open(path, encoding="utf-8-sig") as f:
            data.update(_parse_env_text(f.read()))
    # Cloud Agent ortaminda yalnizca cursor-deploy inject edilebiliyor;
    # icinde WP_USERNAME= / WP_APP_PASSWORD= satirlari varsa oku.
    cursor_deploy = os.environ.get("cursor-deploy", "")
    if "=" in cursor_deploy:
        data.update(_parse_env_text(cursor_deploy))
    site = (
        os.environ.get("WP_SITE_URL")
        or data.get("WP_SITE_URL")
        or "https://ledajans.com"
    ).rstrip("/")
    user = os.environ.get("WP_USERNAME") or data.get("WP_USERNAME", "")
    pw = (
        os.environ.get("WP_APP_PASSWORD")
        or data.get("WP_APP_PASSWORD")
        or ""
    ).replace(" ", "")
    return site, user, pw


def verify_auth(site: str, user: str, pw: str) -> bool:
    r = requests.get(
        f"{site}/wp-json/wp/v2/users/me",
        auth=(user, pw),
        headers={"User-Agent": "LEDAJANS-Rank-Recovery-Live/1.0"},
        timeout=30,
    )
    if r.status_code == 200:
        print(f"  OK: {r.json().get('name', user)}")
        return True
    print(f"  HATA HTTP {r.status_code}: kimlik dogrulama basarisiz")
    if r.status_code == 403:
        print("  IP engeli olabilir — komutu kendi PC'nizden calistirin.")
    return False


def run_py(script: str, apply: bool) -> int:
    cmd = [sys.executable, str(ROOT / "scripts" / script)]
    if apply:
        cmd.append("--apply")
    print(f"\n>> python3 scripts/{script}" + (" --apply" if apply else ""))
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def deploy_blog_file(
    site: str,
    user: str,
    pw: str,
    file_rel: str,
    slug: str,
    title: str,
    post_type: str,
    apply: bool,
) -> bool:
    content = content_path(file_rel).read_text(encoding="utf-8")
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-Rank-Recovery-Live/1.0", "Content-Type": "application/json"}
    endpoint = f"{site}/wp-json/wp/v2/{'posts' if post_type == 'post' else 'pages'}"
    r = requests.get(
        endpoint,
        params={"slug": slug, "status": "publish,draft,private"},
        auth=auth,
        headers=headers,
        timeout=30,
    )
    if r.status_code != 200 or not r.json():
        print(f"  ATLANDI: /{slug}/ bulunamadi")
        return False
    post_id = int(r.json()[0]["id"])
    if not apply:
        print(f"  [dry-run] GUNCELLE post_id={post_id} slug={slug} ({len(content)} char)")
        return True
    u = requests.post(
        f"{endpoint}/{post_id}",
        json={"content": content, "status": "publish"},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    if u.status_code not in (200, 201):
        print(f"  HATA HTTP {u.status_code}: {u.text[:200]}")
        return False
    print(f"  OK: /blog/{slug}/ guncellendi (id={post_id})")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Canli yaz (varsayilan: dry-run)")
    args = parser.parse_args()

    site, user, pw = load_env()
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"LEDAJANS rank-recovery canli deploy — {mode}\n")

    if not user or not pw:
        print("HATA: WP kimlik bilgisi yok.")
        print("  .env olusturun (.env.example) veya ortam degiskeni:")
        print("    WP_USERNAME=...")
        print("    WP_APP_PASSWORD=...")
        print("\nCursor Cloud: Environment secrets'a WP_USERNAME ve WP_APP_PASSWORD ekleyin.")
        print("(cursor-deploy secret'i WP sifresi degil — 401 donuyor.)")
        return 1

    print("1) Kimlik dogrulama...")
    if not verify_auth(site, user, pw):
        return 1

    print("\n2) Hub /led-ekran/ icerik...")
    rc_hub = run_py("deploy/deploy-money-pages.py", args.apply)

    print("\n3) RankMath P0 + anasayfa meta...")
    rc_meta = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seo" / "set-rankmath-p0-meta.py")]
        + (["--apply"] if args.apply else []),
        cwd=ROOT,
    ).returncode

    print("\n4) Blog guncellemeleri...")
    blog_ok = 0
    for file_rel, slug, title, ptype in BLOG_UPDATES:
        print(f"  >> /blog/{slug}/")
        if deploy_blog_file(site, user, pw, file_rel, slug, title, ptype, args.apply):
            blog_ok += 1

    print("\n5) Elementor HTML widget'lari (canli gorunum)...")
    rc_el = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "deploy" / "deploy-elementor-widgets.py")]
        + (["--apply"] if args.apply else []),
        cwd=ROOT,
    ).returncode

    print("\n6) robots.txt + mu-plugin...")
    rc_files = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "deploy" / "deploy-site-files.py")]
        + (["--apply"] if args.apply else []),
        cwd=ROOT,
    ).returncode

    print("\n7) Canli dogrulama...")
    if args.apply:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify" / "verify-rankmath-p0-meta.py")],
            cwd=ROOT,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify" / "verify-money-pages-live.py")],
            cwd=ROOT,
        )

    print(MANUAL_PLESK)

    fail = (rc_hub != 0) + (rc_meta != 0) + (blog_ok != len(BLOG_UPDATES)) + (rc_el != 0) + (rc_files != 0)
    if not args.apply:
        print("\nDry-run tamam. Canli icin: python3 scripts/deploy-rank-recovery-live.py --apply")
        return 0
    print(f"\nDeploy tamam (Elementor + robots + mu-plugin dahil).")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
