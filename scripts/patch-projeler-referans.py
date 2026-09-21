#!/usr/bin/env python3
"""EspressoLab still'i /projeler/ + anasayfa proje kartına bas."""
from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Project-Ref-Image/1.1"
WIDGET_FILE = ROOT / "Anasayfa" / "widget-7-projeler.html"
PREVIEW_FILE = ROOT / "local-preview" / "anasayfa.html"
NEW_URL = "https://ledajans.com/wp-content/uploads/2026/09/dis-mekan-led-ekran-referans.webp"
OLD_GIF = "https://ledajans.com/wp-content/uploads/2026/04/dis-mekan-led-ekran.gif"


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


def walk_set_html(nodes, new_html: str) -> list[str]:
    ids: list[str] = []
    if isinstance(nodes, list):
        for x in nodes:
            ids.extend(walk_set_html(x, new_html))
        return ids
    if not isinstance(nodes, dict):
        return ids
    html_val = (nodes.get("settings") or {}).get("html")
    is_target = nodes.get("widgetType") == "html" and isinstance(html_val, str) and (
        "ledajans-proje-listesi" in html_val or "ledajans-project-card" in html_val
    )
    if is_target:
        nodes.setdefault("settings", {})["html"] = new_html
        ids.append(str(nodes.get("id")))
    for key in ("elements", "content"):
        if key in nodes:
            ids.extend(walk_set_html(nodes[key], new_html))
    return ids


def patch_local(html: str) -> str:
    html = html.replace(OLD_GIF, NEW_URL)
    for old_cls in ("--cover", "--shift-up"):
        needle = (
            f'data-media-src="{NEW_URL}">\n            '
            f'<div class="ledajans-project-image-wrap ledajans-project-image-wrap{old_cls}">'
        )
        repl = (
            f'data-media-src="{NEW_URL}">\n            '
            '<div class="ledajans-project-image-wrap ledajans-project-image-wrap--align-top">'
        )
        if needle in html:
            html = html.replace(needle, repl, 1)
    return html


def update_page(site: str, auth: tuple[str, str], page_id: int, html: str) -> int:
    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{page_id}",
        params={"context": "edit"},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    print("page_get", page_id, rp.status_code)
    if rp.status_code != 200:
        print(rp.text[:300])
        return 0
    meta = rp.json().get("meta") or {}
    raw = meta.get("_elementor_data")
    if not raw:
        print("no elementor_data", page_id)
        return 0
    data = json.loads(raw)
    ids = walk_set_html(data, html)
    print("widgets", page_id, ids)
    if not ids:
        return 0
    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{page_id}",
        json={
            "meta": {
                "_elementor_data": json.dumps(
                    data, ensure_ascii=False, separators=(",", ":")
                )
            }
        },
        auth=auth,
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        timeout=120,
    )
    print("page_update", page_id, ru.status_code)
    return 1 if ru.status_code in (200, 201) else 0


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    html = patch_local(WIDGET_FILE.read_text(encoding="utf-8"))
    WIDGET_FILE.write_text(html, encoding="utf-8")
    print("wrote widget", NEW_URL in html, OLD_GIF not in html)
    if PREVIEW_FILE.is_file():
        preview = patch_local(PREVIEW_FILE.read_text(encoding="utf-8"))
        PREVIEW_FILE.write_text(preview, encoding="utf-8")
        print("wrote preview")

    found = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": "projeler", "context": "edit", "per_page": 5},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    print("slug_projeler", found.status_code, [p.get("id") for p in found.json()] if found.ok else found.text[:200])
    page_ids = {1248}
    if found.ok:
        for p in found.json():
            page_ids.add(int(p["id"]))
            print("projeler_page", p["id"], p.get("link"), p.get("title"))

    updated = 0
    for pid in sorted(page_ids):
        updated += update_page(site, auth, pid, html)
    dc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=30,
    )
    print("cache_delete", dc.status_code)
    for path in ("/", "/projeler/"):
        live = requests.get(
            f"{site}{path}?nocache=projeref2",
            headers={"User-Agent": UA, "Cache-Control": "no-cache"},
            timeout=45,
        )
        print(
            "live",
            path,
            live.status_code,
            "webp",
            NEW_URL in live.text,
            "gif",
            OLD_GIF in live.text,
        )
    return 0 if updated else 1


if __name__ == "__main__":
    raise SystemExit(main())
