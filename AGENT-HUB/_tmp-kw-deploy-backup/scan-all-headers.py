from __future__ import annotations

import hashlib
import re

import requests

UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-HDR-SCAN"}

URLS = [
    "/",
    "/led-ekran/",
    "/ic-mekan-led-ekran/",
    "/dis-mekan-led-ekran/",
    "/rental-ekran/",
    "/cob-ekran/",
    "/magaza-vitrin-led-ekran/",
    "/cephe-led-ekran/",
    "/fuar-led-ekran/",
    "/gob-led-ekran/",
    "/pitch-secim-rehberi/",
    "/istanbul-led-ekran/",
    "/hakkimizda/",
    "/projeler/",
    "/iletisim/",
    "/blog/",
    "/huidu-c08l-controller/",
    "/led-ekran-fiyatlari-2026/",
    "/en/",
    "/en/home-en/",
    "/de/",
    "/search/led/",
    "/?s=led",
    "/404-test-xyz/",
    "/urunler/",
    "/case/ic-mekan-led-ekran-gva-eski/",
    "/ic-mekan-rgb-panel/",
    "/dis-mekan-rgb-panel/",
    "/kontrol-kartlari/",
    "/sertifikalarimiz/",
    "/firma-bilgilerimiz/",
    "/colorlight/",
    "/program-indir/",
    "/teknik-destek-videolari/",
]


def header_bits(html: str) -> dict:
    phones = "tel:+902122204004" in html and "tel:+905438795108" in html
    anasayfa = html.count('menu-title">Anasayfa')
    urun = html.count("Ürünlerimiz") + html.count("Urunlerimiz")
    htmlw = "LEDAJANS — Header HTML widget" in html
    el43 = "elementor-43" in html
    default = "header_default_screen" in html
    m = re.search(r'(<header[^>]*wp-site-header[\s\S]*?</header>)', html, re.I)
    hdr = m.group(1) if m else ""
    titles = re.findall(r'menu-title">([^<]+)', hdr)
    # unique top-level from first 20
    return {
        "phones": phones,
        "anasayfa": anasayfa,
        "urun": urun,
        "htmlw": htmlw,
        "el43": el43,
        "default": default,
        "hdr_hash": hashlib.md5(hdr.encode()).hexdigest()[:10] if hdr else "NONE",
        "titles": titles[:12],
        "n_headers": html.lower().count("<header"),
        "home_class": " home " in f" {html[html.find('<body'):html.find('<body')+400]} ",
        "len": len(html),
    }


def main() -> None:
    s = requests.Session()
    s.headers.update(UA)
    s.max_redirects = 5
    for path in URLS:
        try:
            r = s.get("https://ledajans.com" + path, timeout=35, allow_redirects=True)
        except Exception as e:
            print(f"ERR {path} {e}")
            continue
        b = header_bits(r.text)
        final = r.url.replace("https://ledajans.com", "")
        print(
            f"{r.status_code:3} {path:42} -> {final[:40]:40} "
            f"h={b['hdr_hash']} phones={int(b['phones'])} ana={b['anasayfa']} "
            f"urun={b['urun']} htmlw={int(b['htmlw'])} el43={int(b['el43'])} "
            f"nh={b['n_headers']} titles={b['titles'][:8]}"
        )


if __name__ == "__main__":
    main()
