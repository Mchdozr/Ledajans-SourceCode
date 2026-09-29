from __future__ import annotations

import re

import requests

for u in ("https://ledajans.com/rental-ekran/", "https://ledajans.com/p3-9-ic-mekan-rental-led-ekran/"):
    t = requests.get(u, headers={"User-Agent": "x"}, timeout=60).text
    print(u)
    print(" body:", re.search(r'<body[^>]*class="([^"]*)"', t).group(1))
    i = t.find('class="title"')
    if i > 0:
        print(" ctx:", re.sub(r"\s+", " ", t[i - 900 : i + 120]))
