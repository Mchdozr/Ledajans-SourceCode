from __future__ import annotations

import re

import requests

ua = {"User-Agent": "Mozilla/5.0 LEDAJANS-HDR2"}
pages = [
    "/",
    "/led-ekran/",
    "/hakkimizda/",
    "/firma-bilgilerimiz/",
    "/projeler/",
    "/case/ic-mekan-led-ekran-gva-eski/",
    "/huidu-c08l-controller/",
    "/gob-led-nedir/",
    "/pitch-secim-rehberi/",
    "/en/",
]


def bits(html: str, path: str) -> None:
    body = re.search(r"<body[^>]*class=\"([^\"]+)\"", html)
    bc = body.group(1) if body else ""
    titles = len(re.findall(r"page-title|gva-breadcrumb|breadcrumb", html, re.I))
    current = re.findall(r'class="([^"]*current-menu-item[^"]*)"', html)
    current_titles = re.findall(
        r'current-menu-item[^>]*>[\s\S]{0,200}?class="menu-title"[^>]*>([^<]+)', html
    )
    headers = len(re.findall(r"<header", html, re.I))
    nav_menus = re.findall(r'id="menu-primary[^"]*"|class="gva-main-menu', html)
    extra_nav = "menu-item" in html
    print(
        f"{path:45} headers={headers} body_home={'home ' in bc or bc.startswith('home')} "
        f"page-id={re.search(r'page-id-(\\d+)', bc).group(1) if re.search(r'page-id-(\\d+)', bc) else '-'} "
        r"post={bool(re.search(r'single-post|single-portfolio', bc))} "
        f"crumb_hits={titles} current={current_titles[:6]}"
    )


for path in pages:
    r = requests.get(f"https://ledajans.com{path}", headers=ua, timeout=40, allow_redirects=True)
    print(r.status_code, r.url.split("?")[0])
    bits(r.text, path)
