"""7 rental model sayfasını eski slug'larıyla oluşturur / günceller (yerleşim: ledajans_model_layout).

python scripts/create-rental-model-pages.py            # dry-run: önizleme HTML + özet
python scripts/create-rental-model-pages.py --publish  # canlı: sayfa oluştur/güncelle + cache purge
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ledajans_model_layout import (
    ProductArea, adapt_hero, base_style, build_layout, find_page, page_meta, page_payload, purge_caches,
    render_product_area, upsert_page, word_count, wp_session, write_preview,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "AGENT-HUB/_tmp-kw-deploy-backup/rental-5004"
PREVIEW = ROOT / "AGENT-HUB/_tmp-kw-deploy-backup/rental-model-preview"
UA = "LEDAJANS-Rental-Models/1.0"
HUB = "https://ledajans.com/rental-ekran/"


@dataclass
class Model:
    slug: str
    pitch: str
    pitch_mm: str
    env: str  # "ic" | "dis"
    specs: list[tuple[str, str]]
    missing: list[str] = field(default_factory=list)
    spec_doc_url: str | None = None  # Google Drive teknik föy linki (sonra eklenecek)

    @property
    def env_label(self) -> str:
        return "İç Mekan" if self.env == "ic" else "Dış Mekan"

    @property
    def name(self) -> str:
        return f"{self.pitch} {self.env_label} Rental LED Ekran"

    @property
    def url(self) -> str:
        return f"https://ledajans.com/{self.slug}/"


MODELS: list[Model] = [
    Model("p1-9-ic-mekan-rental-led-ekran", "P1.9", "1,953", "ic", [
        ("Piksel aralığı", "1,953 mm"), ("Piksel yoğunluğu", "262.144 nokta/m²"), ("LED tipi", "SMD1515"),
        ("Tarama", "1/32"), ("Parlaklık", "2600 cd/m²"), ("Yenileme hızı", "3840 Hz"),
    ]),
    Model("p2-6-ic-mekan-rental-led-ekran", "P2.6", "2,604", "ic", [
        ("Piksel aralığı", "2,604 mm"), ("Piksel yoğunluğu", "147.456 nokta/m²"), ("Tarama", "1/32"),
        ("Parlaklık", "≥1200 cd/m²"), ("Yenileme hızı", "1920 / 3840 Hz"), ("Maksimum güç", "≤650 W/m²"),
    ], missing=["LED tipi (SMD)"]),
    Model("p2-9-ic-mekan-rental-led-ekran", "P2.9", "2,976", "ic", [
        ("Piksel aralığı", "2,976 mm"), ("Piksel yoğunluğu", "112.896 nokta/m²"), ("LED tipi", "SMD2121"),
        ("Tarama", "1/28"), ("Parlaklık", "≥1000 cd/m²"), ("Yenileme hızı", "3840 Hz"),
    ]),
    Model("p3-9-ic-mekan-rental-led-ekran", "P3.9", "3,91", "ic", [
        ("Piksel aralığı", "3,91 mm"), ("Piksel yoğunluğu", "65.536 nokta/m²"), ("Tarama", "1/16"),
        ("Parlaklık", "2800 cd/m²"), ("Kontrast", "5000:1"), ("Yenileme hızı", "3840 Hz"),
    ], missing=["LED tipi (SMD)"]),
    Model("p2-6-dis-mekan-rental-led-ekran", "P2.6", "2,604", "dis", [
        ("Piksel aralığı", "2,604 mm"), ("Piksel yoğunluğu", "147.456 nokta/m²"), ("LED tipi", "SMD1415"),
        ("Tarama", "1/24"), ("Parlaklık", "≥4500 cd/m²"), ("Yenileme hızı", "3840 Hz"),
    ]),
    Model("p2-9-dis-mekan-rental-led-ekran", "P2.9", "2,976", "dis", [
        ("Piksel aralığı", "2,976 mm"), ("Piksel yoğunluğu", "112.896 nokta/m²"), ("LED tipi", "SMD1415"),
        ("Tarama", "1/21"), ("Parlaklık", "≥4500 cd/m²"), ("Yenileme hızı", "3840 Hz"),
    ]),
    Model("p3-9-dis-mekan-rental-led-ekran", "P3.9", "3,91", "dis", [
        ("Piksel aralığı", "3,91 mm"), ("Piksel yoğunluğu", "65.536 nokta/m²"), ("LED tipi", "SMD1921"),
        ("Tarama", "1/16"), ("Parlaklık", "≥4500 cd/m²"), ("Yenileme hızı", "3840 Hz"),
    ]),
]

FOCUS = {
    ("P1.9", "ic"): "p1.9 iç mekan rental led ekran",
    ("P2.6", "ic"): "p2.6 iç mekan rental led ekran",
    ("P2.9", "ic"): "p2.9 iç mekan rental led ekran",
    ("P3.9", "ic"): "p3.9 iç mekan rental led ekran",
    ("P2.6", "dis"): "p2.6 dış mekan rental led ekran",
    ("P2.9", "dis"): "p2.9 dış mekan rental led ekran",
    ("P3.9", "dis"): "p3.9 dış mekan rental led ekran",
}

USAGE = {
    "ic": "konferans salonu, kurumsal lansman, fuar standı, stüdyo ve kapalı alan sahne kurulumları",
    "dis": "açık hava konserleri, festival sahneleri, stadyum ve meydan etkinlikleri, açık alan fuar ve lansmanlar",
}


def src(section_idx: str) -> str:
    return next(SRC.glob(f"{section_idx}-*.html")).read_text(encoding="utf-8")


def seo_desc(m: Model) -> str:
    spec = dict(m.specs)
    bits = [spec["Piksel yoğunluğu"], spec["Parlaklık"]]
    return f"{m.name}: {', '.join(bits)}, {spec['Yenileme hızı']}. Konser, fuar ve etkinlik kiralama/satış için LEDAJANS'tan teklif alın."[:158]


def hero(m: Model) -> str:
    return adapt_hero(
        src("0"), name=m.name, url=m.url, hub_name="Rental Ekran", hub_url=HUB,
        subtitle_html=(
            f'<strong>{m.pitch} {m.env_label.lower()} rental LED ekran</strong> — '
            'konser, fuar ve etkinlikler için kiralık ve satılık kabin. '
            f'<a href="{HUB}" style="color:#fff;text-decoration:underline;">Tüm rental modeller</a> · '
            '<a href="https://ledajans.com/iletisim/" style="color:#fff;text-decoration:underline;">Teklif alın</a>'
        ),
    )


def schema(m: Model) -> dict:
    props = [{"@type": "PropertyValue", "name": k, "value": v} for k, v in m.specs]
    props.append({"@type": "PropertyValue", "name": "Kasa Yapısı", "value": "Die-Cast Alüminyum"})
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": m.name,
        "description": seo_desc(m),
        "brand": {"@type": "Brand", "name": "LEDAJANS"},
        "manufacturer": {"@type": "Organization", "name": "LEDAJANS", "url": "https://ledajans.com"},
        "category": "Rental LED Ekran",
        "url": m.url,
        "image": "https://ledajans.com/wp-content/uploads/2022/12/rentalkabin-600x540.png",
        "offers": {
            "@type": "AggregateOffer", "priceCurrency": "TRY", "lowPrice": "0", "highPrice": "0", "offerCount": "1",
            "availability": "https://schema.org/InStock",
            "seller": {"@type": "Organization", "name": "LEDAJANS", "url": "https://ledajans.com"},
            "url": "https://ledajans.com/iletisim/",
        },
        "additionalProperty": props,
    }


def product(m: Model) -> str:
    siblings = [x for x in MODELS if x.env == m.env and x.slug != m.slug]
    sib_links = ", ".join(f'<a href="{x.url}">{x.name}</a>' for x in siblings)
    other_env = "dış mekan" if m.env == "ic" else "iç mekan"
    env_text = (
        "Kapalı alanda yakın izleme mesafesinde net görüntü gerektiren projeler için tasarlanmıştır."
        if m.env == "ic"
        else "Yüksek parlaklığı sayesinde gün ışığında da okunaklı görüntü verir; açık alan etkinlikleri için tasarlanmıştır."
    )
    near = int(m.pitch_mm.split(",")[0])
    return render_product_area(base_style(src("2")), ProductArea(
        title=f"{m.name} Teknik Özellikleri",
        intro_html=(
            f"<strong>{m.pitch} {m.env_label.lower()} rental LED ekran</strong>, {m.pitch_mm} mm piksel aralığına sahip, die-cast alüminyum kasalı kiralık LED ekran kabinidir.\n"
            f'        {env_text} <a href="https://ledajans.com/">LEDAJANS</a> bu modeli etkinlik bazlı kiralama ve proje bazlı satış seçenekleriyle sunar;\n'
            "        kurulum, söküm ve etkinlik süresince teknik destek hizmete dahildir."
        ),
        spec_title=f"{m.pitch} Teknik Değerler",
        specs=m.specs,
        spec_note_html=(
            f"Genel bir kural olarak piksel aralığı (mm) kadar metre, rahat izleme için önerilen minimum mesafeyi verir; {m.pitch} için bu yaklaşık {near}–{near + 1} metredir.\n"
            "        Ekran ölçüsü, kabin adedi ve proje detayları için keşif sonrası net teklif hazırlanır."
        ),
        usage_title="Kullanım Alanları",
        usage_html=f"{m.name}; {USAGE[m.env]} için uygundur. Modüler kabin yapısı sayesinde farklı ölçülerde duvar ekran, sahne arkası ve yan ekran kurulumları yapılabilir.",
        links_html=(
            f'Diğer modeller: {sib_links}. {other_env.capitalize()} seçenekleri ve tüm karşılaştırma için <a href="{HUB}">Rental Ekran</a> sayfasına,\n'
            '          fiyat aralıkları için <a href="https://ledajans.com/rental-led-ekran-kiralama-fiyatlari-2026/">LED ekran kiralama fiyatları 2026</a> rehberine göz atın.'
        ),
        ctas=[("p", "https://ledajans.com/iletisim/", "Fiyat teklifi alın"), ("g", HUB, "Tüm rental modeller")],
        schema=schema(m),
        spec_doc_url=m.spec_doc_url,
    ))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    PREVIEW.mkdir(exist_ok=True)
    jobs = []
    for i, m in enumerate(MODELS):
        data, flat = build_layout(f"r{i}", hero(m), product(m))
        meta = page_meta(data, {
            "rank_math_title": f"{m.name} | LEDAJANS",
            "rank_math_description": seo_desc(m),
            "rank_math_focus_keyword": f"{FOCUS[(m.pitch, m.env)]},{m.pitch.lower()} rental led ekran,rental led ekran",
        })
        write_preview(PREVIEW / f"{m.slug}.html", m.name, flat)
        print(f"{m.slug}: title='{meta['rank_math_title']}' desc={len(meta['rank_math_description'])}ch words~{word_count(flat)} missing={m.missing or '-'}")
        jobs.append((m, page_payload(m.name, m.slug, flat, meta)))

    s, site = wp_session(UA)
    if not args.publish:
        for m, _ in jobs:
            ex = find_page(s, site, m.slug)
            print("mevcut" if ex else "yeni", m.slug, ex or "")
        print(f"DRY_RUN OK — önizleme: {PREVIEW}")
        return 0

    results = []
    for m, payload in jobs:
        action, body = upsert_page(s, site, payload)
        results.append((m.slug, body["id"], body.get("link")))
        print(f"{action} {m.slug} id={body['id']} {body.get('link')}")
    purge_caches(s, site, UA)
    (PREVIEW / "created.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
