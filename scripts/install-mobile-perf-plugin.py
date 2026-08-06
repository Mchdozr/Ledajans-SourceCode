#!/usr/bin/env python3
"""LEDAJANS Mobile Perf'i canliya mu-plugin olarak yazar (ledajans/v1/write-files)."""
from __future__ import annotations

import base64
import os
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


def main() -> int:
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli (WP_USERNAME / WP_APP_PASSWORD)")
        return 1

    src = os.path.join(ROOT, "wordpress-mobil-hiz-patch.php")
    if not os.path.isfile(src):
        print("HATA: wordpress-mobil-hiz-patch.php yok")
        return 1

    raw = open(src, "rb").read()
    if b"ledajans_mp_v11_active" not in raw:
        print("HATA: patch mobil-only imza icermiyor (ledajans_mp_v11_active)")
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
