from __future__ import annotations

import re

import requests

H = {"User-Agent": "LEDAJANS-Verify/1.0", "Cache-Control": "no-cache"}

hub = requests.get("https://ledajans.com/rental-ekran/", headers=H, timeout=60)
links = sorted(set(re.findall(r'href="(https://ledajans\.com/p\d-\d-(?:ic|dis)-mekan-rental-led-ekran/)"', hub.text)))
print("rental-ekran", hub.status_code, "model links:", len(links))
for u in links:
    r = requests.get(u, headers=H, timeout=60, allow_redirects=False)
    t = r.text
    title = re.search(r"<title>([^<]*)</title>", t)
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", t, flags=re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', t)
    ld = "Product" in t and '"@type": "Product"' in t
    print(
        f"{u} -> {r.status_code} {r.headers.get('location', '')}\n"
        f"   title={title.group(1) if title else None}\n   h1={[re.sub('<[^>]+>', '', h).strip() for h in h1s]}\n"
        f"   desc={desc.group(1)[:90] if desc else None}\n   product_schema={ld}"
    )
