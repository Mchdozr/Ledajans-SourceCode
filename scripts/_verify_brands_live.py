#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def load_env():
    data = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data["WP_USERNAME"],
        data["WP_APP_PASSWORD"].replace(" ", ""),
    )


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    h = {"User-Agent": "LEDAJANS-Verify/1.0"}

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/1248",
        params={"context": "edit"},
        auth=auth,
        headers=h,
        timeout=60,
    )
    raw = (rp.json().get("meta") or {}).get("_elementor_data")
    data = json.loads(raw) if isinstance(raw, str) else raw
    print("sections", len(data))
    for i, sec in enumerate(data[:8]):
        blob = json.dumps(sec, ensure_ascii=False)
        flags = []
        if "ledajans-brands" in blob:
            flags.append("brands")
        if "ledajans-home-certs" in blob:
            flags.append("certs")
        if "ledajans-hero" in blob:
            flags.append("hero")
        print(i, " ".join(flags) or "-", "id", sec.get("id"))

    # Purge via known custom endpoints / hero-widget re-touch
    for path in (
        "/wp-json/ledajans/v1/purge",
        "/wp-json/ledajans/v1/hero-widget",
    ):
        try:
            r = requests.post(site + path, auth=auth, headers=h, timeout=30, json={})
            print("endpoint", path, r.status_code, r.text[:160])
        except Exception as exc:
            print("endpoint", path, "ERR", exc)

    # Force Elementor clear: post same data again + status publish
    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/1248",
        json={
            "status": "publish",
            "meta": {
                "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                "_elementor_edit_mode": "builder",
            },
        },
        auth=auth,
        headers={**h, "Content-Type": "application/json"},
        timeout=120,
    )
    print("republish", ru.status_code)

    # LiteSpeed purge if available via plugin REST
    try:
        rls = requests.get(site + "/?LSCWP_CTRL=purge&litespeed_type=purge_all", headers=h, timeout=20)
        print("lsc_purge_get", rls.status_code)
    except Exception as exc:
        print("lsc_purge_get ERR", exc)

    home = requests.get(
        site + "/",
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone)",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        timeout=45,
    ).text
    print("home_brands", "ledajans-brands" in home or "Markalarımız" in home)
    print("home_certs", "ledajans-home-certs" in home)
    print("home_primary", "LED Ekranları İncele" in home)
    # position check
    i_certs = home.find("ledajans-home-certs")
    i_brands = home.find("ledajans-brands")
    print("order_certs_then_brands", i_certs >= 0 and i_brands > i_certs, i_certs, i_brands)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
