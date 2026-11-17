#!/usr/bin/env python3
"""LEDAJANS Mobile Perf'i canliya mu-plugin olarak yazar (ledajans/v1/write-files)."""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import shutil
import subprocess
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-Install-Mobile-Perf/1.1"


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


ASSET_DIR = os.path.join(ROOT, "assets", "ledajans-mobile")


def dry_run(raw: bytes, src: str) -> int:
    """Canliya hicbir sey yazmaz: lint + imza + boyut + yuklenecek varlik listesi."""
    ok = True
    if shutil.which("php"):
        r = subprocess.run(["php", "-l", src], capture_output=True, text=True)
        print("php -l:", (r.stdout or r.stderr).strip())
        ok = ok and r.returncode == 0
    else:
        print("UYARI: php yok, lint atlandi")
    for sig in (b"ledajans_mp_v11_active", b"ledajans_mp_v13_optimize", b"GTM-WDLJTMSV"):
        found = sig in raw
        print(f"imza {sig.decode()}: {'OK' if found else 'YOK'}")
        ok = ok and found
    ver = next((l.split(b":", 1)[1].strip().decode() for l in raw.splitlines() if b"Version:" in l), "?")
    print(f"surum: {ver}  boyut: {len(raw)} B  sha256: {hashlib.sha256(raw).hexdigest()[:16]}")
    print("hedef: wp-content/mu-plugins/ledajans-perf-patch.php (ledajans/v1/write-files)")
    if os.path.isdir(ASSET_DIR):
        files = sorted(os.listdir(ASSET_DIR))
        total = sum(os.path.getsize(os.path.join(ASSET_DIR, f)) for f in files)
        print(f"varliklar ({len(files)} dosya, {total // 1024} KiB) -> wp-content/uploads/ledajans-mobile/ (SFTP/Plesk):")
        for f in files:
            print(f"  {f}  {os.path.getsize(os.path.join(ASSET_DIR, f)) // 1024} KiB")
        print("  (yuklenmezse yama orijinal URL'leri kullanir; kirik gorsel olmaz)")
    print("DRY-RUN:", "OK — canliya yazilmadi" if ok else "HATA")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="canliya yazmadan kontrol et")
    args = ap.parse_args()

    src = os.path.join(ROOT, "wordpress-mobil-hiz-patch.php")
    if not os.path.isfile(src):
        print("HATA: wordpress-mobil-hiz-patch.php yok")
        return 1

    raw = open(src, "rb").read()
    if b"ledajans_mp_v11_active" not in raw:
        print("HATA: patch mobil-only imza icermiyor (ledajans_mp_v11_active)")
        return 1

    if args.dry_run:
        return dry_run(raw, src)

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli (WP_USERNAME / WP_APP_PASSWORD)")
        return 1

    mu_b64 = base64.b64encode(raw).decode("ascii")
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    r = requests.post(
        f"{site}/wp-json/ledajans/v1/write-files",
        json={"mu_b64": mu_b64},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print("write-files", r.status_code, r.text[:800])
    if r.status_code not in (200, 201):
        return 1

    # Dogrula: yanitta path / bytes beklenir
    try:
        body = r.json()
        print("response_keys", list(body.keys()) if isinstance(body, dict) else type(body))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
