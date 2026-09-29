"""/dis-mekan-rgb-panel/ altındaki 5 model sayfasını aynı URL ile Elementor sayfası olarak oluşturur / günceller
(yerleşim: ledajans_model_layout). Aynı slug'lı eski düz yazılar (post) sayfa yayınlandıktan sonra çöpe taşınır.

python scripts/create-disrgb-model-pages.py            # dry-run: önizleme HTML + özet
python scripts/create-disrgb-model-pages.py --publish  # canlı: sayfa oluştur/güncelle, eski post'u çöpe at, cache purge
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import requests

from ledajans_model_layout import (
    ProductArea, adapt_hero, base_style, build_layout, find_page, page_meta, page_payload, purge_caches,
    render_product_area, upsert_page, word_count, wp_session, write_preview,
)

ROOT = Path(__file__).resolve().parents[1]
BK = ROOT / "AGENT-HUB/_tmp-kw-deploy-backup"
HERO_SRC = BK / "disrgb-3795/0-453da90.html"
STYLE_SRC = BK / "icrgb-5006/2-17346b2.html"
PREVIEW = BK / "disrgb-model-preview"
UA = "LEDAJANS-DISRGB-Models/1.0"
B = "https://ledajans.com/"
HUB = B + "dis-mekan-rgb-panel/"
IMAGE = "https://ledajans.com/wp-content/uploads/2026/04/dis-mekan-rgb-scaled.png"


@dataclass
class Model:
    slug: str
    code: str
    pitch: str
    density: str
    bright: str
    refresh: str
    scan: str | None = None
    spec_doc_url: str | None = None  # Google Drive teknik föy linki (sonra eklenecek)

    @property
    def name(self) -> str:
        return f"{self.code} Dış Mekan RGB LED Panel"

    @property
    def url(self) -> str:
        return f"{B}{self.slug}/"

    @property
    def specs(self) -> list[tuple[str, str]]:
        rows = [("Model", self.code), ("Piksel aralığı", self.pitch), ("Piksel yoğunluğu", self.density),
                ("Parlaklık", self.bright), ("Yenileme hızı", self.refresh)]
        if self.scan:
            rows.append(("Tarama", self.scan))
        return rows + [("Koruma sınıfı", "IP65"), ("Kullanım ortamı", "Dış mekan")]


MODELS: list[Model] = [
    Model("h2-5-dis-mekan-rgb-panel", "H2.5", "2.5 mm", "160.000 nokta/m²", "≥4500 cd/m²", "≥7680 Hz"),
    Model("h3-076-dis-mekan-rgb-panel", "H3.076", "3.076 mm", "105.625 nokta/m²", "≥4500 cd/m²", "≥7680 Hz"),
    Model("h4-dis-mekan-rgb-panel", "H4", "4 mm", "62.500 nokta/m²", "≥4500 cd/m²", "≥7680 Hz"),
    Model("h5-dis-mekan-rgb-panel", "H5", "5 mm", "40.000 nokta/m²", "≥4500 cd/m²", "≥7680 Hz"),
    Model("p10-4s-dis-mekan-rgb-panel", "P10 4S", "10 mm", "10.000 nokta/m²", "≥3500 cd/m²", "1920 / 3840 Hz", scan="4S (1/4 tarama)"),
]


def seo(m: Model) -> dict[str, str]:
    desc = f"{m.name}: {m.pitch} piksel aralığı, {m.density}, {m.bright} parlaklık, IP65. LEDAJANS'tan teknik föy ve fiyat teklifi alın."
    return {
        "rank_math_title": f"{m.name} | {m.pitch} IP65 | LEDAJANS",
        "rank_math_description": desc[:160],
        "rank_math_focus_keyword": f"{m.code.lower()} dış mekan rgb led panel,dış mekan rgb led panel",
    }


def hero(m: Model) -> str:
    return adapt_hero(
        HERO_SRC.read_text(encoding="utf-8"), name=m.name, url=m.url, hub_name="Dış Mekan RGB Panel", hub_url=HUB,
        subtitle_html=(
            f'<strong>{m.name}</strong> — {m.pitch}, IP65, teknik özellikler ve fiyat teklifi. '
            f'<a href="{HUB}" style="color:#fff;text-decoration:underline;">Tüm dış mekan RGB paneller</a> · '
            f'<a href="{B}iletisim/" style="color:#fff;text-decoration:underline;">Teklif alın</a>'
        ),
    )


def schema(m: Model) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": m.name,
        "description": seo(m)["rank_math_description"],
        "brand": {"@type": "Brand", "name": "LEDAJANS"},
        "manufacturer": {"@type": "Organization", "name": "LEDAJANS", "url": "https://ledajans.com"},
        "category": "Dış Mekan RGB LED Paneller",
        "url": m.url,
        "image": IMAGE,
        "additionalProperty": [{"@type": "PropertyValue", "name": k, "value": v} for k, v in m.specs],
    }


def product(m: Model) -> str:
    sib_links = ", ".join(f'<a href="{x.url}">{x.name}</a>' for x in MODELS if x.slug != m.slug)
    return render_product_area(base_style(STYLE_SRC.read_text(encoding="utf-8")), ProductArea(
        title=f"{m.name} Teknik Özellikleri",
        intro_html=(
            f'<strong>{m.name}</strong>, <a href="{B}">LEDAJANS</a> <a href="{HUB}">dış mekan RGB LED panel</a> serisinde {m.pitch} piksel aralığına sahip, '
            f"IP65 korumalı bir LED modüldür. {m.density} piksel yoğunluğu ve {m.bright} parlaklık değeriyle açık hava LED ekran uygulamaları için tasarlanmıştır."
        ),
        spec_title=f"{m.code} Teknik Değerler",
        specs=m.specs,
        spec_note_html=(
            "Modül ölçüsü, modül çözünürlüğü, ağırlık, güç tüketimi, sürüş/tarama modu ve kabin ölçüleri gibi ayrıntılı değerler ile ürün dökümanı için "
            f'<a href="{B}iletisim/">bizimle iletişime geçin</a>; projenize uygun teknik föyü paylaşalım.'
        ),
        usage_title="Kullanım Alanları",
        usage_html=(
            f"{m.name}; bina cephesi ve reklam panosu ekranları, AVM ve mağaza dış cepheleri, stadyum ve spor alanları ile meydan ekranları için uygundur. "
            "Güncel fiyat, stok durumu ve proje bazlı teknik destek için +90 212 220 40 04 numaralı hattı arayabilirsiniz."
        ),
        links_html=f'Diğer modeller: {sib_links}. Tüm modelleri karşılaştırmak için <a href="{HUB}">Dış Mekan RGB Panel</a> sayfasına göz atın.',
        ctas=[("p", f"{B}iletisim/", "Fiyat teklifi alın"), ("g", HUB, "Tüm dış mekan RGB paneller")],
        schema=schema(m),
        spec_doc_url=m.spec_doc_url,
    ))


def find_posts(s: requests.Session, site: str, slug: str) -> list[dict]:
    r = s.get(f"{site}/wp-json/wp/v2/posts", params={"slug": slug, "status": "publish,draft,private", "context": "edit", "_fields": "id,status,link"}, timeout=60)
    r.raise_for_status()
    return r.json()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    PREVIEW.mkdir(exist_ok=True)
    jobs = []
    for i, m in enumerate(MODELS):
        data, flat = build_layout(f"d{i}", hero(m), product(m))
        meta = page_meta(data, {**seo(m), "rank_math_robots": ["index", "follow"]})
        write_preview(PREVIEW / f"{m.slug}.html", m.name, flat)
        print(f"{m.slug}: title='{meta['rank_math_title']}' desc={len(meta['rank_math_description'])}ch words~{word_count(flat)}")
        jobs.append((m, page_payload(m.name, m.slug, flat, meta)))

    s, site = wp_session(UA)
    if not args.publish:
        for m, _ in jobs:
            print(m.slug, "page:", find_page(s, site, m.slug) or "-", "post:", find_posts(s, site, m.slug) or "-")
        print(f"DRY_RUN OK — önizleme: {PREVIEW}")
        return 0

    results = []
    for m, payload in jobs:
        action, body = upsert_page(s, site, payload)
        trashed = []
        for post in find_posts(s, site, m.slug):
            r = s.delete(f"{site}/wp-json/wp/v2/posts/{post['id']}", timeout=60)
            if r.status_code != 200:
                raise RuntimeError(f"post çöpe atılamadı {post['id']} {r.status_code} {r.text[:200]}")
            trashed.append(post["id"])
        results.append({"slug": m.slug, "page_id": body["id"], "link": body.get("link"), "trashed_posts": trashed})
        print(f"{action} {m.slug} page_id={body['id']} {body.get('link')} trashed_posts={trashed}")
    purge_caches(s, site, UA)
    (PREVIEW / "created.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
