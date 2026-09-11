#!/usr/bin/env python3
"""Elementor route + theme mods + footer HTML kesiti."""
from __future__ import annotations

import json
import re
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


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA}

    r = requests.get(f"{site}/wp-json/elementor/v1", auth=auth, headers=headers, timeout=45)
    data = r.json()
    routes = data.get("routes") or {}
    print("elementor_routes")
    for k in routes:
        print(" ", k, routes[k].get("methods"))

    r2 = requests.get(f"{site}/wp-json/", auth=auth, headers=headers, timeout=45)
    ns = (r2.json().get("namespaces") or [])
    print("namespaces", ns)

    wp = xmlrpc.client.ServerProxy(f"{site}/xmlrpc.php", allow_none=True)
    for key in [
        "theme_mods_modins",
        "theme_mods_modins_child",
        "modins_theme_options",
        "gva_theme_options",
        "elementor_active_kit",
        "elementor_pro_theme_builder_conditions",
    ]:
        try:
            opts = wp.wp.getOptions(0, user, pw, [key])
            print(f"OPT {key}", str(opts)[:400].replace("\n", " "))
        except Exception as exc:
            print(f"OPT {key} ERR", exc)

    live = requests.get(site + "/", headers={"User-Agent": UA, "Cache-Control": "no-cache"}, timeout=45).text
    m = re.search(r'<footer\b[^>]*>.*?</footer>', live, flags=re.I | re.S)
    if m:
        chunk = m.group(0)
        print("footer_html_len", len(chunk))
        Path(ROOT / "AGENT-HUB" / "BACKUPS").mkdir(parents=True, exist_ok=True)
        out = ROOT / "AGENT-HUB" / "BACKUPS" / "2026-09-11-live-footer.html"
        out.write_text(chunk, encoding="utf-8")
        print("wrote", out)
        print(chunk[:1500])
        print("-----TAIL-----")
        print(chunk[-800:])
    else:
        print("NO FOOTER TAG")

    post = wp.wp.getPost(0, user, pw, 176)
    (ROOT / "AGENT-HUB" / "BACKUPS" / "2026-09-11-footer-176-content.html").write_text(
        post.get("post_content") or "", encoding="utf-8"
    )
    print("content_len", len(post.get("post_content") or ""))
    print(json.dumps({k: post.get(k) for k in ["post_id", "post_type", "post_name", "post_status", "post_title", "link"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
