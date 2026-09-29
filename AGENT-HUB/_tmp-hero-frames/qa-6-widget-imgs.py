import json
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
UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-QA/1.0"}
CTX = ssl.create_default_context()

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")

def head(url):
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
            return r.status, r.headers.get("Content-Type", "")
    except Exception as e:
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
                return r.status, r.headers.get("Content-Type", "")
        except Exception as e2:
            return 0, str(e2)

for url in URLS:
    status, headers, html = fetch(url)
    print("=" * 72)
    print(url, "HTTP", status)

    # isolate article widget
    m = re.search(
        r'(<div class="ledajans-seo-article[\s\S]*?</div>\s*(?:<script[\s\S]*?</script>)?)',
        html,
    )
    if not m:
        # fallback: from first h1 in article to FAQ
        m = re.search(r'<div class="ledajans-seo-article[\s\S]{0,80000}', html)
    widget = m.group(0) if m else ""
    print("  widget_len", len(widget))

    w_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)', widget)
    print("  widget imgs:")
    for src in w_imgs:
        st, ct = head(src)
        name = src.split("/")[-1]
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else "?"
        banned = any(x.lower() in src.lower() for x in ["basliksiz", "icmekanrgbpanel", "dismekanrgbpanel"])
        print(f"    {st} {ext} banned={banned} {name[:70]} {ct[:40]}")

    page_h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    widget_h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", widget, re.I | re.S)
    def txt(s):
        return re.sub(r"<[^>]+>", "", s).strip()
    print("  page H1 n=", len(page_h1), [txt(x) for x in page_h1])
    print("  widget H1 n=", len(widget_h1), [txt(x) for x in widget_h1])

    # robots
    robots = re.findall(r'<meta name="robots" content="([^"]+)"', html, re.I)
    print("  robots", robots, "x-robots", headers.get("X-Robots-Tag"))

    # FAQ in widget or page
    print("  FAQPage in html", "FAQPage" in html)
    print("  widget banned strings", [b for b in ["Basliksiz", "IcMekanRGBPanel", "DisMekanRGBPanel"] if b.lower() in widget.lower()])
