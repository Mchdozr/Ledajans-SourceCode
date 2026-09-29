from __future__ import annotations

import hashlib
import re
import time

import requests

UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-HDR-VERIFY", "Cache-Control": "no-cache"}
bust = f"?nocache={int(time.time())}"


def fetch(path: str) -> tuple[int, str, str]:
    r = requests.get(
        f"https://ledajans.com{path}{bust}",
        headers=UA,
        timeout=40,
        allow_redirects=True,
    )
    return r.status_code, r.url, r.text


def bits(html: str) -> dict:
    m = re.search(r'(<header[^>]*wp-site-header[\s\S]*?</header>)', html, re.I)
    hdr = m.group(1) if m else ""
    titles = re.findall(r'menu-title">([^<]+)', hdr)
    case_hits = len(re.findall(r"/case/", html))
    theme_canvas = bool(re.search(r'wrapper-page">[\s\S]*?</footer>[\s\S]*?<div class="canvas-mobile"', html))
    return {
        "identity_css": 'id="ledajans-header-identity"' in html,
        "identity_js": 'id="ledajans-header-identity-js"' in html,
        "hdr_hash": hashlib.md5(hdr.encode()).hexdigest()[:10] if hdr else "NONE",
        "titles": titles[:8],
        "iletisim": "İletişim" in hdr or "Iletisim" in hdr,
        "contact_us": "Contact Us" in hdr,
        "kontakt": "Kontakt" in hdr,
        "sertifika": "sertifikalarimiz" in html.lower(),
        "ic_mekan_ok": "/ic-mekan-led-ekran/" in html,
        "case_ic": "/case/ic-mekan-led-ekran-gva-eski/" in html,
        "canvas_count": html.count('class="canvas-mobile"'),
        "hide_rule": ".wrapper-page > .canvas-mobile" in html,
        "margin_global": "#page-content,\n#wp-main-content" in html or "#page-content,\r\n#wp-main-content" in html or "margin-top: 0 !important" in html,
    }


def anamenu_urls(html: str) -> list[str]:
    chunks = re.findall(r'<ul id="menu-anamenu"[^>]*>([\s\S]*?)</ul>', html)
    urls: list[str] = []
    for ch in chunks:
        urls.extend(re.findall(r'href="([^"]+)"', ch))
    return urls


def main() -> None:
    for path in ["/", "/led-ekran/", "/hakkimizda/", "/magaza-vitrin-led-ekran/", "/en/home-en/", "/de/home-de/"]:
        code, url, html = fetch(path)
        b = bits(html)
        urls = anamenu_urls(html)
        print(f"\n{code} {path} -> {url.replace('https://ledajans.com','')}")
        print(" identity", b["identity_css"], b["identity_js"], "hide", b["hide_rule"], "canvas", b["canvas_count"])
        print(" hash", b["hdr_hash"], "titles", b["titles"])
        print(" iletisim", b["iletisim"], "contact", b["contact_us"], "kontakt", b["kontakt"])
        print(" sertifika", b["sertifika"], "ic_ok", b["ic_mekan_ok"], "old_case", b["case_ic"])
        print(" anamenu", urls[:14])


if __name__ == "__main__":
    main()
