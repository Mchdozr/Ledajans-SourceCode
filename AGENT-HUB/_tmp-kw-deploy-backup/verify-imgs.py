from __future__ import annotations

import time

import requests

ua = {"User-Agent": "Mozilla/5.0 LEDAJANS-KW-IMG", "Cache-Control": "no-cache"}
bust = str(int(time.time()))
needles = {
    "/cephe-led-ekran/": ["cephe-led-ekran-bina.webp", "led-billboard-otoyol.webp", "la-kw-actions", "WhatsApp"],
    "/pitch-secim-rehberi/": ["cob-led-lobi.webp", "pitch-dis-mekan-p10.webp", "rental-led-sahne.webp"],
    "/gob-led-ekran/": ["gob-led-yuzey.webp", "cob-led-lobi.webp"],
    "/fuar-led-ekran/": ["fuar-led-stand.webp", "fuar-fuaye-led.webp"],
    "/magaza-vitrin-led-ekran/": ["magaza-vitrin-led.webp", "avm-led-ekran.webp"],
    "/istanbul-led-ekran/": ["istanbul-cephe-led-kurulum.webp", "cephe-led-ekran-bina.webp"],
}
for path, keys in needles.items():
    r = requests.get(f"https://ledajans.com{path}?nocache={bust}", headers=ua, timeout=40)
    html = r.text
    found = {k: (k in html) for k in keys}
    broken = "DisMekanRGBPanel.png" in html or "IcMekanRGBPanel.png" in html or "Basliksiz-1-6.png" in html
    print(r.status_code, path, found, "old_stock", broken, "len", len(html))
