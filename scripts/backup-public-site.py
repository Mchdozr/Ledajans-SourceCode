#!/usr/bin/env python3
"""ledajans.com'un herkese açık halini salt okunur olarak yedekler (giriş gerektirmez).

Çıktı: YEDEK/<tarih>/
  html/<yol>.html          sitemap'teki her URL'nin canlı HTML'i (TR + EN + DE)
  html.tar.gz              aynı klasörün sıkıştırılmış hali (depoya giren bu)
  rest/<tip>.json          REST API context=view (başlık, içerik, slug, link, tarih)
  meta.csv                 URL, durum, title, açıklama, robots, canonical, H1, og:image, kelime
  sitemaps/, robots.txt, llms.txt
  yonlendirmeler.csv       bilinen eski/olmayan adreslerin şu anki yönlendirme hedefi
Kullanım: python3 scripts/backup-public-site.py [--out YEDEK/2026-11-24]
Hiçbir şeyi değiştirmez, sadece GET isteği atar.
"""
from __future__ import annotations
import argparse, csv, concurrent.futures as cf, json, re, tarfile, time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

SITE = "https://ledajans.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36 (ledajans-yedek)"
H = {"User-Agent": UA}
SITEMAPS = ["sitemap_index.xml", "post-sitemap.xml", "page-sitemap.xml", "portfolio-sitemap.xml",
            "category-sitemap.xml", "category_portfolio-sitemap.xml"]
REDIRECT_PROBES = [
    "/case/ic-mekan-led-ekran/", "/case/dis-mekan-led-ekran/", "/case/kontrol-kartlari/", "/case/rental-ekran/",
    "/case/ic-mekan-rgb-panel/", "/led-ekran-kiralama/", "/led-ekran-tamiri/", "/led-ekran-servis/",
    "/seffaf-led-ekran/", "/led-ekran-hesaplama/", "/p10-panel-kirmizi-4/", "/dis-mekan-led-ekranlar/",
    "/rehber/magaza-vitrin-led-ekran/", "/sozluk/nits-parlaklik-nedir/", "/totem-led-ekran/",
    "/ankara-led-ekran/", "/izmir-led-ekran/", "/stadyum-led-ekran/", "/otel-led-ekran/",
]


def path_to_file(u: str) -> str:
    p = urlparse(u).path.strip("/")
    return (p or "anasayfa").replace("/", "__") + ".html"


def meta_of(u: str, r: requests.Response) -> dict:
    s = BeautifulSoup(r.text, "lxml")
    g = lambda sel, a="content": (s.select_one(sel).get(a) if s.select_one(sel) else "")
    for x in s(["script", "style", "noscript"]):
        x.decompose()
    return {"url": u, "status": r.status_code, "final_url": r.url,
            "title": s.title.get_text(strip=True) if s.title else "",
            "description": g('meta[name="description"]'), "robots": g('meta[name="robots"]'),
            "canonical": g('link[rel="canonical"]', "href"), "og_image": g('meta[property="og:image"]'),
            "h1": " | ".join(h.get_text(" ", strip=True) for h in s.find_all("h1")),
            "words": len(s.get_text(" ").split()), "bytes": len(r.content), "file": path_to_file(u)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"YEDEK/{date.today().isoformat()}")
    a = ap.parse_args()
    out = Path(a.out); (out / "html").mkdir(parents=True, exist_ok=True)
    (out / "sitemaps").mkdir(exist_ok=True); (out / "rest").mkdir(exist_ok=True)

    urls: list[str] = []
    for sm in SITEMAPS:
        r = requests.get(f"{SITE}/{sm}", headers=H, timeout=60)
        (out / "sitemaps" / sm).write_text(r.text, encoding="utf-8")
        if sm != "sitemap_index.xml":
            urls += [u for u in re.findall(r"<loc>([^<]+)</loc>", r.text) if "/wp-content/" not in u]
    for f in ["robots.txt", "llms.txt"]:
        (out / f).write_bytes(requests.get(f"{SITE}/{f}", headers=H, timeout=60).content)  # ham bayt: sunucu charset bildirmiyor
    extra = [SITE + p for p in REDIRECT_PROBES if p.endswith(("ankara-led-ekran/", "izmir-led-ekran/", "stadyum-led-ekran/", "otel-led-ekran/"))]
    urls = list(dict.fromkeys(urls + extra))

    def one(u):
        for i in range(3):
            try:
                r = requests.get(u, headers=H, timeout=60)
                (out / "html" / path_to_file(u)).write_bytes(r.content)
                return meta_of(u, r)
            except Exception as e:  # noqa: BLE001
                err = str(e); time.sleep(2 * (i + 1))
        return {"url": u, "status": "ERR", "title": err}
    with cf.ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(one, urls))
    with open(out / "meta.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["url", "status", "final_url", "title", "description", "robots", "canonical",
                                          "og_image", "h1", "words", "bytes", "file"])
        w.writeheader(); [w.writerow(r) for r in rows]

    for t in ["pages", "posts", "portfolio", "categories", "media"]:
        allp, page = [], 1
        while True:
            r = requests.get(f"{SITE}/wp-json/wp/v2/{t}", params={"per_page": 100, "page": page, "context": "view"}, headers=H, timeout=120)
            if r.status_code != 200:
                break
            data = r.json()
            if not data:
                break
            allp += data
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                break
            page += 1
        (out / "rest" / f"{t}.json").write_text(json.dumps(allp, ensure_ascii=False, indent=1), encoding="utf-8")

    with open(out / "yonlendirmeler.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["adres", "durum", "hedef"])
        for p in REDIRECT_PROBES:
            r = requests.get(SITE + p, headers=H, timeout=60, allow_redirects=False)
            w.writerow([p, r.status_code, r.headers.get("Location", "")])

    with tarfile.open(out / "html.tar.gz", "w:gz") as tar:
        tar.add(out / "html", arcname="html")
    ok = sum(1 for r in rows if r.get("status") == 200)
    print(f"{len(rows)} URL, {ok} tanesi 200 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
