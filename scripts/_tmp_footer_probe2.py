#!/usr/bin/env python3
"""Footer 176 post_content + ledajans/v1 + XML-RPC meta denemesi (okuma)."""
from __future__ import annotations

import json
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

    for path in [
        "/wp-json/",
        "/wp-json/ledajans/v1",
        "/wp-json/ledajans/v1/hero-widget",
        "/wp-json/ledajans/v1/write-files",
        "/wp-json/ledajans/v1/purge",
        "/wp-json/elementor/v1",
        "/wp-json/wp/v2/gva__template/176",
        "/wp-json/wp/v2/gva__template?per_page=50",
        "/index.php?rest_route=/wp/v2/gva__template/176",
    ]:
        r = requests.get(site + path, auth=auth, headers=headers, timeout=45)
        print(f"GET {path} {r.status_code} {r.headers.get('content-type','')[:40]} {r.text[:180].replace(chr(10),' ')}")

    wp = xmlrpc.client.ServerProxy(f"{site}/xmlrpc.php", allow_none=True)
    methods = wp.system.listMethods()
    print("xmlrpc_methods", [m for m in methods if "meta" in m.lower() or "custom" in m.lower() or "option" in m.lower()][:40])

    post = wp.wp.getPost(0, user, pw, 176)
    content = post.get("post_content") or ""
    print("post176_content_len", len(content))
    print("post176_content_head", content[:400].replace("\n", " "))
    print("has_ledajans_footer", "ledajans-footer" in content)
    print("has_2024", "2024" in content)
    print("has_elementor", "elementor" in content.lower())
    print("keys", sorted(post.keys()))

    posts = wp.wp.getPosts(0, user, pw, {"post_type": "gva__template", "number": 100})
    print("gva_count", len(posts))
    for p in posts:
        print(
            p.get("post_id"),
            p.get("post_status"),
            p.get("post_name"),
            p.get("post_title"),
        )

    # theme options
    try:
        opts = wp.wp.getOptions(0, user, pw, ["stylesheet", "template", "theme_mods_tevily", "theme_mods_krowd"])
        print("options", {k: str(v)[:120] for k, v in (opts or {}).items()})
    except Exception as exc:
        print("options_err", exc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
