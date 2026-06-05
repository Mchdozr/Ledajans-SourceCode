import re
import urllib.request

URLS = [
    "https://ledajans.com/dis-mekan-led-ekran/",
    "https://ledajans.com/ic-mekan-led-ekran/",
    "https://ledajans.com/rental-ekran/",
]

for url in URLS:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LEDAJANS-check/1.0)"},
    )
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
    products = len(re.findall(r'"@type"\s*:\s*"Product"', html))
    low = "lowPrice" in html
    offers = '"@type": "Offer"' in html or '"@type":"Offer"' in html
    agg = "AggregateOffer" in html
    print(url)
    print("  Product_blocks", products)
    print("  has_lowPrice", low)
    print("  has_AggregateOffer", agg)
    print("  has_Offer", offers)
