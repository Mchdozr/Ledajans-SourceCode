from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]

PRICE_REPLS = [
    ("https://ledajans.com/blog/led-ekran-fiyatlari-2026-rehber/", "https://ledajans.com/led-ekran-fiyatlari-2026/"),
    ("https://ledajans.com/blog/led-ekran-fiyatlari-2026/", "https://ledajans.com/led-ekran-fiyatlari-2026/"),
    ("https://ledajans.com/blog/ic-mekan-led-ekran-fiyatlari-2026/", "https://ledajans.com/ic-mekan-led-ekran-fiyatlari-2026/"),
    ("https://ledajans.com/blog/dis-mekan-led-ekran-fiyatlari-2026/", "https://ledajans.com/dis-mekan-led-ekran-fiyatlari-2026/"),
    ("https://ledajans.com/blog/rental-led-ekran-kiralama-fiyatlari-2026/", "https://ledajans.com/rental-led-ekran-kiralama-fiyatlari-2026/"),
]

HIDE = """
    body.page-id-5001 .page-title,
    body.page-id-5001 .page-title h1,
    body.page-id-5001 .gva-breadcrumb-content h1,
    body.page-id-5001 header.entry-header h1,
    body.page-id-5001 .title-info > h1.title {
      display: none !important;
    }
"""
COB_START = "<!-- LEDAJANS - COB & Smart Screen ANA SAYFA"


def load_env() -> tuple[str, str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("\"'")
    return (
        env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        env["WP_USERNAME"],
        env["WP_APP_PASSWORD"].replace(" ", ""),
    )


def rewrite_prices(html: str) -> str:
    for a, b in PRICE_REPLS:
        html = html.replace(a, b)
    return html


def insert_after_href(html: str, after_href: str, href: str, label: str) -> str:
    if href in html:
        return html
    marker = f'href="{after_href}"'
    i = html.find(marker)
    if i < 0:
        return html
    close = html.find("</li>", i)
    if close < 0:
        return html
    return html[: close + 5] + f'\n    <li><a href="{href}">{label}</a></li>' + html[close + 5 :]


def walk(nodes: Any, fn) -> int:
    changed = 0
    if isinstance(nodes, list):
        for n in nodes:
            changed += walk(n, fn)
        return changed
    if not isinstance(nodes, dict):
        return 0
    settings = nodes.get("settings") or {}
    for key in ("html", "editor"):
        val = settings.get(key)
        if isinstance(val, str) and val:
            new = fn(val)
            if new != val:
                settings[key] = new
                nodes["settings"] = settings
                changed += 1
    for key in ("elements", "content"):
        if key in nodes:
            changed += walk(nodes[key], fn)
    return changed


def hub_fn(val: str) -> str:
    if ".la-wrapper" not in val and "la-gradient-title" not in val:
        return val
    hub = (ROOT / "LED Ekran" / "led-ekran.html").read_text(encoding="utf-8")
    if "body.page-id-5001" not in hub:
        hub = hub.replace(".la-card { cursor: pointer; }", ".la-card { cursor: pointer; }" + HIDE, 1)
    return hub


def cob_fn(val: str) -> str:
    val = rewrite_prices(val)
    if COB_START in val:
        hub = (ROOT / "Urunlerimiz" / "Cob-Smart-Screen" / "cob-ve-smart-screen-led-ekran-modelleri.html").read_text(
            encoding="utf-8"
        )
        start = val.find(COB_START)
        end = val.find("/* COB Smart Screen - mobil uyumlu")
        if end > start:
            style_tag = val.rfind("<style", start, end)
            if style_tag > start:
                end = style_tag
            val = val[:start] + hub.rstrip() + "\n" + val[end:]
        else:
            val = val[:start] + hub
    val = insert_after_href(
        val, "https://ledajans.com/cob-led-ne-zaman/", "https://ledajans.com/gob-led-ekran/", "GOB LED ekran"
    )
    val = insert_after_href(
        val, "https://ledajans.com/gob-led-ekran/", "https://ledajans.com/pitch-secim-rehberi/", "Pitch seçim rehberi"
    )
    return val


def product_fn(after: str, href: str, label: str):
    def fn(val: str) -> str:
        val = rewrite_prices(val)
        return insert_after_href(val, after, href, label)

    return fn


def save_page(site: str, auth, headers, pid: int, data: list) -> None:
    payload = {
        "meta": {
            "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            "_elementor_edit_mode": "builder",
        }
    }
    r = requests.post(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        json=payload,
        auth=auth,
        headers=headers,
        timeout=120,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"POST {pid} {r.status_code} {r.text[:300]}")


def load_el(site: str, auth, headers, pid: int) -> list:
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        params={"context": "edit"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    raw = (r.json().get("meta") or {}).get("_elementor_data")
    if isinstance(raw, str):
        return json.loads(raw)
    if isinstance(raw, list):
        return raw
    raise RuntimeError(f"no elementor data {pid}")


def main() -> None:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-EL-Apply/1.0", "Content-Type": "application/json"}

    jobs = [
        (5001, hub_fn),
        (3958, cob_fn),
        (
            5002,
            product_fn(
                "https://ledajans.com/p2-vs-p3-led-ekran/",
                "https://ledajans.com/pitch-secim-rehberi/",
                "Pitch seçim rehberi (P2–P10)",
            ),
        ),
        (
            5003,
            product_fn(
                "https://ledajans.com/stadyum-led-ekran/",
                "https://ledajans.com/cephe-led-ekran/",
                "Cephe LED ekran",
            ),
        ),
        (
            5004,
            product_fn(
                "https://ledajans.com/fuar-led-ekran/",
                "https://ledajans.com/pitch-secim-rehberi/",
                "Pitch seçim rehberi",
            ),
        ),
    ]
    for pid, fn in jobs:
        data = load_el(site, auth, headers, pid)
        n = walk(data, fn)
        save_page(site, auth, headers, pid, data)
        print(f"OK id={pid} widgets_changed={n}")

    r = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("elementor_cache", r.status_code)


if __name__ == "__main__":
    main()
