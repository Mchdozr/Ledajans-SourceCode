#!/usr/bin/env python3
"""elementor_snippet REST + widgets + abilities."""
from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"


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
    headers = {"User-Agent": UA}

    r = requests.get(f"{site}/wp-json/wp/v2/types/elementor_snippet", auth=auth, headers=headers, timeout=45)
    print("type", r.status_code)
    if r.status_code == 200:
        t = r.json()
        print("rest_base", t.get("rest_base"), "slug", t.get("slug"))
        print("keys", list(t.keys()))
        print("supports", t.get("supports"))
        print("taxonomies", t.get("taxonomies"))

    r = requests.get(
        f"{site}/wp-json/wp/v2/elementor_snippet",
        params={"per_page": 50, "context": "edit"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    print("list", r.status_code, "len", len(r.text))
    try:
        items = r.json()
        print("count", len(items) if isinstance(items, list) else items)
        if isinstance(items, list):
            for it in items:
                print(
                    it.get("id"),
                    it.get("status"),
                    it.get("slug"),
                    it.get("title"),
                    list((it.get("meta") or {}).keys())[:20],
                )
    except Exception as exc:
        print("parse", exc, r.text[:300])

    # schema
    r = requests.options(f"{site}/wp-json/wp/v2/elementor_snippet", auth=auth, headers=headers, timeout=45)
    print("options", r.status_code)
    try:
        schema = r.json()
        # routes schema
        print(json.dumps(schema, ensure_ascii=False)[:1500])
    except Exception:
        print(r.text[:400])

    r = requests.get(f"{site}/wp-json/wp-abilities/v1/abilities", auth=auth, headers=headers, timeout=45)
    print("abilities", r.status_code, r.text[:800].replace("\n", " "))

    r = requests.get(f"{site}/wp-json/wp/v2/widgets", auth=auth, headers=headers, timeout=45)
    print("widgets", r.status_code, r.text[:400].replace("\n", " "))

    r = requests.get(f"{site}/wp-json/wp/v2/widget-types", auth=auth, headers=headers, timeout=45)
    print("widget-types", r.status_code, str(r.json())[:300] if r.status_code == 200 else r.text[:200])

    r = requests.get(f"{site}/wp-json/wp/v2/sidebars", auth=auth, headers=headers, timeout=45)
    print("sidebars", r.status_code, r.text[:500].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
