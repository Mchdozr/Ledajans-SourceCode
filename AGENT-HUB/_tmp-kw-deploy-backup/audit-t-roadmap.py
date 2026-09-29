from __future__ import annotations

import requests

ua = {"User-Agent": "LEDAJANS-T-AUDIT/1.0"}

def head(url: str, allow: bool = False) -> None:
    r = requests.head(url, headers=ua, timeout=25, allow_redirects=allow)
    loc = r.headers.get("Location", "")
    xr = r.headers.get("X-Redirect-By", "")
    print(f"{r.status_code} {url} loc={loc} by={xr}")

print("=== robots ===")
r = requests.get("https://ledajans.com/robots.txt", headers=ua, timeout=25)
print(r.status_code)
for line in r.text.splitlines():
    if "sitemap" in line.lower() or line.strip().startswith("Disallow"):
        print(line)

print("\n=== sitemap ===")
for u in (
    "https://ledajans.com/sitemap_index.xml",
    "https://ledajans.com/sitemap.xml",
    "https://ledajans.com/wp-sitemap.xml",
    "https://ledajans.com/post-sitemap.xml",
    "https://ledajans.com/page-sitemap.xml",
    "https://ledajans.com/sitemap_index.xml/",
):
    try:
        rr = requests.get(u, headers=ua, timeout=25, allow_redirects=False)
        print(rr.status_code, u, rr.headers.get("Content-Type", "")[:40], "len", len(rr.content))
        if rr.status_code in (301, 302, 307, 308):
            print("  loc", rr.headers.get("Location"))
    except Exception as exc:
        print("ERR", u, type(exc).__name__)

print("\n=== fiyat ===")
for u in (
    "https://ledajans.com/led-ekran-fiyatlari-2026/",
    "https://ledajans.com/blog/led-ekran-fiyatlari-2026/",
    "https://ledajans.com/ic-mekan-led-ekran-fiyatlari-2026/",
    "https://ledajans.com/blog/ic-mekan-led-ekran-fiyatlari-2026/",
):
    head(u)

print("\n=== senaryo ===")
for u in (
    "https://ledajans.com/magaza-vitrin-led-ekran/",
    "https://ledajans.com/cephe-led-ekran/",
    "https://ledajans.com/fuar-led-ekran/",
    "https://ledajans.com/cozumler/",
    "https://ledajans.com/cozumler/magaza-led-ekran/",
    "https://ledajans.com/pitch-secim-rehberi/",
    "https://ledajans.com/gob-led-ekran/",
    "https://ledajans.com/cob-ekran/",
    "https://ledajans.com/cob-led-ekran/",
    "https://ledajans.com/istanbul-led-ekran/",
    "https://ledajans.com/led-ekran/",
    "https://ledajans.com/rental-ekran/",
):
    head(u)
