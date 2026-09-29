from __future__ import annotations

import re
import time

import requests

H = {"User-Agent": "Mozilla/5.0 LEDAJANS-LOGO-V", "Cache-Control": "no-cache"}
bust = f"?nocache={int(time.time())}"
NEW = "2026/09/ledajans-logo.webp"
OLD = "ledajans-logo-web.jpg"
pages = ["/", "/led-ekran/", "/gob-led-nedir/", "/hakkimizda/", "/blog/", "/huidu-c08l-controller/", "/en/home-en/"]
for path in pages:
    html = requests.get("https://ledajans.com" + path + bust, headers=H, timeout=35).text
    has_new_script = NEW in html and "ledajans-logo-swap" in html
    places = "ledajans-logo-places" in html
    old_jpg = html.count(OLD)
    new_webp = html.count(NEW)
    aug = html.count("2026/08/LedajansLogo.webp")
    print(f"{path:28} swap={int(has_new_script)} places={int(places)} old_jpg={old_jpg} new09={new_webp} aug08={aug}")
