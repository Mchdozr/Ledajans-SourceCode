from __future__ import annotations

import requests

ua = {"User-Agent": "LEDAJANS-IMG/1.0"}
urls = [
    "https://ledajans.com/wp-content/uploads/2025/12/Basliksiz-5.png",
    "https://ledajans.com/wp-content/uploads/2025/12/Basliksiz-5-550x622.png",
    "https://ledajans.com/wp-content/uploads/2025/12/Basliksiz-1-6.png",
    "https://ledajans.com/wp-content/uploads/2025/11/Basliksiz-6-7.png",
    "https://ledajans.com/wp-content/uploads/2026/02/DisMekanRGBPanel.png",
    "https://ledajans.com/wp-content/uploads/2026/02/IcMekanRGBPanel.png",
    "https://ledajans.com/wp-content/uploads/2022/12/untitled.232-min-1.png",
    "https://ledajans.com/wp-content/uploads/2026/09/hero-stant-poster-mobile-1.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/gob-led-ekran.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/rental-led-ekran-kiralama.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/dis-mekan-led-ekran-fiyatlari.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/ic-mekan-led-ekran-fiyatlari.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/led-ekran-fiyatlari-2026.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/led-ekran-nasil-secilir.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/cob-led-ekran-nedir.webp",
]
for url in urls:
    try:
        r = requests.get(url, headers=ua, timeout=25, stream=True)
        chunk = next(r.iter_content(64), b"")
        ctype = r.headers.get("Content-Type", "")
        clen = r.headers.get("Content-Length", "")
        ok = r.status_code == 200 and b"<html" not in chunk.lower()[:20]
        print(f"{r.status_code} {ctype:28} {str(clen):8} ok={ok}  {url.split('/')[-1]}  magic={chunk[:12]!r}")
        r.close()
    except Exception as exc:
        print("ERR", url.split("/")[-1], type(exc).__name__, exc)
