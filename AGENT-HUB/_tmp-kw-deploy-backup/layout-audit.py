import re
import sys

import requests

for u in sys.argv[1:]:
    r = requests.get(f"https://ledajans.com/{u}/", headers={"User-Agent": "Mozilla/5.0 LA-audit"}, timeout=60)
    t = r.text
    print("==", u, r.status_code, r.url, len(t))
    m = re.search(r'<body[^>]*class="([^"]*)"', t)
    print("body", m.group(1)[:300] if m else "")
    print("neden", len(re.findall("Neden", t)), "urunlerimiz", len(re.findall("Ürünlerimiz", t)))
    for h in re.findall(r"<(h[1-4])[^>]*>(.*?)</\1>", t, re.S):
        print(" ", h[0], re.sub(r"<[^>]+>|\s+", " ", h[1]).strip()[:80])
