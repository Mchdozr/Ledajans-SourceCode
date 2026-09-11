#!/usr/bin/env python3
"""WP MCP / abilities / plugins REST keşfi."""
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


def routes_of(js):
    routes = js.get("routes") or {}
    for k, v in routes.items():
        print(" ", k, v.get("methods"))


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA}

    for path in ["/wp-json/mcp", "/wp-json/wp-abilities/v1", "/wp-json/duplicate-post/v1"]:
        r = requests.get(site + path, auth=auth, headers=headers, timeout=45)
        print("====", path, r.status_code)
        try:
            routes_of(r.json())
        except Exception as exc:
            print(exc, r.text[:200])

    r = requests.get(f"{site}/wp-json/wp/v2/plugins", auth=auth, headers=headers, timeout=60)
    plugins = r.json()
    print("plugin_count", len(plugins) if isinstance(plugins, list) else type(plugins))
    if isinstance(plugins, list):
        for p in plugins:
            print(p.get("status"), p.get("plugin"), p.get("name"))

    # abilities list
    for path in [
        "/wp-json/wp-abilities/v1/abilities",
        "/wp-json/mcp/abilities",
        "/wp-json/mcp/v1",
        "/wp-json/mcp/tools",
    ]:
        r = requests.get(site + path, auth=auth, headers=headers, timeout=45)
        print("GET", path, r.status_code, r.text[:300].replace("\n", " "))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
