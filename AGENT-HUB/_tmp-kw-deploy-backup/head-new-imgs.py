from __future__ import annotations

import requests

ua = {"User-Agent": "LEDAJANS-IMG/1.0"}
urls = [
    "https://ledajans.com/wp-content/uploads/2026/09/cephe-led-ekran-bina.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/led-billboard-otoyol.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/istanbul-cephe-led-kurulum.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/pitch-dis-mekan-p10.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/rental-led-sahne.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/gob-led-yuzey.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/cob-led-lobi.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/fuar-led-stand.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/fuar-fuaye-led.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/magaza-vitrin-led.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/avm-led-ekran.webp",
]
for url in urls:
    r = requests.head(url, headers=ua, timeout=20, allow_redirects=True)
    ctype = r.headers.get("Content-Type", "")
    clen = r.headers.get("Content-Length", "")
    print(r.status_code, ctype, clen, url.split("/")[-1])
