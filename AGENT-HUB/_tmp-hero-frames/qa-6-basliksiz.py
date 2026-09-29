import re
import ssl
import urllib.request

URLS = [
    "https://ledajans.com/cephe-led-ekran/",
    "https://ledajans.com/pitch-secim-rehberi/",
    "https://ledajans.com/gob-led-ekran/",
    "https://ledajans.com/fuar-led-ekran/",
    "https://ledajans.com/magaza-vitrin-led-ekran/",
    "https://ledajans.com/istanbul-led-ekran/",
]
BANNED = ["Basliksiz", "IcMekanRGBPanel", "DisMekanRGBPanel"]
UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-QA/1.0"}
CTX = ssl.create_default_context()

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
        return r.read().decode("utf-8", "replace")

pat = re.compile(
    r".{0,80}(Basliksiz|IcMekanRGBPanel|DisMekanRGBPanel).{0,80}",
    re.I,
)

for url in URLS:
    html = fetch(url)
    print("=" * 80)
    print(url)
    hits = pat.findall(html) if False else pat.finditer(html)
    n = 0
    for m in pat.finditer(html):
        n += 1
        snippet = m.group(0).replace("\n", " ")
        print(f"  HIT{n}: {snippet[:200]}")
    print(f"  total hits: {n}")

    # landing widget vs chrome: look around la-kw / ledajans-seo
    for cls in ["la-kw", "ledajans-seo-article", "elementor-widget-theme-post-title", "<h1"]:
        print(f"  contains {cls}: {cls.lower() in html.lower() or cls in html}")

    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    for i, h in enumerate(h1s, 1):
        text = re.sub(r"<[^>]+>", "", h).strip()
        print(f"  H1[{i}] = {text}")

    # widget images only: inside first la-kw or content
    # extract img src from main content area after entry-content
    m = re.search(r'class="[^"]*entry-content[^"]*"', html)
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)', html)
    content_webp = [s for s in imgs if "cephe" in s or "gob-" in s or "fuar-" in s or "magaza" in s or "pitch" in s or "istanbul" in s or "avm-led" in s or "rental-led" in s or "cob-led" in s or "led-billboard" in s]
    print("  landing-ish imgs:", [s.split("/")[-1] for s in content_webp])
