from __future__ import annotations

import time

import requests

ua = {"User-Agent": "Mozilla/5.0 LEDAJANS-HUB-IMG", "Cache-Control": "no-cache"}
html = requests.get(
    f"https://ledajans.com/led-ekran/?nocache={int(time.time())}", headers=ua, timeout=40
).text
needles = [
    "cob-led-lobi.webp",
    "cephe-led-ekran-bina.webp",
    "rental-led-sahne.webp",
    "cob-led-ekran-nedir.webp",
    "ic-mekan-rgb-panel-1.webp",
    "dis-mekan-rgb-panel-1.webp",
    "magaza-vitrin-led.webp",
    "fuar-led-stand.webp",
    "pitch-dis-mekan-p10.webp",
]
old = [
    "IcMekanRGBPanel.png",
    "DisMekanRGBPanel.png",
    "Basliksiz-1-6.png",
    "Basliksiz-5.png",
    "untitled.232-min-1.png",
    "rentalkabin-600x540.png",
    "Basliksiz-6-7.png",
    "Basliksiz-5-550x622.png",
]
print({n: (n in html) for n in needles})
print("OLD", {n: (n in html) for n in old})
