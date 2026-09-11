#!/usr/bin/env python3
"""Elementor Footer taslaklarinda ledajans-footer var mi?"""
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
    for pid in (3910, 3908, 3906, 4292):
        r = requests.get(
            f"{site}/wp-json/wp/v2/elementor_library/{pid}",
            params={"context": "edit"},
            auth=auth,
            headers=headers,
            timeout=60,
        )
        print("id", pid, r.status_code)
        if r.status_code != 200:
            print(r.text[:200])
            continue
        js = r.json()
        meta = js.get("meta") or {}
        print("  title", js.get("title"), "status", js.get("status"), "slug", js.get("slug"))
        print("  meta_keys", list(meta.keys())[:30])
        raw = meta.get("_elementor_data")
        print("  el_len", len(raw) if raw else 0)
        blob = json.dumps(js, ensure_ascii=False)
        print("  has_ledajans_footer", "ledajans-footer" in blob)
        print("  has_2024", "2024 Ledajans" in blob)
        if raw:
            data = json.loads(raw) if isinstance(raw, str) else raw
            print("  sections", len(data) if isinstance(data, list) else type(data))
            s = json.dumps(data, ensure_ascii=False)
            print("  html_widget", '"widgetType": "html"' in s or '"widgetType":"html"' in s)
            print("  snippet", s[:200].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
