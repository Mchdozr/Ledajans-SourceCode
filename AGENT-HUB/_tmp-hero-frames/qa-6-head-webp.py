import ssl
import urllib.request

urls = [
    "https://ledajans.com/wp-content/uploads/2026/09/cephe-led-ekran-bina.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/led-billboard-otoyol.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/istanbul-cephe-led-kurulum.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/cob-led-lobi.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/pitch-dis-mekan-p10.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/rental-led-sahne.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/gob-led-yuzey.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/gob-led-ekran.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/fuar-led-stand.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/rental-led-ekran-kiralama.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/fuar-fuaye-led.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/magaza-vitrin-led.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/avm-led-ekran.webp",
    "https://ledajans.com/wp-content/uploads/2025/11/cropped-Basliksiz-4-32x32.png",
]
UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-QA/1.0"}
CTX = ssl.create_default_context()
for u in urls:
    req = urllib.request.Request(u, headers=UA, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
            print(r.status, r.headers.get("Content-Type"), r.headers.get("Content-Length"), u.split("/")[-1])
    except Exception as e:
        print("ERR", e, u.split("/")[-1])
