from __future__ import annotations

import re

import requests

HEADERS = {"User-Agent": "LEDAJANS-VERIFY-IC/1.0", "Cache-Control": "no-cache"}
SITE = "https://ledajans.com"
NEW = "ic-mekan-led-ekran-1.webp"


def main() -> None:
    h = requests.head(
        f"{SITE}/wp-content/uploads/2026/09/{NEW}",
        headers=HEADERS,
        timeout=30,
        allow_redirects=True,
    )
    print("HEAD", NEW, h.status_code, h.headers.get("Content-Length"))

    hub = requests.get(f"{SITE}/led-ekran/", headers=HEADERS, timeout=60).text
    print(
        "/led-ekran/",
        "indoor",
        hub.count(NEW),
        "cob-card",
        "cob-led-ekran-nedir.webp" in hub,
        "vitrin",
        "magaza-vitrin-led-cadde-1.webp" in hub,
        "cephe",
        "cephe-led-ekran.webp" in hub,
        "dis",
        "dis-mekan-led-ekran-1.webp" in hub,
        "fuar",
        "fuar-led-ekran-stand.webp" in hub,
    )

    ic = requests.get(f"{SITE}/ic-mekan-led-ekran/", headers=HEADERS, timeout=60).text
    print("/ic-mekan-led-ekran/", NEW, NEW in ic)

    pitch = requests.get(f"{SITE}/pitch-secim-rehberi/", headers=HEADERS, timeout=60).text
    print("/pitch-secim-rehberi/", NEW, pitch.count(NEW), "dis kept", "dis-mekan-led-ekran-1.webp" in pitch)

    proj = requests.get(f"{SITE}/projeler/", headers=HEADERS, timeout=60).text
    titles = re.findall(r'data-title="([^"]+)"', proj)
    print("/projeler/", titles[:4], "new", NEW in proj)


if __name__ == "__main__":
    main()
