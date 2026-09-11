#!/usr/bin/env python3
"""Snippet POST schema + wp_footer HTML placement + xmlrpc newPost denemesi yok, sadece okuma."""
from __future__ import annotations

import json
import re
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

    r = requests.options(
        f"{site}/wp-json/wp/v2/elementor_snippet",
        auth=auth,
        headers=headers,
        timeout=45,
    )
    js = r.json()
    endpoints = js.get("endpoints") or []
    for ep in endpoints:
        if "POST" in (ep.get("methods") or []):
            args = ep.get("args") or {}
            print("POST args", list(args.keys()))
            meta = args.get("meta", {})
            print("meta arg", json.dumps(meta, ensure_ascii=False)[:2000])

    live = requests.get(site + "/", headers={"User-Agent": UA}, timeout=45).text
    idx = live.lower().find('id="wp-footer"')
    if idx != -1:
        chunk = live[idx : idx + 2500]
        print("--- wp-footer start ---")
        print(chunk[:500])
        # find closing footer and what follows
        end = live.lower().find("</footer>", idx)
        print("--- after footer 800 ---")
        print(live[end : end + 800])

    print("has_wp_footer_fn_hint", "wp-embed" in live, "wp-emoji" in live)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
