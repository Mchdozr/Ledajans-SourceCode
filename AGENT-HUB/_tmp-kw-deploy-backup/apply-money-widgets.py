from __future__ import annotations

import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]

PRICE_REPLS = [
    ("https://ledajans.com/blog/led-ekran-fiyatlari-2026-rehber/", "https://ledajans.com/led-ekran-fiyatlari-2026/"),
    ("https://ledajans.com/blog/led-ekran-fiyatlari-2026/", "https://ledajans.com/led-ekran-fiyatlari-2026/"),
    ("https://ledajans.com/blog/ic-mekan-led-ekran-fiyatlari-2026/", "https://ledajans.com/ic-mekan-led-ekran-fiyatlari-2026/"),
    ("https://ledajans.com/blog/dis-mekan-led-ekran-fiyatlari-2026/", "https://ledajans.com/dis-mekan-led-ekran-fiyatlari-2026/"),
    ("https://ledajans.com/blog/rental-led-ekran-kiralama-fiyatlari-2026/", "https://ledajans.com/rental-led-ekran-kiralama-fiyatlari-2026/"),
]

HIDE_TITLE = """
    body.page-id-5001 .page-title,
    body.page-id-5001 .page-title h1,
    body.page-id-5001 .gva-breadcrumb-content h1,
    body.page-id-5001 header.entry-header h1,
    body.page-id-5001 .title-info > h1.title {
      display: none !important;
    }
"""

COB_START = "<!-- LEDAJANS - COB & Smart Screen ANA SAYFA"
COB_END = "<style>\n    /* COB Smart Screen - mobil uyumlu, kompakt */"


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


def get_page(site: str, auth, headers, pid: int) -> dict:
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        params={"context": "edit"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def put_page(site: str, auth, headers, pid: int, content: str) -> None:
    r = requests.post(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        json={"content": content},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"POST {pid} HTTP {r.status_code}: {r.text[:300]}")


def rewrite_prices(html: str) -> str:
    for a, b in PRICE_REPLS:
        html = html.replace(a, b)
    return html


def inject_hide_css(hub: str) -> str:
    if "body.page-id-5001" in hub:
        return hub
    needle = ".la-card { cursor: pointer; }"
    if needle not in hub:
        raise RuntimeError("hub hide-css insert point missing")
    return hub.replace(needle, needle + HIDE_TITLE, 1)


def patch_cob(live: str, hub_html: str) -> str:
    start = live.find(COB_START)
    end = live.find(COB_END)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError(f"cob splice failed start={start} end={end}")
    return live[:start] + hub_html.rstrip() + "\n\t\t\t\t\t" + live[end:]


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


def main() -> None:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-KW-Apply/1.0", "Content-Type": "application/json"}

    hub = (ROOT / "LED Ekran" / "led-ekran.html").read_text(encoding="utf-8")
    hub = inject_hide_css(hub)
    put_page(site, auth, headers, 5001, hub)
    print("OK hub /led-ekran/ id=5001")

    cob_hub = (ROOT / "Urunlerimiz" / "Cob-Smart-Screen" / "cob-ve-smart-screen-led-ekran-modelleri.html").read_text(
        encoding="utf-8"
    )
    cob_live = (get_page(site, auth, headers, 3958).get("content") or {}).get("raw") or ""
    cob_live = rewrite_prices(cob_live)
    cob_live = patch_cob(cob_live, cob_hub)
    cob_live = insert_after_href(
        cob_live, "https://ledajans.com/cob-led-ne-zaman/", "https://ledajans.com/gob-led-ekran/", "GOB LED ekran"
    )
    cob_live = insert_after_href(
        cob_live, "https://ledajans.com/gob-led-ekran/", "https://ledajans.com/pitch-secim-rehberi/", "Pitch seçim rehberi"
    )
    put_page(site, auth, headers, 3958, cob_live)
    print("OK cob-ekran id=3958")

    extras = {
        5002: ("https://ledajans.com/p2-vs-p3-led-ekran/", "https://ledajans.com/pitch-secim-rehberi/", "Pitch seçim rehberi (P2–P10)"),
        5003: ("https://ledajans.com/stadyum-led-ekran/", "https://ledajans.com/cephe-led-ekran/", "Cephe LED ekran"),
        5004: ("https://ledajans.com/fuar-led-ekran/", "https://ledajans.com/pitch-secim-rehberi/", "Pitch seçim rehberi"),
    }
    for pid, (after, href, label) in extras.items():
        live = (get_page(site, auth, headers, pid).get("content") or {}).get("raw") or ""
        live = rewrite_prices(live)
        live = insert_after_href(live, after, href, label)
        put_page(site, auth, headers, pid, live)
        print(f"OK product id={pid}")


if __name__ == "__main__":
    main()
