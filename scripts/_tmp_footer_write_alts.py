#!/usr/bin/env python3
"""Footer yazma alternatifleri: wp-admin, ajax, plugins, xmlrpc meta."""
from __future__ import annotations

import json
import xmlrpc.client
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


def dump(label, r):
    print(f"{label} {r.status_code} loc={r.headers.get('Location','')[:80]} ct={r.headers.get('content-type','')[:36]} {r.text[:180].replace(chr(10),' ')}")


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA}

    for path in [
        "/wp-json/wp/v2/plugins",
        "/wp-json/mcp",
        "/wp-json/duplicate-post/v1",
        "/wp-json/elementor/v1/site-navigation/add-new-post",
        "/wp-json/elementor/v1/settings/elementor_cpt_support",
        "/wp-json/pll/v1",
    ]:
        r = requests.get(site + path, auth=auth, headers=headers, timeout=45, allow_redirects=False)
        dump(f"GET {path}", r)

    for path in [
        "/wp-admin/",
        "/wp-admin/post.php?post=176&action=edit",
        "/wp-admin/post.php?post=176&action=elementor",
        "/wp-admin/admin-ajax.php?action=elementor_ajax",
        "/wp-admin/admin-ajax.php?action=elementor_library_direct_actions&library_action=get_template_data&source=local&template_id=176",
    ]:
        r = requests.get(
            site + path,
            auth=auth,
            headers=headers,
            timeout=45,
            allow_redirects=False,
        )
        dump(f"ADMIN {path[:70]}", r)

    # XML-RPC: protected meta add test on a DUMMY key first? skip
    wp = xmlrpc.client.ServerProxy(f"{site}/xmlrpc.php", allow_none=True)
    methods = wp.system.listMethods()
    print("interesting_methods")
    for m in methods:
        if any(x in m.lower() for x in ["meta", "custom", "option", "term", "media", "newpost", "editpost"]):
            print(" ", m)

    # newPost with gva__template?
    print("newPost signature skip")

    r = requests.get(
        f"{site}/wp-json/elementor/v1/settings/elementor_cpt_support",
        auth=auth,
        headers=headers,
        timeout=45,
    )
    print("cpt_support", r.status_code, r.text[:500])

    r = requests.get(f"{site}/wp-json/wp/v2/types", auth=auth, headers=headers, timeout=45)
    types = r.json()
    print("all_types", list(types.keys()))
    for k, v in types.items():
        if "gva" in k.lower() or "template" in k.lower() or "footer" in k.lower():
            print(" TYPE", k, "rest", v.get("rest_base"), "vis", v.get("visibility"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
