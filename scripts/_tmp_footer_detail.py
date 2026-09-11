#!/usr/bin/env python3
"""Footer template 176 + Elementor library footer detay."""
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


def summarize_el(data, depth=0) -> None:
    if not isinstance(data, list):
        print("  not list", type(data))
        return
    for item in data:
        if not isinstance(item, dict):
            continue
        el = item.get("elType")
        wt = item.get("widgetType")
        sid = item.get("id")
        settings = item.get("settings") or {}
        html = settings.get("html") or ""
        snippet = html[:80].replace("\n", " ") if html else ""
        print("  " * depth + f"{el} {wt or ''} id={sid} html_len={len(html)} {snippet}")
        kids = item.get("elements") or []
        if kids:
            summarize_el(kids, depth + 1)


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA}

    for path in [
        "/wp-json/wp/v2/types/gva__template",
        "/wp-json/wp/v2/gva_template/176",
        "/wp-json/wp/v2/pages/176?context=edit",
        "/wp-json/wp/v2/elementor_library/176?context=edit",
        "/wp-json/wp/v2/elementor_library/3910?context=edit",
        "/wp-json/wp/v2/elementor_library/3908?context=edit",
        "/wp-json/wp/v2/elementor_library/3906?context=edit",
        "/wp-json/elementor/v1/documents/176",
        "/?p=176",
    ]:
        r = requests.get(
            site + path,
            auth=auth,
            headers=headers,
            timeout=60,
            allow_redirects=False,
        )
        loc = r.headers.get("Location", "")
        print(f"GET {path} {r.status_code} loc={loc[:80]} len={len(r.text)} ct={r.headers.get('content-type','')[:40]}")
        if r.status_code == 200 and "json" in (r.headers.get("content-type") or ""):
            try:
                data = r.json()
                print("  keys", list(data.keys())[:25] if isinstance(data, dict) else type(data))
                if isinstance(data, dict):
                    title = data.get("title")
                    if isinstance(title, dict):
                        title = title.get("raw")
                    print("  title", title, "slug", data.get("slug"), "type", data.get("type"))
                    meta = data.get("meta") or {}
                    el = meta.get("_elementor_data")
                    if el:
                        parsed = json.loads(el) if isinstance(el, str) else el
                        print("  elementor sections", len(parsed) if isinstance(parsed, list) else type(parsed))
                        summarize_el(parsed)
            except Exception as exc:
                print("  parse_err", exc)

    wp = xmlrpc.client.ServerProxy(f"{site}/xmlrpc.php", allow_none=True)
    for pid in [176, 75, 3910, 3908, 3906]:
        try:
            post = wp.wp.getPost(0, user, pw, pid)
        except Exception as exc:
            print(f"XMLRPC getPost {pid} ERR", exc)
            continue
        print(
            f"XMLRPC {pid} type={post.get('post_type')} status={post.get('post_status')} "
            f"slug={post.get('post_name')} title={post.get('post_title')}"
        )
        customs = post.get("custom_fields") or []
        interesting = []
        el_data = None
        for cf in customs:
            key = cf.get("key") or ""
            val = cf.get("value") or ""
            if key.startswith("_elementor") or "footer" in key.lower() or "gva" in key.lower() or "template" in key.lower():
                interesting.append((key, cf.get("id"), len(str(val)), str(val)[:80].replace("\n", " ")))
            if key == "_elementor_data":
                el_data = val
        for row in interesting:
            print("  CF", row)
        if el_data:
            try:
                parsed = json.loads(el_data)
                print("  el_sections", len(parsed) if isinstance(parsed, list) else type(parsed))
                summarize_el(parsed)
            except Exception as exc:
                print("  el_parse_err", exc, "prefix", str(el_data)[:60])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
