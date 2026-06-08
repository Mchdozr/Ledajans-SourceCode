#!/usr/bin/env python3
"""LEDAJANS katalog sayfalarını data/katalog-data.json'dan üretir."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data" / "katalog-data.json").read_text(encoding="utf-8"))
PAGES = ROOT / "pages"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def head(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>LEDAJANS — {esc(title)}</title>
  <link rel="stylesheet" href="../assets/katalog.css">
</head>
<body>
"""


def foot() -> str:
    return "</body>\n</html>\n"


def page_num(n: str, pos: str = "left") -> str:
    return f'<div class="page-num page-num--{pos}">{n}</div>'


def partners() -> str:
    names = DATA["intro"]["partners"]
    spans = "".join(
        f'<span{" style=\"color:var(--brand-orange)\"" if n == "LEDAJANS" else ""}>{n}</span>'
        for n in names
    )
    return f'<div class="partner-logos">{spans}</div>'


def generate_cover() -> str:
    c = DATA["cover"]
    cats = "\n".join(f"            <li>{esc(x)}</li>" for x in c["categories"])
    return head("Kapak") + f"""
  <div class="page page--cover">
    <div class="cover-top">
      <div class="logo">
        <div class="logo-icon"></div>
        <span class="logo-text">LEDAJANS</span>
      </div>
      <div class="cover-hero-frame">
        <img src="{c['hero']}" alt="LED Ekran Uygulamaları">
      </div>
    </div>
    <div class="cover-bottom">
      <div class="cover-bottom-inner">
        <div>
          <p class="heading-sm text-white cover-label">LED DISPLAY SYSTEMS</p>
          <div class="accent-bar"></div>
          <div class="chevrons chevrons--up">
            <div class="chevron"></div><div class="chevron"></div><div class="chevron"></div>
          </div>
        </div>
        <div>
          <h1 class="cover-title">
            <span class="heading-lg text-accent">Product</span><br>
            <span class="heading-lg text-white">Catalog</span>
          </h1>
          <ul class="cover-categories">{cats}
          </ul>
        </div>
      </div>
      <div class="cover-stripe"></div>
    </div>
  </div>
""" + foot()


def generate_intro() -> str:
    i = DATA["intro"]
    paras = "".join(f"        <p class=\"text-body\">{esc(p)}</p>\n" for p in i["text"].split("\n\n"))
    return head("Kurumsal Tanıtım") + f"""
  <div class="page page--intro">
    <div class="intro-hero">
      <img src="{i['hero']}" alt="LEDAJANS LED Ekran">
    </div>
    <div class="intro-body">
      <div class="intro-accent"></div>
      <div class="intro-text">
        {paras}
      </div>
    </div>
    {partners()}
    <div class="page-stripe"></div>
    {page_num("02")}
  </div>
""" + foot()


def generate_toc() -> str:
    imgs = "".join(
        f'        <img src="{u}" alt="Ürün görseli {n+1}">\n'
        for n, u in enumerate(DATA["toc_images"])
    )
    items = "".join(
        f"""        <li class="toc-item">
          <span class="toc-item-bar">{esc(t['title'])}</span>
          <span class="toc-item-num"><span>{t['page']}</span></span>
        </li>\n"""
        for t in DATA["toc"]
    )
    return head("İçindekiler") + f"""
  <div class="page page--toc">
    <div class="toc-header">
      <h1 class="heading-lg"><span class="text-accent">Our</span> <span class="text-navy">Products</span></h1>
      <div class="accent-bar accent-bar--wide"></div>
    </div>
    <div class="toc-body">
      <div class="toc-images">{imgs}      </div>
      <ol class="toc-list">{items}      </ol>
    </div>
    <div class="page-stripe"></div>
    {page_num("03")}
  </div>
""" + foot()


def generate_product(p: dict) -> str:
    feats = "".join(f'          <div class="feature-row"><span class="feature-dot"></span>{esc(f)}</div>\n' for f in p["features"])
    gallery = "".join(f'        <img src="{u}" alt="{esc(p["title"])}">\n' for u in p["gallery"])
    specs = "".join(
        f'          <div class="spec-item"><dt>{esc(s[0])}</dt><dd>{esc(s[1])}</dd></div>\n'
        for s in p["specs"]
    )
    models_html = ""
    if p.get("models"):
        chips = "".join(f'<span class="model-chip">{esc(m)}</span>' for m in p["models"])
        models_html = f"""
      <div class="product-models">
        <h3 class="heading-sm text-accent">Modeller</h3>
        <div class="model-chips">{chips}</div>
      </div>"""

    return head(p["title"]) + f"""
  <div class="page page--product">
    <div class="product-hero">
      <img src="{p['hero']}" alt="{esc(p['title'])}">
      <div class="product-hero-overlay">
        <span class="badge">{esc(p['badge'])}</span>
        <h1 class="heading-lg text-white">{esc(p['title'])}</h1>
        <p class="text-body text-white product-sub">{esc(p['subtitle'])}</p>
      </div>
    </div>
    <div class="product-body">
      <div class="product-desc">
        <h2 class="heading-md">{esc(p['heading'])}</h2>
        <p class="text-body">{esc(p['description'])}</p>
        <div class="product-features">{feats}        </div>
      </div>
      <div class="product-gallery">{gallery}      </div>
      <div class="product-specs">
        <h3 class="heading-sm text-accent">Teknik Özellikler</h3>
        <dl class="spec-grid">{specs}        </dl>
      </div>{models_html}
    </div>
    <div class="product-footer">
      {partners()}
      <p class="product-url"><a href="{p['url']}">{p['url'].replace('https://','')}</a></p>
    </div>
    {page_num(p['page'], 'right')}
  </div>
""" + foot()


def generate_references() -> str:
    r = DATA["references"]
    cards = ""
    for i, item in enumerate(r["items"]):
        cards += f"""
      <div class="ref-card">
        <img src="{item['image']}" alt="{esc(item['title'])}">
        <div class="ref-card-info">
          <p class="ref-location">{esc(item['location'])}</p>
          <h3 class="heading-sm">{esc(item['title'])}</h3>
        </div>
      </div>"""

  # First item full width hero style
    hero = r["items"][0]
    rest = r["items"][1:]

    grid = ""
    for item in rest:
        grid += f"""
        <div class="ref-card ref-card--sm">
          <img src="{item['image']}" alt="{esc(item['title'])}">
          <div class="ref-card-info">
            <p class="ref-location">{esc(item['location'])}</p>
          </div>
        </div>"""

    return head(r["title"]) + f"""
  <div class="page page--refs">
    <div class="refs-header">
      <h1 class="heading-lg text-white">{esc(r['title'])}</h1>
      <p class="text-body text-white refs-sub">{esc(r['subtitle'])}</p>
    </div>
    <div class="refs-hero">
      <img src="{hero['image']}" alt="{esc(hero['title'])}">
      <div class="refs-hero-overlay">
        <p class="ref-location text-white">{esc(hero['location'])}</p>
        <h2 class="heading-md text-white">{esc(hero['title'])}</h2>
      </div>
    </div>
    <div class="refs-grid">{grid}
    </div>
    {page_num(r['page'])}
  </div>
""" + foot()


def generate_back() -> str:
    c = DATA["contact"]
    offices = ""
    for o in c["offices"]:
        addr = "<br>".join(esc(line) for line in o["address"].split("\n"))
        offices += f"""
      <div class="office">
        <div class="office-flag">{o['flag']}</div>
        <h4>{esc(o['country'])}</h4>
        <p>{addr}<br><br>
          <a href="tel:{o['phone'].replace(' ','')}">{esc(o['phone'])}</a><br>
          <a href="https://{o['web']}">{esc(o['web'])}</a><br>
          {esc(o['email'])}
        </p>
      </div>"""

    return head("İletişim") + f"""
  <div class="page page--back">
    <div class="back-top"></div>
    <div class="back-main">
      <div class="logo">
        <div class="logo-icon"></div>
        <span class="logo-text">LEDAJANS</span>
      </div>
      <div class="world-map-wrap">
        <div class="chevrons-h"><div class="chevron-h"></div><div class="chevron-h"></div><div class="chevron-h"></div></div>
        <div class="world-map"><div class="world-dots"></div></div>
        <div class="chevrons-h"><div class="chevron-h"></div><div class="chevron-h"></div><div class="chevron-h"></div></div>
      </div>
      <div class="offices">{offices}
      </div>
    </div>
    <div class="back-bottom"></div>
  </div>
""" + foot()


def generate_index() -> str:
    pages = [
        ("01-kapak.html", "01 — Kapak"),
        ("02-tanitim.html", "02 — Kurumsal"),
        ("03-icindekiler.html", "03 — İçindekiler"),
    ]
    for p in DATA["products"]:
        pages.append((p["file"], f"{p['page']} — {p['title']}"))
    pages.append(("14-referanslar.html", "14 — Referanslar"))
    pages.append(("15-arka-kapak.html", "15 — İletişim"))

    nav = "\n".join(
        f'    <a href="#{f.replace(".html","")}"{" class=\"active\"" if i==0 else ""}>{label}</a>'
        for i, (f, label) in enumerate(pages)
    )
    iframes = "\n".join(
        f'    <iframe id="{f.replace(".html","")}" src="pages/{f}" title="{label}"></iframe>'
        for f, label in pages
    )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{DATA['meta']['title']}</title>
  <link rel="stylesheet" href="assets/katalog.css">
  <link rel="stylesheet" href="assets/viewer.css">
</head>
<body>
  <header class="viewer-header no-print">
    <h1><span>LEDA</span>JANS Katalog {DATA['meta']['year']}</h1>
    <div class="viewer-actions">
      <a class="btn btn-ghost" href="https://www.figma.com/design/nzwEECDoNRqekt8pUo5Jsl" target="_blank">Figma</a>
      <button class="btn btn-primary" onclick="window.print()">PDF İndir / Yazdır</button>
    </div>
  </header>
  <nav class="viewer-nav no-print">
    <h3>Sayfalar ({len(pages)})</h3>
{nav}
  </nav>
  <main class="viewer-content">
{iframes}
  </main>
  <script src="assets/viewer.js"></script>
</body>
</html>
"""


def main():
    PAGES.mkdir(parents=True, exist_ok=True)
    (PAGES / "01-kapak.html").write_text(generate_cover(), encoding="utf-8")
    (PAGES / "02-tanitim.html").write_text(generate_intro(), encoding="utf-8")
    (PAGES / "03-icindekiler.html").write_text(generate_toc(), encoding="utf-8")
    for p in DATA["products"]:
        (PAGES / p["file"]).write_text(generate_product(p), encoding="utf-8")
    (PAGES / "14-referanslar.html").write_text(generate_references(), encoding="utf-8")
    (PAGES / "15-arka-kapak.html").write_text(generate_back(), encoding="utf-8")
    (ROOT / "index.html").write_text(generate_index(), encoding="utf-8")
    print(f"OK: {len(list(PAGES.glob('*.html')))} sayfa + index.html üretildi")


if __name__ == "__main__":
    main()
