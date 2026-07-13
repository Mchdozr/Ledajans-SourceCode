"""REST API erisim teshisi — sifre yazdirmaz."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import os
import sys

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests

ENV = ROOT / ".env"


def load_env() -> tuple[str, str, str]:
    if not os.path.isfile(ENV):
        print("HATA: .env yok")
        sys.exit(1)
    data: dict[str, str] = {}
    with open(ENV, encoding="utf-8-sig") as f:
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


def probe(label: str, url: str, *, auth=None) -> int:
    r = requests.get(
        url,
        auth=auth,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Diagnose"},
    )
    body = r.text or ""
    nginx = "nginx" in body.lower() and r.status_code == 403
    kind = "nginx-WAF" if nginx else ("WP-JSON" if body.strip().startswith("{") else "HTML")
    print(f"  [{label}] HTTP {r.status_code} ({kind})")
    return r.status_code


def main() -> None:
    site, user, pw = load_env()
    print(f"site={site}")
    print(f"username={user!r}")
    print(f"app_password_len={len(pw)}")
    if not pw:
        print("HATA: WP_APP_PASSWORD bos")
        sys.exit(1)

    print("\n1) Kimliksiz REST (acik olmali):")
    s1 = probe("wp-json", f"{site}/wp-json/")
    s2 = probe("posts", f"{site}/wp-json/wp/v2/posts?per_page=1")

    print("\n2) Uygulama sifresi ile (Basic Auth):")
    auth = (user, pw)
    s3 = probe("users/me", f"{site}/wp-json/wp/v2/users/me", auth=auth)
    s4 = probe("posts+auth", f"{site}/wp-json/wp/v2/posts?per_page=1", auth=auth)

    print("\n--- Sonuc ---")
    if s1 in (200,) and s3 == 403:
        print("REST acik ama Basic Auth (Uygulama Sifresi) engelleniyor.")
        print("Cozum: Hosting / Wordfence / ModSecurity — wp-json + Authorization izni.")
        print("Rehber: scripts/WP-REST-403-FIX.md")
    elif s3 == 200:
        print("OK: Deploy calistirabilirsiniz:")
        print("  python deploy-to-wordpress.py --blog-only")
    elif s1 == 403:
        print("wp-json tamamen kapali — once REST API acilmali.")
    elif s3 == 401:
        print("Kimlik hatasi: WP giris adi veya uygulama sifresi yanlis.")
        print("WP Admin > Profil > Uygulama Sifreleri > yeni sifre, .env guncelle.")
        print("WP_USERNAME = giris adi (gorunen ad degil; cogunlukla admin).")
    else:
        print(f"Beklenmeyen durum: {s1}/{s3} — destek/hosting kontrolu.")


if __name__ == "__main__":
    main()
