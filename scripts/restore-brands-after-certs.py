#!/usr/bin/env python3
"""Markalarımız HTML widget'ini Sertifikalarımız section'indan hemen sonra ekle."""
from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PAGE_ID = 1248
BRANDS_FILE = ROOT / "Anasayfa" / "Marka-logolar.html"
UA = "LEDAJANS-Restore-Brands/1.0"


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


def eid() -> str:
    return secrets.token_hex(4)[:7]


def make_section(html: str) -> dict:
    sec_id, col_id, wid = eid(), eid(), eid()
    return {
        "id": sec_id,
        "elType": "section",
        "settings": {
            "layout": "full_width",
            "gap": "no",
        },
        "elements": [
            {
                "id": col_id,
                "elType": "column",
                "settings": {"_column_size": 100},
                "elements": [
                    {
                        "id": wid,
                        "elType": "widget",
                        "widgetType": "html",
                        "settings": {"html": html},
                        "elements": [],
                    }
                ],
            }
        ],
    }


def has_brands(nodes) -> bool:
    if isinstance(nodes, list):
        return any(has_brands(n) for n in nodes)
    if not isinstance(nodes, dict):
        return False
    html = ((nodes.get("settings") or {}).get("html") or "")
    if isinstance(html, str) and ("ledajans-brands" in html or "Markalarımız" in html):
        return True
    for key in ("elements", "content"):
        if key in nodes and has_brands(nodes[key]):
            return True
    return False


def find_certs_index(data: list) -> int:
    for i, sec in enumerate(data):
        raw = json.dumps(sec, ensure_ascii=False)
        if "ledajans-home-certs" in raw:
            return i
    return -1


def main() -> int:
    dry = "--dry-run" in sys.argv
    site, user, pw = load_env()
    html = BRANDS_FILE.read_text(encoding="utf-8")
    if "ledajans-brands" not in html:
        print("HATA: Marka-logolar.html gecersiz")
        return 1

    auth = (user, pw)
    h = {"User-Agent": UA}
    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers=h,
        timeout=60,
    )
    print("page_get", rp.status_code)
    if rp.status_code != 200:
        return 1
    raw = (rp.json().get("meta") or {}).get("_elementor_data")
    data = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(data, list):
        print("HATA: elementor root list degil")
        return 1

    if has_brands(data):
        print("OK: Markalarımız zaten var")
        return 0

    idx = find_certs_index(data)
    print("certs_index", idx)
    if idx < 0:
        print("HATA: Sertifikalar section bulunamadi")
        return 1

    section = make_section(html)
    data.insert(idx + 1, section)
    print("inserted_section", section["id"], "after", idx)

    if dry:
        print("DRY_RUN")
        return 0

    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        json={
            "meta": {
                "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            }
        },
        auth=auth,
        headers={**h, "Content-Type": "application/json"},
        timeout=120,
    )
    print("page_update", ru.status_code, ru.text[:250])
    return 0 if ru.status_code in (200, 201) else 1


if __name__ == "__main__":
    sys.exit(main())
