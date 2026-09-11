#!/usr/bin/env python3
"""Canlı footer HTML + WP şablon keşfi."""
from __future__ import annotations

import json
import re
import xmlrpc.client
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
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

    live = requests.get(
        site + "/",
        headers={"User-Agent": "Mozilla/5.0 (iPhone)", "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    print("live_len", len(live))
    print("has_ledajans_footer", "ledajans-footer" in live)
    print("has_2024_copy", "2024 Ledajans" in live)
    print("has_bulten", "Bülten" in live)
    print("has_satis_kanallari", "Satış Kanallarımız" in live)

    for pat in [
        r'class="[^"]*footer[^"]*"',
        r'id="[^"]*footer[^"]*"',
        r"gva[-_]template[^\"'\s]*",
        r"elementor-location-footer",
        r"template_footer[^\"'\s]*",
        r"data-elementor-id=\"(\d+)\"",
        r"elementor-(\d+)",
    ]:
        hits = re.findall(pat, live, flags=re.I)
        uniq = list(dict.fromkeys(hits))[:12]
        print(f"PAT {pat[:50]} count={len(hits)} sample={uniq}")

    idx = live.lower().rfind("footer")
    if idx != -1:
        start = max(0, idx - 400)
        print("--- around last footer ---")
        print(live[start : start + 900].replace("\n", " ")[:900])

    routes = [
        "/wp-json/wp/v2/types",
        "/wp-json/wp/v2/gva__template",
        "/wp-json/wp/v2/elementor_library",
        "/wp-json/elementor/v1/templates",
        "/wp-json/wp/v2/pages?search=footer",
        "/wp-json/wp/v2/posts?search=footer",
    ]
    for route in routes:
        url = site + route if route.startswith("/") else route
        r = requests.get(url, auth=auth, headers=headers, timeout=60)
        ct = r.headers.get("content-type", "")
        print(f"REST {route} status={r.status_code} ct={ct[:40]} len={len(r.text)}")
        if r.status_code == 200 and "json" in ct:
            try:
                data = r.json()
            except Exception as exc:
                print("  json_err", exc)
                continue
            if isinstance(data, dict) and "gva" in route or (isinstance(data, dict) and route.endswith("types")):
                if route.endswith("types"):
                    keys = [k for k in data.keys() if "gva" in k.lower() or "elementor" in k.lower() or "template" in k.lower() or "footer" in k.lower()]
                    print("  type_keys", keys)
                    for k in keys:
                        print("   ", k, data[k].get("rest_base"), data[k].get("slug"))
                else:
                    print("  dict_keys", list(data.keys())[:20])
            elif isinstance(data, list):
                print("  list_len", len(data))
                for item in data[:15]:
                    if isinstance(item, dict):
                        print(
                            "   ",
                            item.get("id"),
                            item.get("slug") or item.get("title"),
                            item.get("type"),
                            item.get("status"),
                        )

    wp = xmlrpc.client.ServerProxy(f"{site}/xmlrpc.php", allow_none=True)
    for ptype in ["gva__template", "elementor_library", "page"]:
        try:
            posts = wp.wp.getPosts(
                0,
                user,
                pw,
                {"post_type": ptype, "number": 50},
            )
            print(f"XMLRPC {ptype} count={len(posts)}")
            for p in posts:
                title = p.get("post_title") or ""
                slug = p.get("post_name") or ""
                if "foot" in (title + slug).lower() or "footer" in (title + slug).lower() or "gva" in slug.lower():
                    print(
                        "  HIT",
                        p.get("post_id"),
                        p.get("post_type"),
                        slug,
                        title[:80],
                    )
                elif ptype != "page":
                    print("  ", p.get("post_id"), slug, title[:80])
        except Exception as exc:
            print(f"XMLRPC {ptype} ERR", exc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
