from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSS = (ROOT / "SEO-Icerik-Widgets" / "blocks" / "la-kw-landing-styles.html").read_text(
    encoding="utf-8"
).strip()
URLS = json.loads(
    (Path(__file__).resolve().parent / "media-urls.json").read_text(encoding="utf-8")
)

U = {k: v for k, v in URLS.items() if not k.endswith(":id")}
EXISTING = {
    "ic": "https://ledajans.com/wp-content/uploads/2026/09/ic-mekan-led-ekran-fiyatlari.webp",
    "gob_blog": "https://ledajans.com/wp-content/uploads/2026/09/gob-led-ekran.webp",
    "rental_price": "https://ledajans.com/wp-content/uploads/2026/09/rental-led-ekran-kiralama.webp",
}
WA = "https://wa.me/905438795108"


def img(src: str, alt: str) -> str:
    return (
        f'<img src="{src}" alt="{alt}" width="1280" height="720" '
        f'loading="lazy" decoding="async">'
    )


def wrap_style(html: str) -> str:
    return re.sub(
        r"<style>.*?</style>",
        "<style>\n" + CSS + "\n</style>",
        html,
        count=1,
        flags=re.S,
    )


def wrap_hero_actions(html: str) -> str:
    if "la-kw-actions" in html:
        return html
    html = html.replace(
        '    <a class="la-kw-btn la-kw-btn-p"',
        '    <div class="la-kw-actions">\n    <a class="la-kw-btn la-kw-btn-p"',
        1,
    )
    # close after second hero button (outline), before </header>
    html = re.sub(
        r'(<a class="la-kw-btn la-kw-btn-o" href="[^"]+">[^<]+</a>)\s*</header>',
        rf'\1\n    <a class="la-kw-btn la-kw-btn-o" href="{WA}">WhatsApp teklif</a>\n    </div>\n  </header>',
        html,
        count=1,
    )
    return html


def add_sec_h2(html: str, title: str) -> str:
    if "la-kw-sec" in html:
        return html
    return html.replace(
        '  <div class="la-kw-grid">',
        f'  <h2 class="la-kw-sec">{title}</h2>\n  <div class="la-kw-grid">',
        1,
    )


def wrap_tables(html: str) -> str:
    if "la-kw-table-wrap" in html:
        return html
    html = html.replace("<table>", '<div class="la-kw-table-wrap">\n  <table>', 1)
    html = html.replace("</table>", "</table>\n  </div>", 1)
    return html


def inject_image_ld(html: str, page_url: str, name: str, img_url: str, caption: str) -> str:
    m = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', html, re.S)
    if not m:
        return html
    faq = json.loads(m.group(1))
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": f"{page_url}#webpage",
                "url": page_url,
                "name": name,
                "inLanguage": "tr-TR",
                "primaryImageOfPage": {"@id": f"{img_url}#primary"},
            },
            {
                "@type": "ImageObject",
                "@id": f"{img_url}#primary",
                "url": img_url,
                "contentUrl": img_url,
                "width": 1280,
                "height": 720,
                "caption": caption,
                "inLanguage": "tr-TR",
            },
            {k: v for k, v in faq.items() if k != "@context"},
        ],
    }
    new = (
        '<script type="application/ld+json">\n'
        + json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
        + "\n</script>"
    )
    return html[: m.start()] + new + html[m.end() :]


def replace_imgs(html: str, triples: list[tuple[str, str]]) -> str:
    parts = re.split(r"<img\b[^>]*>", html)
    if len(parts) - 1 != len(triples):
        raise SystemExit(f"img count {len(parts)-1} != {len(triples)}")
    out = parts[0]
    for i, (src, alt) in enumerate(triples):
        out += img(src, alt) + parts[i + 1]
    return out


PAGES = [
    (
        ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/cephe-led-ekran.html",
        "https://ledajans.com/cephe-led-ekran/",
        "Cephe LED ekran",
        U["cephe-led-ekran-bina.webp"],
        "Cephe LED ekran IP65 bina uygulaması",
        "Cephe senaryoları",
        [
            (U["cephe-led-ekran-bina.webp"], "Cephe LED ekran IP65 bina uygulaması"),
            (U["led-billboard-otoyol.webp"], "LED billboard otoyol panosu"),
            (U["istanbul-cephe-led-kurulum.webp"], "İstanbul cephe LED ekran kurulum"),
        ],
    ),
    (
        ROOT / "SEO-Icerik-Widgets/temel-rehberler/pitch-secim-rehberi.html",
        "https://ledajans.com/pitch-secim-rehberi/",
        "LED ekran pitch seçim rehberi",
        U["pitch-dis-mekan-p10.webp"],
        "P4 P10 dış mekan LED ekran pitch seçimi",
        "Pitch ailesi",
        [
            (U["cob-led-lobi.webp"], "P2 P2.5 P3 iç mekan LED ekran"),
            (U["pitch-dis-mekan-p10.webp"], "P4 P5 P6 P8 P10 dış mekan LED ekran"),
            (U["rental-led-sahne.webp"], "P2.6 rental LED ekran sahne"),
        ],
    ),
    (
        ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/gob-led-ekran.html",
        "https://ledajans.com/gob-led-ekran/",
        "GOB LED ekran",
        U["gob-led-yuzey.webp"],
        "GOB LED ekran Glue on Board yüzey",
        "GOB seçenekleri",
        [
            (U["gob-led-yuzey.webp"], "GOB LED ekran Glue on Board yüzey"),
            (U["cob-led-lobi.webp"], "COB LED ekran lobi karşılaştırması"),
            (EXISTING["gob_blog"], "GOB LED nedir teknik özet"),
        ],
    ),
    (
        ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/fuar-led-ekran.html",
        "https://ledajans.com/fuar-led-ekran/",
        "Fuar LED ekran",
        U["fuar-led-stand.webp"],
        "Fuar LED ekran stand duvarı",
        "Fuar senaryoları",
        [
            (U["fuar-led-stand.webp"], "Fuar LED ekran stand duvarı"),
            (EXISTING["rental_price"], "Fuar LED ekran kiralama fiyatı"),
            (U["fuar-fuaye-led.webp"], "Sabit fuar salonu LED ekran"),
        ],
    ),
    (
        ROOT / "SEO-Icerik-Widgets/sektor-rehberleri/magaza-vitrin-led-rehberi.html",
        "https://ledajans.com/magaza-vitrin-led-ekran/",
        "Mağaza ve vitrin LED ekran",
        U["magaza-vitrin-led.webp"],
        "Mağaza vitrin LED ekran",
        "Mağaza senaryoları",
        [
            (U["magaza-vitrin-led.webp"], "Mağaza vitrin LED ekran"),
            (U["avm-led-ekran.webp"], "AVM LED ekran atrium"),
            (U["gob-led-yuzey.webp"], "GOB korumalı vitrin LED ekran"),
        ],
    ),
    (
        ROOT / "SEO-Icerik-Widgets/sehir-sayfalari/istanbul-led-ekran.html",
        "https://ledajans.com/istanbul-led-ekran/",
        "İstanbul LED ekran",
        U["istanbul-cephe-led-kurulum.webp"],
        "İstanbul cephe LED ekran kurulum",
        "İstanbul senaryoları",
        [
            (U["magaza-vitrin-led.webp"], "İstanbul mağaza LED ekran"),
            (U["cephe-led-ekran-bina.webp"], "İstanbul cephe LED ekran"),
            (U["rental-led-sahne.webp"], "İstanbul LED ekran kiralama"),
        ],
    ),
]


def main() -> None:
    for path, page_url, name, primary, caption, sec, triples in PAGES:
        html = path.read_text(encoding="utf-8")
        html = wrap_style(html)
        html = inject_image_ld(html, page_url, name, primary, caption)
        html = wrap_hero_actions(html)
        html = add_sec_h2(html, sec)
        html = replace_imgs(html, triples)
        html = wrap_tables(html)
        path.write_text(html, encoding="utf-8")
        print("OK", path.name, "imgs", html.count("<img "), "wa", WA in html)


if __name__ == "__main__":
    main()
