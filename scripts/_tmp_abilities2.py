#!/usr/bin/env python3
"""Abilities, Redux, File Manager, snippet CPT."""
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

    r = requests.get(f"{site}/wp-json/wp-abilities/v1/abilities", auth=auth, headers=headers, timeout=60)
    abs_ = r.json()
    print("abilities", len(abs_) if isinstance(abs_, list) else type(abs_))
    if isinstance(abs_, list):
        for a in abs_:
            print("-", a.get("name"), "|", a.get("label"))

    r = requests.get(f"{site}/wp-json/", auth=auth, headers=headers, timeout=45)
    ns = r.json().get("namespaces") or []
    print("namespaces", ns)

    for path in [
        "/wp-json/redux/v1",
        "/wp-json/redux/v1/options",
        "/wp-json/wp-file-manager/v1",
        "/wp-json/file-manager/v1",
        "/wp-json/mk_file_folder_manager/v1",
        "/wp-json/elementor-pro/v1/theme-builder",
        "/wp-json/elementor-pro/v1/theme-builder/documents",
        "/wp-json/wp/v2/elementor_snippet",
        "/wp-json/wp/v2/elementor_snippets",
        "/wp-json/wp/v2/widgets",
        "/wp-json/wp/v2/sidebars",
    ]:
        r = requests.get(site + path, auth=auth, headers=headers, timeout=45)
        print(f"GET {path} {r.status_code} {r.text[:160].replace(chr(10),' ')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
