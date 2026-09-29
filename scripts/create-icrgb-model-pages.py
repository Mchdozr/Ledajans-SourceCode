"""/ic-mekan-rgb-panel/ altındaki 18 model sayfasını eski slug'larıyla oluşturur / günceller (yerleşim: ledajans_model_layout).

python scripts/create-icrgb-model-pages.py            # dry-run: önizleme HTML + özet
python scripts/create-icrgb-model-pages.py --publish  # canlı: sayfa oluştur/güncelle + cache purge
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
SRC = ROOT / "AGENT-HUB/_tmp-kw-deploy-backup/icrgb-5006"
PREVIEW = ROOT / "AGENT-HUB/_tmp-kw-deploy-backup/icrgb-model-preview"
UA = "LEDAJANS-ICRGB-Models/1.0"
HUB = "https://ledajans.com/ic-mekan-rgb-panel/"
IMG = {
    "1.25": "https://ledajans.com/wp-content/uploads/2022/12/P1.25-I-1.jpg",
    "1.53": "https://ledajans.com/wp-content/uploads/2022/12/P1.53-I-1.jpg",
    "1.86": "https://ledajans.com/wp-content/uploads/2022/12/P1.86-I-1.jpg",
}
STD_FIELDS = ["LED tipi", "Tarama", "Yenileme hızı", "Parlaklık", "Modül ölçüsü", "Modül çözünürlüğü", "Maksimum güç"]


@dataclass
class Model:
    slug: str
    name: str
    code: str
    group: str  # "rgb" | "gob" | "flex"
    pitch_m: float
    specs: list[tuple[str, str]]
    missing: list[str] = field(default_factory=list)
    spec_doc_url: str | None = None  # Google Drive teknik föy linki (sonra eklenecek)

    @property
    def url(self) -> str:
        return f"https://ledajans.com/{self.slug}/"

    @property
    def focus(self) -> str:
        return self.name.lower().replace("i̇", "i").replace("İ", "i")

    @property
    def has_ip65(self) -> bool:
        return any(v == "IP65" for _, v in self.specs)


def M(slug: str, name: str, code: str, group: str, pitch_m: float, specs: list[tuple[str, str]]) -> Model:
    keys = {k for k, _ in specs}
    return Model(slug, name, code, group, pitch_m, specs, [f for f in STD_FIELDS if f not in keys])


PA, PY, LT, TR, YH, KS = "Piksel aralığı", "Piksel yoğunluğu", "LED tipi", "Tarama", "Yenileme hızı", "Koruma sınıfı"
MODELS: list[Model] = [
    M("p0-93-ic-mekan-led-ekran", "P0.93 İç Mekan RGB Panel", "P0.93", "rgb", 1.86, [
        (PA, "Dinamik 0,93 mm / Gerçek 1,86 mm"), (PY, "577.812 nokta/m²"), (YH, "≥3840 Hz")]),
    M("h1-25-ic-mekan-rgb-panel", "H1.25 İç Mekan RGB Panel", "H1.25", "rgb", 1.25, [
        (PA, "1,25 mm"), (PY, "640.000 nokta/m²"), (LT, "SMD1010"), (TR, "1/64")]),
    M("h1-53-ic-mekan-rgb-led-panel", "H1.53 İç Mekan RGB Panel", "H1.53", "rgb", 1.53, [
        (PA, "1,53 mm"), (PY, "422.500 nokta/m²"), (LT, "SMD1212"), (YH, "≥3840 Hz")]),
    M("h1-86-ic-mekan-rgb-led-panel", "H1.86 İç Mekan RGB Panel", "H1.86", "rgb", 1.86, [
        (PA, "1,86 mm"), (PY, "288.906 nokta/m²"), (LT, "SMD1515"), (YH, "≥3840 Hz")]),
    M("p2-5-ic-mekan-rgb-panel", "P2.5 1920Hz İç Mekan RGB Panel", "P2.5 1920Hz", "rgb", 2.5, [
        (PA, "2,5 mm"), (PY, "160.000 piksel/m²"), (LT, "SMD2121 / SMD2020"), (YH, "≥1920 Hz"), (KS, "IP65")]),
    M("p2-5-3840hz-ic-mekan-rgb-panel", "P2.5 3840Hz İç Mekan RGB Panel", "P2.5 3840Hz", "rgb", 2.5, [
        (PA, "2,5 mm"), (PY, "160.000 nokta/m²"), (LT, "SMD1515"), (YH, "≥3840 Hz"), (TR, "1/64")]),
    M("h2-5-6000-hz-ic-mekan-rgb-panel", "H2.5 6000Hz İç Mekan RGB Panel", "H2.5 6000Hz", "rgb", 2.5, [
        (PA, "2,5 mm"), (PY, "160.000 nokta/m²"), (YH, "≥6000 Hz"), ("Gri seviye", "14 bit"), ("Kamera uyumu", "Kamera çekimlerine uyumlu")]),
    M("p3-07-ic-mekan-rgb-panel", "P3.07 İç Mekan RGB Panel", "P3.07", "rgb", 3.076, [
        (PA, "3,076 mm"), (PY, "105.625 nokta/m²"), (LT, "SMD2020"), (YH, "≥3840 Hz"), (TR, "1/26")]),
    M("p4-ic-mekan-rgb-panel", "P4 İç Mekan RGB Panel", "P4", "rgb", 4.0, [
        (PA, "4 mm"), (PY, "62.500 nokta/m²"), (LT, "SMD2121"), (YH, "≥1920 Hz"), (TR, "1/20")]),
    M("p0-93-3840hz-gob-ic-mekan-rgb-panel", "P0.93 3840Hz GOB İç Mekan RGB Panel", "P0.93 GOB", "gob", 1.86, [
        (PA, "Dinamik 0,93 mm / Gerçek 1,86 mm"), (PY, "577.812 nokta/m²"), (LT, "SMD1617 RGGB"), (YH, "≥3840 Hz"), (KS, "IP65")]),
    M("p1-25-6000hz-gob-ic-mekan-rgb-led-panel", "P1.25 GOB İç Mekan RGB Panel", "P1.25 GOB", "gob", 1.25, [
        (PA, "1,25 mm"), (PY, "640.000 piksel/m²"), (LT, "SMD1010"), (YH, "≥6000 Hz"), ("Arayüz", "HUB320"), (KS, "IP65")]),
    M("p1-53-6000hz-gob-ic-mekan-rgb-led-panel", "P1.53 GOB İç Mekan RGB Panel", "P1.53 GOB", "gob", 1.53, [
        (PA, "1,53 mm"), (PY, "422.500 piksel/m²"), (LT, "SMD1212"), (YH, "≥6000 Hz"), ("Arayüz", "HUB75"), (KS, "IP65")]),
    M("p1-86-6000hz-gob-ic-mekan-rgb-led-panel", "P1.86 GOB İç Mekan RGB Panel", "P1.86 GOB", "gob", 1.86, [
        (PA, "1,86 mm"), (PY, "288.906 piksel/m²"), (LT, "SMD1515"), (YH, "≥6000 Hz"), ("Arayüz", "HUB75"), (KS, "IP65")]),
    M("p2-5-gob-ic-mekan-rgb-led-panel", "P2.5 GOB İç Mekan RGB Panel", "P2.5 GOB", "gob", 2.5, [
        (PA, "2,5 mm"), (PY, "160.000 piksel/m²"), (LT, "SMD1515 / SMD2020"), (YH, "≥3840 Hz / ≥6000 Hz"), (TR, "1/32"), (KS, "IP65")]),
    M("q1-25-ic-mekan-flexible-led-panel", "Q1.25 Flexible İç Mekan LED Panel", "Q1.25", "flex", 1.25, [
        (PA, "1,25 mm"), (PY, "640.000 nokta/m²"), (LT, "SMD1010"), ("Arayüz", "HUB320"), ("Bükülme açısı", "150°~180°"), ("Kalınlık", "7,5 mm")]),
    M("q1-53-ic-mekan-flexible-led-panel", "Q1.53 Flexible İç Mekan LED Panel", "Q1.53", "flex", 1.53, [
        (PA, "1,53 mm"), (PY, "422.500 nokta/m²"), (LT, "SMD1212"), ("Arayüz", "HUB75"), ("Bükülme açısı", "150°~180°"), ("Kalınlık", "7,5 mm")]),
    M("q1-86-ic-mekan-flexible-led-panel", "Q1.86 Flexible İç Mekan LED Panel", "Q1.86", "flex", 1.86, [
        (PA, "1,86 mm"), (PY, "288.906 nokta/m²"), (LT, "SMD1515"), ("Arayüz", "HUB75"), ("Bükülme açısı", "150°~180°"), ("Kalınlık", "7,5 mm")]),
    M("q2-5-ic-mekan-flexible-led-panel", "Q2.5 Flexible İç Mekan LED Panel", "Q2.5", "flex", 2.5, [
        (PA, "2,5 mm"), (PY, "160.000 nokta/m²"), (LT, "SMD1515"), ("Arayüz", "HUB75"), ("Bükülme açısı", "150°~180°"), ("Kalınlık", "7,5 mm"), ("Parlaklık", "≥400 cd/m²")]),
]

GROUP = {
    "rgb": {
        "label": "İç Mekan RGB LED Paneller",
        "intro": "SMD LED'li, tam renkli (RGB) iç mekan LED modülüdür",
        "usage": "toplantı odası, mağaza, AVM, lobi, kontrol odası, stüdyo ve poster/raket LED ekran",
        "extra": '<a href="https://ledajans.com/ic-mekan-led-ekran/">İç mekan LED ekran</a> ve <a href="https://ledajans.com/pitch-secim-rehberi/">pitch seçim rehberi</a>',
    },
    "gob": {
        "label": "İç Mekan RGB GOB LED Paneller",
        "intro": "GOB (Glue on Board) kapsülleme ile üretilmiş iç mekan RGB LED modülüdür; LED yüzeyini kaplayan koruyucu tabaka darbe, toz ve neme karşı ek dayanım sağlar",
        "usage": "yoğun insan trafiği olan AVM ve mağazalar, fuar standları, kiralama projeleri ve dokunmaya açık iç mekan alanları",
        "extra": '<a href="https://ledajans.com/gob-led-ekran/">GOB LED ekran</a> ve <a href="https://ledajans.com/gob-led-nedir/">GOB LED nedir?</a>',
    },
    "flex": {
        "label": "İç Mekan Flexible LED Paneller",
        "intro": "silikon kılıf ve esnek PCB ile üretilmiş bükülebilir (flexible) iç mekan LED modülüdür",
        "usage": "kavisli ve silindirik kolonlar, dalga formlu yüzeyler, mağaza dekorasyonu ve sahne tasarımı",
        "extra": '<a href="https://ledajans.com/ic-mekan-led-ekran/">İç mekan LED ekran</a> ve <a href="https://ledajans.com/pitch-secim-rehberi/">pitch seçim rehberi</a>',
    },
}


def src(name: str) -> str:
    return (SRC / name).read_text(encoding="utf-8")


def image(m: Model) -> str:
    for k, v in IMG.items():
        if k in m.code:
            return v
    return IMG["1.86"]


def seo_desc(m: Model) -> str:
    spec = dict(m.specs)
    bits = [spec[PY]] + [spec[k] for k in (LT, YH) if k in spec]
    return f"{m.name}: {', '.join(bits)}. Teknik özellikler, döküman ve fiyat teklifi için LEDAJANS ile iletişime geçin."[:158]


def hero(m: Model) -> str:
    return adapt_hero(
        src("0-987596b.html"), name=m.name, url=m.url, hub_name="İç Mekan RGB Panel", hub_url=HUB,
        subtitle_html=(
            f'<strong>{m.name}</strong> — teknik özellikler ve fiyat teklifi. '
            f'<a href="{HUB}" style="color:#fff;text-decoration:underline;">Tüm iç mekan RGB paneller</a> · '
            '<a href="https://ledajans.com/iletisim/" style="color:#fff;text-decoration:underline;">Teklif alın</a>'
        ),
    )


def schema(m: Model) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": m.name,
        "description": seo_desc(m),
        "brand": {"@type": "Brand", "name": "LEDAJANS"},
        "manufacturer": {"@type": "Organization", "name": "LEDAJANS", "url": "https://ledajans.com"},
        "category": GROUP[m.group]["label"],
        "url": m.url,
        "image": image(m),
        "additionalProperty": [{"@type": "PropertyValue", "name": k, "value": v} for k, v in m.specs],
    }


def product(m: Model) -> str:
    g = GROUP[m.group]
    siblings = [x for x in MODELS if x.group == m.group and x.slug != m.slug]
    sib_links = ", ".join(f'<a href="{x.url}">{x.name}</a>' for x in siblings)
    dist = f"{m.pitch_m:.1f}".replace(".", ",").replace(",0", "")
    return render_product_area(base_style(src("2-17346b2.html")), ProductArea(
        title=f"{m.name} Teknik Özellikleri",
        intro_html=(
            f'<strong>{m.name}</strong>, {g["intro"]}. <a href="https://ledajans.com/">LEDAJANS</a> bu modeli\n'
            "        LED ekran üretimi, toptan modül satışı ve anahtar teslim proje kapsamında sunar; kasa, kontrol kartı ve güç kaynağı seçimi\n"
            "        projeye göre birlikte planlanır."
        ),
        spec_title=f"{m.code} Teknik Değerler",
        specs=m.specs,
        spec_note_html=(
            f"Genel bir kural olarak piksel aralığı (mm) kadar metre, rahat izleme için önerilen minimum mesafeyi verir; {m.code} için bu yaklaşık {dist} metre ve üzeridir.\n"
            "        Listelenmeyen değerler (modül ölçüsü, parlaklık, güç tüketimi vb.) tedarik partisine göre değişebildiği için teklif aşamasında ürün dökümanıyla birlikte paylaşılır."
        ),
        usage_title="Kullanım Alanları",
        usage_html=f"{m.name}; {g['usage']} projeleri için uygundur. Ekran ölçüsü, modül adedi ve montaj detayları için keşif sonrası net teklif hazırlanır.",
        links_html=(
            f'Aynı serideki diğer modeller: {sib_links}. Tüm modelleri karşılaştırmak için <a href="{HUB}">İç Mekan RGB Panel</a> sayfasına,\n'
            f"          ilgili rehberler için {g['extra']} sayfalarına göz atın."
        ),
        ctas=[("p", "https://ledajans.com/iletisim/", "Fiyat teklifi alın"), ("g", HUB, "Tüm iç mekan RGB paneller")],
        schema=schema(m),
        spec_doc_url=m.spec_doc_url,
    ))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    focuses = [m.focus for m in MODELS]
    assert len(set(focuses)) == len(focuses), "focus keyword tekrarı"
    assert len({m.slug for m in MODELS}) == 18

    PREVIEW.mkdir(exist_ok=True)
    jobs = []
    missing_report = {}
    for i, m in enumerate(MODELS):
        data, flat = build_layout(f"i{i:02d}", hero(m), product(m))
        meta = page_meta(data, {
            "rank_math_title": f"{m.name} | LEDAJANS",
            "rank_math_description": seo_desc(m),
            "rank_math_focus_keyword": m.focus,
            "rank_math_robots": ["index", "follow"],
        })
        write_preview(PREVIEW / f"{m.slug}.html", m.name, flat)
        missing_report[m.slug] = m.missing
        print(f"{m.slug}: focus='{m.focus}' desc={len(meta['rank_math_description'])}ch words~{word_count(flat)} missing={m.missing}")
        jobs.append((m, page_payload(m.name, m.slug, flat, meta)))
    (PREVIEW / "missing.json").write_text(json.dumps(missing_report, ensure_ascii=False, indent=2), encoding="utf-8")

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
        (PREVIEW / "created.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    purge_caches(s, site, UA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
