from __future__ import annotations

import hashlib
import re

import requests

ua = {"User-Agent": "Mozilla/5.0 LEDAJANS-HDR"}
pages = [
    "/",
    "/led-ekran/",
    "/ic-mekan-led-ekran/",
    "/dis-mekan-led-ekran/",
    "/rental-ekran/",
    "/cob-ekran/",
    "/magaza-vitrin-led-ekran/",
    "/cephe-led-ekran/",
    "/fuar-led-ekran/",
    "/projeler/",
    "/iletisim/",
    "/blog/",
    "/led-ekran-fiyatlari-2026/",
]


def extract(html: str) -> dict:
    m = re.search(r'<header[^>]*class="[^"]*wp-site-header[\s\S]*?</header>', html, re.I)
    header = m.group(0) if m else ""
    nav = re.findall(r'<nav[^>]*>[\s\S]*?</nav>', html, re.I)
    menu_links = re.findall(
        r'id="menu-item-(\d+)"[^>]*>[\s\S]*?href="([^"]+)"[\s\S]*?class="menu-title"[^>]*>([^<]+)',
        html,
    )
    phones = re.findall(r'ledajans-header-phone-text">([^<]+)', html)
    sticky = "elementor-element-123bc72" in html
    return {
        "header_len": len(header),
        "header_hash": hashlib.md5(header.encode("utf-8", "replace")).hexdigest()[:12] if header else "NONE",
        "nav_count": len(nav),
        "phones": phones[:4],
        "sticky": sticky,
        "menu": [(i, href.split("ledajans.com")[-1], t.strip()) for i, href, t in menu_links[:20]],
        "has_gva": "gva-navigation" in html or "gavias" in html.lower(),
    }


base = None
for path in pages:
    r = requests.get(f"https://ledajans.com{path}", headers=ua, timeout=40)
    info = extract(r.text)
    if path == "/":
        base = info
        print("HOME", r.status_code, info["header_hash"], "len", info["header_len"], "phones", info["phones"])
        print("  menu", info["menu"][:12])
    else:
        same = info["header_hash"] == (base or {}).get("header_hash")
        print(path, r.status_code, "SAME" if same else "DIFF", info["header_hash"], "len", info["header_len"], "phones", info["phones"])
        if not same:
            print("  menu", info["menu"][:12])
