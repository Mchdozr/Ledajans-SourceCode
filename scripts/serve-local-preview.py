#!/usr/bin/env python3
"""Para sayfa widget'larını birleştirip yerel önizleme sunar."""
from __future__ import annotations

import argparse
import http.server
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "local-preview"

NAV = """
<nav class="lp-nav">
  <a href="/local-preview/">Önizleme</a>
  <a href="/local-preview/ic-mekan.html">İç mekan</a>
  <a href="/local-preview/dis-mekan.html">Dış mekan</a>
  <a href="/local-preview/gob.html">GOB hub</a>
  <a href="/local-preview/led-ekran.html">LED ekran</a>
  <a href="/local-preview/anasayfa.html">Anasayfa widget</a>
  <a href="/local-preview/gob-nedir.html">GOB nedir</a>
  <a href="/local-preview/gob-vs.html">GOB vs COB</a>
  <a href="/local-preview/blog-gob.html">GOB blog</a>
  <a href="/local-preview/rgb-panel.html">RGB panel</a>
</nav>
"""

HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Kumbh+Sans:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="https://ledajans.com/wp-content/themes/modins/style.css?ver=7.1">
<link rel="stylesheet" href="https://ledajans.com/wp-content/themes/modins/assets/css/template.css?ver=1.1.1">
<link rel="stylesheet" href="https://ledajans.com/wp-content/themes/modins_child/style.css?ver=7.1">
<link rel="stylesheet" href="https://ledajans.com/wp-content/themes/modins/assets/css/custom_script.css?ver=7.1">
<link rel="stylesheet" href="/Ek-CSS-global.css">
<link rel="stylesheet" href="/Ek-CSS-final.css">
<style>
  html, body.lp-body {
    margin: 0;
    background: #fff;
    color: #111827;
    font-family: "Kumbh Sans", sans-serif;
  }
  .lp-nav {
    position: sticky; top: 0; z-index: 9999; display: flex; flex-wrap: wrap;
    gap: 0.5rem 1rem; padding: 0.7rem 1rem; background: #111827;
    font-family: "Kumbh Sans", sans-serif;
  }
  .lp-nav a { color: #fdba74; text-decoration: none; font-size: 0.875rem; font-weight: 600; }
  .lp-nav a:hover { color: #fff; }
  .lp-preview, .lp-preview *:not(i):not([class^="fa"]):not([class*=" fa-"]) {
    font-family: "Kumbh Sans", sans-serif;
  }
</style>
"""

PAGES: list[tuple[str, str, list[str]]] = [
    ("ic-mekan.html", "İç Mekan LED Ekran", [
        "Urunlerimiz/Ic-Mekan-Led-Ekran/hero-banner.html",
        "Urunlerimiz/Ic-Mekan-Led-Ekran/ic-mekan-led-ekran-text.html",
        "Urunlerimiz/Ic-Mekan-Led-Ekran/urun-ozellikleri.html",
        "Urunlerimiz/Ic-Mekan-Led-Ekran/sss.html",
    ]),
    ("dis-mekan.html", "Dış Mekan LED Ekran", [
        "Urunlerimiz/Dis-Mekan-Led-Ekran/hero-banner.html",
        "Urunlerimiz/Dis-Mekan-Led-Ekran/dis-mekan-led-ekran-text.html",
        "Urunlerimiz/Dis-Mekan-Led-Ekran/urun-ozellikleri.html",
        "Urunlerimiz/Dis-Mekan-Led-Ekran/ofc-serisi-outdoor.html",
        "Urunlerimiz/Dis-Mekan-Led-Ekran/sss.html",
    ]),
    ("gob.html", "GOB LED Ekran", [
        "Urunlerimiz/Gob-Led-Ekran/page.html",
    ]),
    ("led-ekran.html", "LED Ekran hub", [
        "LED Ekran/led-ekran.html",
    ]),
    ("anasayfa.html", "Anasayfa widget'ları", [
        "Anasayfa/widget-3.html",
        "Anasayfa/widget-4-Ic-Mekan.html",
        "Anasayfa/widget-5-Dis-Mekan.html",
        "Anasayfa/widget-6-Urunlerimiz-Slider.html",
        "Anasayfa/widget-7-projeler.html",
    ]),
    ("gob-nedir.html", "GOB LED nedir", [
        "SEO-Icerik-Widgets/sozluk/gob-led-nedir.html",
    ]),
    ("gob-vs.html", "GOB vs COB vs SMD", [
        "SEO-Icerik-Widgets/karsilastirmalar/gob-vs-cob-smd.html",
    ]),
    ("blog-gob.html", "GOB blog", [
        "Blog/gob-led-ekran-ne-zaman-tercih-edilir.html",
    ]),
    ("rgb-panel.html", "İç mekan RGB panel", [
        "Urunlerimiz/Ic-Mekan-RGB-Panel/ic-mekan-icin-rgb-panel-text.html",
        "Urunlerimiz/Ic-Mekan-RGB-Panel/tablo-ic-mekan-rgb-gob-led-paneller.html",
    ]),
]


def wrap(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html><html lang='tr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{title} — yerel önizleme</title>"
        f"{HEAD}"
        "</head><body class='lp-body'>\n"
        f"{NAV}\n<div class='lp-preview'>\n{body}\n</div>\n</body></html>\n"
    )


def build() -> None:
    OUT.mkdir(exist_ok=True)
    cards = []
    for name, title, parts in PAGES:
        chunks = []
        for rel in parts:
            path = ROOT / rel.replace("/", os.sep)
            chunks.append(path.read_text(encoding="utf-8"))
        (OUT / name).write_text(wrap(title, "\n".join(chunks)), encoding="utf-8")
        cards.append(f"<li><a href='{name}'>{title}</a></li>")
    index = wrap(
        "Yerel önizleme",
        "<div style='max-width:40rem;margin:2rem auto;padding:0 1rem;font-family:system-ui'>"
        "<h1>LEDAJANS — üç KW cluster (yerel)</h1>"
        "<p>WordPress teması yok; widget + CSS. Görseller canlı medya URL’sinden gelir.</p>"
        f"<ul>{''.join(cards)}</ul></div>",
    )
    (OUT / "index.html").write_text(index, encoding="utf-8")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    build()
    print(f"Önizleme yazıldı: {OUT}")
    if args.build_only:
        return 0
    os.chdir(ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as httpd:
        url = f"http://127.0.0.1:{args.port}/local-preview/"
        print(url)
        sys.stdout.flush()
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
