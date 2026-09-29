from __future__ import annotations

import re

import requests

HEADERS = {"User-Agent": "LEDAJANS-VERIFY-DIS-FUAR/1.0", "Cache-Control": "no-cache"}
SITE = "https://ledajans.com"


def main() -> None:
    for url in (
        "https://ledajans.com/wp-content/uploads/2026/09/dis-mekan-led-ekran-1.webp",
        "https://ledajans.com/wp-content/uploads/2026/09/fuar-led-ekran-stand.webp",
    ):
        h = requests.head(url, headers=HEADERS, timeout=30, allow_redirects=True)
        print("HEAD", url.split("/")[-1], h.status_code, h.headers.get("Content-Length"))

    pages = {
        "/led-ekran/": (
            "dis-mekan-led-ekran-1.webp",
            "cephe-led-ekran.webp",
            "fuar-led-ekran-stand.webp",
            "magaza-vitrin-led-cadde-1.webp",
            "cob-led-lobi.webp",
        ),
        "/fuar-led-ekran/": ("fuar-led-ekran-stand.webp",),
        "/cephe-led-ekran/": ("cephe-led-ekran.webp", "dis-mekan-led-ekran-1.webp"),
        "/pitch-secim-rehberi/": ("dis-mekan-led-ekran-1.webp", "fuar-led-ekran-stand.webp", "cob-led-lobi.webp"),
        "/dis-mekan-led-ekran/": ("dis-mekan-led-ekran-1.webp",),
        "/projeler/": ("magaza-vitrin-led-cadde-1.webp",),
    }
    for path, needles in pages.items():
        html = requests.get(SITE + path, headers=HEADERS, timeout=60).text
        print("PUBLIC", path)
        for n in needles:
            print(" ", n, html.count(n))
        if path == "/projeler/":
            titles = re.findall(r'data-title="([^"]+)"', html)
            print("  titles", titles[:3])
            print("  fuar-in-projects", "fuar-led-ekran-stand.webp" in html)
        if path == "/led-ekran/":
            print("  cob not overwritten", "cob-led-lobi.webp" in html)


if __name__ == "__main__":
    main()
