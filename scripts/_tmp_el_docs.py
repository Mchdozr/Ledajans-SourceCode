#!/usr/bin/env python3
"""Elementor documents / site-editor / post endpoint keşfi."""
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


def dump(label: str, r: requests.Response) -> None:
    text = r.text[:500].replace("\n", " ")
    print(f"{label} {r.status_code} {r.headers.get('content-type','')[:40]} {text}")


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA}

    for path in [
        "/wp-json/elementor/v1/documents",
        "/wp-json/elementor/v1/documents/176",
        "/wp-json/elementor/v1/site-editor",
        "/wp-json/elementor/v1/site-editor/templates",
        "/wp-json/elementor/v1/site-editor/templates/176",
        "/wp-json/elementor/v1/post",
        "/wp-json/elementor/v1/post?id=176",
        "/wp-json/elementor/v1/post?post_id=176",
        "/wp-json/elementor/v1/template-library/templates",
        "/wp-json/elementor-pro/v1",
    ]:
        r = requests.get(site + path, auth=auth, headers=headers, timeout=45)
        dump(f"GET {path}", r)

    # documents namespace index
    r = requests.get(f"{site}/wp-json/elementor/v1/documents", auth=auth, headers=headers, timeout=45)
    try:
        js = r.json()
        if isinstance(js, dict) and "routes" in js:
            print("DOC ROUTES")
            for k, v in js["routes"].items():
                print(" ", k, v.get("methods"), list((v.get("endpoints") or [{}])[0].get("args", {}).keys())[:20])
    except Exception as exc:
        print("doc parse", exc)

    r = requests.get(f"{site}/wp-json/elementor/v1/post", auth=auth, headers=headers, timeout=45)
    try:
        js = r.json()
        if isinstance(js, dict):
            print("POST endpoint keys", js.keys())
            if "routes" in js:
                for k, v in js["routes"].items():
                    print(" ", k, v.get("methods"))
                    for ep in v.get("endpoints") or []:
                        print("   args", list(ep.get("args", {}).keys()))
    except Exception:
        pass

    r = requests.get(f"{site}/wp-json/elementor/v1/site-editor/templates", auth=auth, headers=headers, timeout=60)
    try:
        js = r.json()
        print("templates type", type(js), (len(js) if isinstance(js, list) else list(js)[:20] if isinstance(js, dict) else js))
        if isinstance(js, list):
            for t in js[:30]:
                print(" T", t.get("id"), t.get("title"), t.get("type"), t.get("location") if isinstance(t, dict) else t)
        elif isinstance(js, dict):
            data = js.get("data") or js.get("templates") or js
            if isinstance(data, list):
                for t in data[:30]:
                    print(" T", t)
            else:
                print(json.dumps(js, ensure_ascii=False)[:800])
    except Exception as exc:
        print("templates parse", exc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
