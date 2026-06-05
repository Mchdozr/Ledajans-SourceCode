import re
import urllib.request

req = urllib.request.Request(
    "https://ledajans.com/",
    headers={"User-Agent": "Mozilla/5.0 (compatible; LEDAJANS-check/1.0)"},
)
html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")

names = [
    "LED Panel",
    "COB Smart Screen",
    "Rental LED Ekran",
    "Dış Mekan LED Ekran",
    "İç Mekan LED Ekran",
]
for n in names:
    print(n, n in html)

products = re.findall(r'"@type"\s*:\s*"Product"', html)
print("Product_jsonld_count", len(products))

services = re.findall(r'"@type"\s*:\s*"Service"', html)
print("Service_jsonld_count", len(services))

if "hasOfferCatalog" in html:
    i = html.find("hasOfferCatalog")
    chunk = html[i : i + 2500]
    print("catalog_has_Service", '"@type": "Service"' in chunk or '"@type":"Service"' in chunk)
    print("catalog_has_Product", '"@type": "Product"' in chunk or '"@type":"Product"' in chunk)

m = re.search(r'"@type"\s*:\s*"Product"', html)
if m:
    start = max(0, m.start() - 120)
    print("--- first Product snippet ---")
    print(html[start : m.start() + 400])
else:
    print("live_homepage_ok", "no Product JSON-LD on homepage")
