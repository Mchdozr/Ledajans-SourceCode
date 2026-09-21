#!/usr/bin/env python3
"""TR→EN/DE glossary, Elementor/HTML çeviri, iç link ve slug eşlemesi."""
from __future__ import annotations

import html as html_lib
import json
import re
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

ORIGIN = "https://ledajans.com"
LANGS = ("en", "de")

SKIP_PAGE_SLUGS = {
    "teknik-destek-videolari-2",
}
SKIP_POST_SLUGS = {
    "led-ekran-4",
    "led-ekran-5",
    "led-ekran-6",
    "led-ekran-7",
    "led-ekran-9",
    "led-led-ekran",
    "p10-panel-kirmizi-3",
    "p10-panel-kirmizi-4",
    "p10-panel-kirmizi-5",
    "p10-kirmizi-panel-2",
}

PILOT_PAGES = [
    "tr-2",
    "led-ekran",
    "ic-mekan-led-ekran",
    "dis-mekan-led-ekran",
    "rental-ekran",
    "cob-ekran",
    "iletisim",
]
PILOT_POSTS = ["led-ekran-fiyatlari-2026"]

PAGE_SLUGS: dict[str, dict[str, str]] = {
    "tr-2": {"en": "home-en", "de": "home-de"},
    "led-ekran": {"en": "led-screen", "de": "led-display"},
    "ic-mekan-led-ekran": {"en": "indoor-led-screen", "de": "indoor-led-display"},
    "dis-mekan-led-ekran": {"en": "outdoor-led-screen", "de": "outdoor-led-display"},
    "rental-ekran": {"en": "rental-led-screen", "de": "rental-led-display"},
    "cob-ekran": {"en": "cob-led-screen", "de": "cob-led-display"},
    "ic-mekan-rgb-panel": {"en": "indoor-rgb-panel", "de": "indoor-rgb-panel"},
    "dis-mekan-rgb-panel": {"en": "outdoor-rgb-panel", "de": "outdoor-rgb-panel"},
    "kontrol-kartlari": {"en": "control-cards", "de": "steuerkarten"},
    "guc-kaynaklari": {"en": "power-supplies", "de": "netzteile"},
    "markalarimiz": {"en": "brands", "de": "marken"},
    "sertifikalarimiz": {"en": "certificates", "de": "zertifikate"},
    "huidu-processor-hdplayer-indir": {
        "en": "huidu-hdplayer-download",
        "de": "huidu-hdplayer-download",
    },
    "huidu": {"en": "huidu", "de": "huidu"},
    "colorlight": {"en": "colorlight", "de": "colorlight"},
    "gob-led-ekran": {"en": "gob-led-screen", "de": "gob-led-display"},
    "gob-led-nedir": {"en": "what-is-gob-led", "de": "was-ist-gob-led"},
    "smd-led-nedir": {"en": "what-is-smd-led", "de": "was-ist-smd-led"},
    "led-panel-nedir": {"en": "what-is-led-panel", "de": "was-ist-ein-led-panel"},
    "ip-koruma-led-ekran": {"en": "led-screen-ip-rating", "de": "led-display-ip-schutzart"},
    "nits-parlaklik-nedir": {"en": "what-is-nits-brightness", "de": "was-ist-nits-helligkeit"},
    "refresh-hz-nedir": {"en": "what-is-refresh-rate", "de": "was-ist-bildwiederholrate"},
    "pitch-led-nedir": {"en": "what-is-pixel-pitch", "de": "was-ist-pixel-pitch"},
    "led-ekran-projeksiyon": {
        "en": "led-screen-vs-projection",
        "de": "led-display-vs-projektor",
    },
    "led-ekran-lcd-farki": {"en": "led-screen-vs-lcd", "de": "led-display-vs-lcd"},
    "gob-vs-cob-smd": {"en": "gob-vs-cob-smd", "de": "gob-vs-cob-smd"},
    "cob-led-ne-zaman": {"en": "when-to-choose-cob-led", "de": "wann-cob-led-waehlen"},
    "ic-mekan-dis-mekan-led-farki": {
        "en": "indoor-vs-outdoor-led",
        "de": "indoor-vs-outdoor-led",
    },
    "p2-vs-p3-led-ekran": {"en": "p2-vs-p3-led-screen", "de": "p2-vs-p3-led-display"},
    "cami-led-ekran": {"en": "mosque-led-screen", "de": "moschee-led-display"},
    "eczane-led-tabela": {"en": "pharmacy-led-sign", "de": "apotheke-led-tafel"},
    "belediye-bilgi-ekrani": {
        "en": "municipality-info-screen",
        "de": "kommunales-info-display",
    },
    "magaza-vitrin-led-ekran": {
        "en": "storefront-led-screen",
        "de": "schaufenster-led-display",
    },
    "stadyum-led-ekran": {"en": "stadium-led-screen", "de": "stadion-led-display"},
    "avm-led-ekran-rehberi": {"en": "mall-led-screen-guide", "de": "einkaufszentrum-led-leitfaden"},
    "led-ekran-bakim": {"en": "led-screen-maintenance", "de": "led-display-wartung"},
    "led-ekran-kurulum": {"en": "led-screen-installation", "de": "led-display-installation"},
    "led-tabela": {"en": "led-signage", "de": "led-beschilderung"},
    "led-ekran-nedir": {"en": "what-is-led-screen", "de": "was-ist-ein-led-display"},
    "projeler": {"en": "projects", "de": "projekte"},
    "toplanti-odasi-led-ekran": {
        "en": "meeting-room-led-screen",
        "de": "konferenzraum-led-display",
    },
    "billboard-led-ekran": {"en": "billboard-led-screen", "de": "billboard-led-display"},
    "fuar-led-ekran": {"en": "exhibition-led-screen", "de": "messe-led-display"},
    "otel-led-ekran": {"en": "hotel-led-screen", "de": "hotel-led-display"},
    "havaalani-led-ekran": {"en": "airport-led-screen", "de": "flughafen-led-display"},
    "izmir-led-ekran": {"en": "izmir-led-screen", "de": "izmir-led-display"},
    "ankara-led-ekran": {"en": "ankara-led-screen", "de": "ankara-led-display"},
    "istanbul-led-ekran": {"en": "istanbul-led-screen", "de": "istanbul-led-display"},
    "teknik-destek-videolari": {
        "en": "technical-support-videos",
        "de": "technische-support-videos",
    },
    "program-indir": {"en": "software-download", "de": "software-download"},
    "firma-bilgilerimiz": {"en": "company-information", "de": "firmeninformationen"},
    "iletisim": {"en": "contact", "de": "kontakt"},
    "blog": {"en": "blog", "de": "blog"},
    "hakkimizda": {"en": "about-us", "de": "uber-uns"},
}

POST_SLUGS: dict[str, dict[str, str]] = {
    "led-ekran-fiyatlari-2026": {
        "en": "led-screen-prices-2026",
        "de": "led-display-preise-2026",
    },
    "ic-mekan-led-ekran-fiyatlari-2026": {
        "en": "indoor-led-screen-prices-2026",
        "de": "indoor-led-display-preise-2026",
    },
    "dis-mekan-led-ekran-fiyatlari-2026": {
        "en": "outdoor-led-screen-prices-2026",
        "de": "outdoor-led-display-preise-2026",
    },
    "rental-led-ekran-kiralama-fiyatlari-2026": {
        "en": "rental-led-screen-hire-prices-2026",
        "de": "led-display-mietpreise-2026",
    },
    "led-ekran-nasil-secilir-rehber": {
        "en": "how-to-choose-led-screen",
        "de": "led-display-richtig-auswaehlen",
    },
    "gob-led-ekran-ne-zaman-tercih-edilir": {
        "en": "when-to-choose-gob-led",
        "de": "wann-gob-led-waehlen",
    },
    "cob-led-ekran-nedir-avantajlari": {
        "en": "what-is-cob-led-screen",
        "de": "was-ist-cob-led-display",
    },
    "huidu-wf1-wf2-wf4-led-kontrol-karti": {
        "en": "huidu-wf1-wf2-wf4-led-controller",
        "de": "huidu-wf1-wf2-wf4-led-steuerung",
    },
    "serit-led": {"en": "led-strip", "de": "led-streifen"},
    "kayan-yazi": {"en": "led-ticker", "de": "led-laufschrift"},
    "p10-grafik-ekran-kullanimi": {
        "en": "p10-graphic-display-usage",
        "de": "p10-grafikdisplay-nutzung",
    },
    "ic-mekan-led-ekranlar": {"en": "indoor-led-screens", "de": "indoor-led-displays"},
    "dis-mekan-led-ekranlar": {"en": "outdoor-led-screens", "de": "outdoor-led-displays"},
    "pcb-nedir": {"en": "what-is-pcb", "de": "was-ist-pcb"},
    "led-nit-mcd": {"en": "led-nits-mcd", "de": "led-nits-mcd"},
    "dip-led-panel-tamiri": {"en": "dip-led-panel-repair", "de": "dip-led-panel-reparatur"},
    "led-ekran-omru": {"en": "led-screen-lifespan", "de": "led-display-lebensdauer"},
    "led-ekran-kullanim-alanlari": {
        "en": "led-screen-applications",
        "de": "led-display-anwendungsbereiche",
    },
}

TEXT_KEYS = {
    "title",
    "editor",
    "html",
    "text",
    "description",
    "caption",
    "inner_text",
    "button_text",
    "link_text",
    "editor_content",
    "testimonial_content",
    "tab_title",
    "accordion_title",
    "item_description",
    "heading_title",
    "sub_title",
    "subtitle",
    "label",
    "placeholder",
    "before",
    "after",
    "alert_title",
    "alert_description",
    "title_text",
    "description_text",
    "footer_text",
    "header_text",
    "prefix",
    "suffix",
    "inner_html",
    "custom_text",
    "excerpt",
    "short_description",
    "before_text",
    "after_text",
    "heading",
    "content",
    "button",
    "cta_text",
    "more_text",
}

SKIP_VALUE_RE = re.compile(
    r"^(https?:|mailto:|tel:|#|rgb\(|rgba\(|hsl\(|#?[0-9a-fA-F]{3,8}$|fa |eicon-|fas |far |elementor-)"
)
TR_HINT_RE = re.compile(
    r"[ğüşıöçĞÜŞİÖÇ]|(\b)(ve|ile|için|bir|bu|nedir|nasıl|fiyat|teklif|keşif|ekran)(\b)",
    re.I,
)
TOKEN_RE = re.compile(
    r"LEDAJANS|Ledajans|Colorlight|HUIDU|Huidu|Novastar|Linsn|WhatsApp|"
    r"HDPlayer|LEDVISION|COB|GOB|SMD|DIP|RGB|IP65|IP54|HDMI|"
    r"P1\.25|P1\.53|P1\.86|P2\.5|P10|P2|P3|P4|P5|P6|P8",
)

# (tr, en, de) — longest match first after sort
_PHRASES: list[tuple[str, str, str]] = [
    (
        "LEDAJANS, LED ekran, kayan yazı ve dijital tabela sistemlerinde kullanılan LED modül, güç kaynağı, kontrol kartı ve aksesuar satışında Türkiye'nin güvenilir adresidir. Toptan ve perakende satış, teknik destek ve hızlı kargo ile sektör profesyonellerinin yanındadır.",
        "LEDAJANS is Turkey’s trusted source for LED modules, power supplies, control cards and accessories used in LED screens, tickers and digital signage. Wholesale and retail sales, technical support and fast shipping for industry professionals.",
        "LEDAJANS ist die verlässliche Adresse in der Türkei für LED-Module, Netzteile, Steuerkarten und Zubehör für LED-Displays, Laufschriften und Digital Signage. Groß- und Einzelhandel, technischer Support und schneller Versand für Profis.",
    ),
    ("Ücretsiz keşif ve fiyat teklifi", "Free site survey and quote", "Kostenlose Besichtigung und Angebot"),
    ("Ücretsiz keşif", "Free site survey", "Kostenlose Besichtigung"),
    ("Fiyatları ve Modelleri", "Prices and Models", "Preise und Modelle"),
    ("Fiyatları ve modelleri", "prices and models", "Preise und Modelle"),
    ("LED Ekran Projeleri", "LED Screen Projects", "LED-Display-Projekte"),
    ("LED Ekran Fiyatları 2026", "LED Screen Prices 2026", "LED-Display-Preise 2026"),
    ("İç Mekan LED Ekran Fiyatları", "Indoor LED Screen Prices", "Indoor-LED-Display-Preise"),
    ("Dış Mekan LED Ekran Fiyatları", "Outdoor LED Screen Prices", "Outdoor-LED-Display-Preise"),
    ("LED Ekran Kiralama Fiyatları", "LED Screen Rental Prices", "LED-Display-Mietpreise"),
    ("COB LED Ekran Nedir?", "What is a COB LED Screen?", "Was ist ein COB-LED-Display?"),
    ("GOB LED Ekran Ne Zaman Tercih Edilir?", "When to Choose a GOB LED Screen?", "Wann ein GOB-LED-Display wählen?"),
    ("LED Ekran Nasıl Seçilir?", "How to Choose an LED Screen?", "Wie wählt man ein LED-Display?"),
    ("LED Ekran Nedir?", "What is an LED Screen?", "Was ist ein LED-Display?"),
    ("Nits Parlaklık Nedir?", "What is Nits Brightness?", "Was ist Nits-Helligkeit?"),
    ("LED Ekran vs Projeksiyon", "LED Screen vs Projection", "LED-Display vs. Projektor"),
    ("LED Ekran vs LCD Karşılaştırma", "LED Screen vs LCD Comparison", "LED-Display vs. LCD-Vergleich"),
    ("P2 vs P3 LED Ekran Karşılaştırma", "P2 vs P3 LED Screen Comparison", "P2 vs. P3 LED-Display-Vergleich"),
    ("Cami LED Ekran Rehberi", "Mosque LED Screen Guide", "LED-Display-Leitfaden für Moscheen"),
    ("Mağaza Vitrin LED Ekran", "Storefront LED Screen", "Schaufenster-LED-Display"),
    ("Stadyum LED Ekran Rehberi", "Stadium LED Screen Guide", "Stadion-LED-Display-Leitfaden"),
    ("AVM LED Ekran Rehberi", "Mall LED Screen Guide", "Einkaufszentrum-LED-Leitfaden"),
    ("LED Ekran Bakım Rehberi", "LED Screen Maintenance Guide", "LED-Display-Wartungsleitfaden"),
    ("LED Ekran Kurulum Rehberi", "LED Screen Installation Guide", "LED-Display-Installationsleitfaden"),
    ("LED Ekran Kullanım Alanları", "LED Screen Use Cases", "LED-Display-Einsatzbereiche"),
    ("Belediye Bilgi Ekranı Rehberi", "Municipal Info Screen Guide", "Leitfaden kommunales Info-Display"),
    ("Eczane LED Tabela Rehberi", "Pharmacy LED Sign Guide", "Apotheken-LED-Tafel-Leitfaden"),
    ("LED Tabela Rehberi", "LED Signage Guide", "LED-Beschilderungsleitfaden"),
    ("Toplantı Odası LED Ekran", "Meeting Room LED Screen", "LED-Display für Besprechungsräume"),
    ("Billboard LED Ekran", "Billboard LED Screen", "Billboard-LED-Display"),
    ("Fuar LED Ekran", "Trade Fair LED Screen", "Messe-LED-Display"),
    ("Otel LED Ekran", "Hotel LED Screen", "Hotel-LED-Display"),
    ("Havalimanı LED Ekran", "Airport LED Screen", "Flughafen-LED-Display"),
    ("İzmir LED Ekran", "Izmir LED Screen", "Izmir-LED-Display"),
    ("Ankara LED Ekran", "Ankara LED Screen", "Ankara-LED-Display"),
    ("İstanbul LED Ekran", "Istanbul LED Screen", "Istanbul-LED-Display"),
    ("GOB LED Ekran", "GOB LED Screen", "GOB-LED-Display"),
    ("IP Koruma Sınıfı", "IP Protection Rating", "IP-Schutzart"),
    ("Kapsamlı Rehber", "Comprehensive Guide", "Umfassender Leitfaden"),
    ("Ne Zaman Tercih Edilmeli", "When to Choose", "Wann wählen"),
    ("Ne Zaman Tercih Edilir", "When to Choose", "Wann wählen"),
    ("Nasıl Seçilir", "How to Choose", "Wie wählen"),
    ("Avantajları", "Advantages", "Vorteile"),
    ("Karşılaştırma", "Comparison", "Vergleich"),
    ("Kullanım Alanları", "Use Cases", "Einsatzbereiche"),
    ("Toplantı Odası", "Meeting Room", "Besprechungsraum"),
    ("Havalimanı", "Airport", "Flughafen"),
    ("Mayıs Güncel", "May Update", "Mai-Update"),
    ("Projeleri", "Projects", "Projekte"),
    ("Fiyatları 2026", "Prices 2026", "Preise 2026"),
    ("Fiyatları", "Prices", "Preise"),
    ("Nedir?", "What is it?", "Was ist das?"),
    ("Rehberi", "Guide", "Leitfaden"),
    ("Rehber", "Guide", "Leitfaden"),
    ("Satış, Kiralama ve Kurulum", "Sales, Rental and Installation", "Verkauf, Miete und Installation"),
    ("Satış, Kiralama", "Sales, Rental", "Verkauf, Miete"),
    ("Teklif Al", "Get a Quote", "Angebot holen"),
    ("Teklif al", "Get a quote", "Angebot holen"),
    ("Hemen Ara", "Call Now", "Jetzt anrufen"),
    ("Hemen ara", "Call now", "Jetzt anrufen"),
    ("WhatsApp ile yazın", "Message on WhatsApp", "Per WhatsApp schreiben"),
    ("Firma Bilgilerimiz", "Company Information", "Firmeninformationen"),
    ("Teknik Destek Videoları", "Technical Support Videos", "Technische Support-Videos"),
    ("Teknik Destek & Bilgi", "Technical Support & Info", "Technischer Support & Infos"),
    ("Teknik Destek", "Technical Support", "Technischer Support"),
    ("Program İndir", "Download Software", "Software herunterladen"),
    ("İç Mekan RGB Panel", "Indoor RGB Panel", "Indoor-RGB-Panel"),
    ("Dış Mekan RGB Panel", "Outdoor RGB Panel", "Outdoor-RGB-Panel"),
    ("İç Mekan LED Ekran", "Indoor LED Screen", "Indoor-LED-Display"),
    ("Dış Mekan LED Ekran", "Outdoor LED Screen", "Outdoor-LED-Display"),
    ("Kontrol Kartları", "Control Cards", "Steuerkarten"),
    ("Güç Kaynakları", "Power Supplies", "Netzteile"),
    ("Rental Ekran", "Rental LED Screen", "Miet-LED-Display"),
    ("COB – Smart Screen", "COB – Smart Screen", "COB – Smart Screen"),
    ("COB - Smart Screen", "COB - Smart Screen", "COB - Smart Screen"),
    ("Tüm ürünler", "All products", "Alle Produkte"),
    ("Tüm Ürünler", "All Products", "Alle Produkte"),
    ("Ürünlerimiz", "Products", "Produkte"),
    ("Hakkımızda", "About Us", "Über uns"),
    ("Sertifikalarımız", "Certificates", "Zertifikate"),
    ("Markalarımız", "Our Brands", "Unsere Marken"),
    ("Hızlı Linkler", "Quick Links", "Schnelllinks"),
    ("Anasayfa", "Home", "Startseite"),
    ("İletişim", "Contact", "Kontakt"),
    ("Galeri", "Gallery", "Galerie"),
    ("Ürünler", "Products", "Produkte"),
    ("Projeler", "Projects", "Projekte"),
    ("Kayan yazı", "LED ticker", "LED-Laufschrift"),
    ("Kayan Yazı", "LED Ticker", "LED-Laufschrift"),
    ("Dijital tabela", "Digital signage", "Digital Signage"),
    ("LED tabela", "LED signage", "LED-Beschilderung"),
    ("LED Ekran", "LED Screen", "LED-Display"),
    ("LED ekran", "LED screen", "LED-Display"),
    ("led ekran", "LED screen", "LED-Display"),
    ("İç mekan", "Indoor", "Innenbereich"),
    ("Dış mekan", "Outdoor", "Außenbereich"),
    ("iç mekan", "indoor", "Innenbereich"),
    ("dış mekan", "outdoor", "Außenbereich"),
    ("Teknik Destek", "Technical Support", "Technischer Support"),
    ("Teknik destek", "Technical support", "Technischer Support"),
    ("Kurumsal", "Company", "Unternehmen"),
    ("Dil", "Language", "Sprache"),
    ("Türkçe", "Turkish", "Türkisch"),
    ("English", "English", "English"),
    ("Deutsch", "Deutsch", "Deutsch"),
    ("Tüm hakları saklıdır.", "All rights reserved.", "Alle Rechte vorbehalten."),
    ("Tüm hakları saklıdır", "All rights reserved", "Alle Rechte vorbehalten"),
    ("Büyütülmüş galeri görseli", "Enlarged gallery image", "Vergrößertes Galeriebild"),
    ("Galeri 1'i büyüt", "Enlarge gallery 1", "Galerie 1 vergrößern"),
    ("Galeri 2'yi büyüt", "Enlarge gallery 2", "Galerie 2 vergrößern"),
    ("Galeri 3'ü büyüt", "Enlarge gallery 3", "Galerie 3 vergrößern"),
    ("Galeri 4'ü büyüt", "Enlarge gallery 4", "Galerie 4 vergrößern"),
    ("Galeri 5'i büyüt", "Enlarge gallery 5", "Galerie 5 vergrößern"),
    ("Galeri 6'yı büyüt", "Enlarge gallery 6", "Galerie 6 vergrößern"),
    ("Menüyü aç", "Open menu", "Menü öffnen"),
    ("Menüyü kapat", "Close menu", "Menü schließen"),
    ("Telefon ile iletişim", "Phone contact", "Telefonkontakt"),
    ("Kapat", "Close", "Schließen"),
    ("Devamını Oku", "Read more", "Weiterlesen"),
    ("Devamını oku", "Read more", "Weiterlesen"),
    ("Daha fazla", "See more", "Mehr anzeigen"),
    ("Yükleniyor", "Loading", "Wird geladen"),
    ("Ücretsiz keşif için arayın", "Call for a free survey", "Für eine kostenlose Besichtigung anrufen"),
    ("Fiyat teklifi", "Price quote", "Preisangebot"),
    ("Keşif", "Site survey", "Besichtigung"),
    ("Kurulum", "Installation", "Installation"),
    ("Kiralama", "Rental", "Miete"),
    ("Satış", "Sales", "Verkauf"),
    ("Garanti", "Warranty", "Garantie"),
    ("2 yıl garanti", "2-year warranty", "2 Jahre Garantie"),
    ("25 yıl tecrübe", "25 years of experience", "25 Jahre Erfahrung"),
    ("İstanbul", "Istanbul", "Istanbul"),
    ("Şişli", "Sisli", "Sisli"),
    ("Piksel pitch", "Pixel pitch", "Pixelpitch"),
    ("Parlaklık", "Brightness", "Helligkeit"),
    ("Kontrol kartı", "Control card", "Steuerkarte"),
    ("Güç kaynağı", "Power supply", "Netzteil"),
    ("LED modül", "LED module", "LED-Modul"),
    ("Fine pitch", "Fine pitch", "Fine Pitch"),
    ("Smart Screen", "Smart Screen", "Smart Screen"),
    ("Blog yazıları yüklenirken bir hata oluştu.", "Failed to load blog posts.", "Blogbeiträge konnten nicht geladen werden."),
]


def _phrase_index() -> list[tuple[str, str, str]]:
    return sorted(_PHRASES, key=lambda x: len(x[0]), reverse=True)


PHRASES = _phrase_index()

ATTR_KEYS = {"alt", "title", "aria-label", "placeholder", "aria-labelledby"}


def link_lang(link: str) -> str:
    low = (link or "").lower()
    if "/en/" in low or low.rstrip("/").endswith("/en"):
        return "en"
    if "/de/" in low or low.rstrip("/").endswith("/de"):
        return "de"
    return "tr"


def slug_for(tr_slug: str, lang: str, kind: str = "page") -> str:
    table = PAGE_SLUGS if kind == "page" else POST_SLUGS
    mapped = table.get(tr_slug, {}).get(lang)
    if mapped:
        return mapped
    return tr_slug


def path_for(tr_slug: str, lang: str, kind: str = "page") -> str:
    if tr_slug in {"tr-2", "", "home", "home-en", "home-de"} and kind == "page":
        return f"/{lang}/"
    sl = slug_for(tr_slug, lang, kind)
    return f"/{lang}/{sl}/"


def skip_page(slug: str) -> bool:
    return slug in SKIP_PAGE_SLUGS


def skip_post(slug: str) -> bool:
    return slug in SKIP_POST_SLUGS


def _protect(text: str) -> tuple[str, list[str]]:
    tokens: list[str] = []

    def repl(m: re.Match[str]) -> str:
        tokens.append(m.group(0))
        return f"§§T{len(tokens) - 1}§§"

    return TOKEN_RE.sub(repl, text), tokens


def _unprotect(text: str, tokens: list[str]) -> str:
    for i, tok in enumerate(tokens):
        text = text.replace(f"§§T{i}§§", tok)
    return text


def _glossary(text: str, lang: str) -> str:
    col = 1 if lang == "en" else 2
    out = text
    for tr, en, de in PHRASES:
        if tr in out:
            out = out.replace(tr, (en if col == 1 else de))
    return out


def looks_turkish(text: str) -> bool:
    if not text or not text.strip():
        return False
    return bool(TR_HINT_RE.search(text))


def _machine(text: str, lang: str) -> str:
    target = "en" if lang == "en" else "de"
    try:
        from deep_translator import GoogleTranslator

        tr = GoogleTranslator(source="tr", target=target)
        got = tr.translate(text)
        return got if isinstance(got, str) and got.strip() else text
    except Exception:
        return text


def translate_text(text: str, lang: str, *, use_mt: bool = True) -> str:
    if lang not in LANGS or not isinstance(text, str) or text == "":
        return text
    if SKIP_VALUE_RE.search(text.strip()):
        return text
    if re.fullmatch(r"[\d\s%.,:+/-]+", text.strip() or "x"):
        return text
    glossed = _glossary(text, lang)
    if glossed.strip() == "Bilgi":
        repl = "Info" if lang == "en" else "Infos"
        glossed = glossed.replace("Bilgi", repl)
    if use_mt and looks_turkish(glossed) and len(glossed.strip()) >= 3:
        raw, tokens = _protect(glossed)
        glossed = _unprotect(_machine(raw, lang), tokens)
    return glossed


class _HTMLRewriter(HTMLParser):
    def __init__(self, lang: str, use_mt: bool) -> None:
        super().__init__(convert_charrefs=False)
        self.lang = lang
        self.use_mt = use_mt
        self.out: list[str] = []
        self._skip = 0
        self._lang_flags: list[bool] = []
        self._hreflang = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = " ".join((v or "") for k, v in attrs if k.lower() == "class")
        if tag == "li":
            self._lang_flags.append("lang-item" in classes)
        if tag == "a" and any(k.lower() == "hreflang" for k, _ in attrs):
            self._hreflang += 1
        if tag in {"script", "style"}:
            self._skip += 1
        self.out.append(self._start(tag, attrs, False))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.out.append(self._start(tag, attrs, True))

    def _start(self, tag: str, attrs: list[tuple[str, str | None]], closed: bool) -> str:
        parts = [f"<{tag}"]
        for k, v in attrs:
            if v is None:
                parts.append(f" {k}")
                continue
            lk = k.lower()
            skip = any(self._lang_flags) or self._hreflang
            if lk in ATTR_KEYS and not skip:
                v = translate_text(v, self.lang, use_mt=self.use_mt)
            elif lk in {"href", "action"} and not skip:
                v = rewrite_href(v, self.lang)
            parts.append(f' {k}="{html_lib.escape(v, quote=True)}"')
        parts.append(" />" if closed else ">")
        return "".join(parts)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1
        if tag == "a" and self._hreflang:
            self._hreflang -= 1
        if tag == "li" and self._lang_flags:
            self._lang_flags.pop()
        self.out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._skip:
            self.out.append(data)
            return
        if data.strip() and not any(self._lang_flags) and not self._hreflang:
            self.out.append(translate_text(data, self.lang, use_mt=self.use_mt))
        else:
            self.out.append(data)

    def handle_entityref(self, name: str) -> None:
        self.out.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.out.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.out.append(f"<!--{data}-->")


def translate_html(src: str, lang: str, *, use_mt: bool = True) -> str:
    if not src or "<" not in src:
        return translate_text(src, lang, use_mt=use_mt)
    p = _HTMLRewriter(lang, use_mt)
    try:
        p.feed(src)
        p.close()
        return "".join(p.out)
    except Exception:
        return translate_text(src, lang, use_mt=use_mt)


def _lookup_tr_slug(path: str) -> tuple[str, str] | None:
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return "tr-2", "page"
    slug = parts[-1]
    if slug in PAGE_SLUGS or slug == "tr-2":
        return slug, "page"
    if slug in POST_SLUGS:
        return slug, "post"
    if slug in PAGE_SLUGS:
        return slug, "page"
    return slug, "page" if slug in PAGE_SLUGS else "post"


def rewrite_href(url: str, lang: str) -> str:
    if not url or url.startswith(("mailto:", "tel:", "#", "javascript:")):
        return url
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if host and host not in {"ledajans.com", "www.ledajans.com"}:
        return url
    path = parsed.path or "/"
    low = path.lower()
    if low.startswith("/wp-content/") or low.startswith("/wp-json"):
        return url
    if re.match(r"^/(en|de)(/|$)", low):
        return url
    slug_path = low.rstrip("/") or "/"
    if slug_path == "/":
        new_path = f"/{lang}/"
    else:
        tr_slug = slug_path.strip("/").split("/")[-1]
        kind = "page" if tr_slug in PAGE_SLUGS or tr_slug == "tr-2" else "post"
        if tr_slug == "tr-2":
            new_path = f"/{lang}/"
        else:
            new_path = path_for(tr_slug, lang, kind)
    rebuilt = parsed._replace(
        scheme="https" if host else parsed.scheme,
        netloc="ledajans.com" if host else parsed.netloc,
        path=new_path,
    )
    if not host and url.startswith("/"):
        return new_path + (("?" + parsed.query) if parsed.query else "") + (
            ("#" + parsed.fragment) if parsed.fragment else ""
        )
    return urlunparse(rebuilt)


def _rewrite_link_obj(obj: Any, lang: str) -> Any:
    if isinstance(obj, dict):
        url = obj.get("url")
        if isinstance(url, str):
            obj = dict(obj)
            obj["url"] = rewrite_href(url, lang)
        return obj
    if isinstance(obj, str):
        return rewrite_href(obj, lang)
    return obj


def translate_elementor(data: Any, lang: str, *, use_mt: bool = True) -> Any:
    if isinstance(data, list):
        return [translate_elementor(x, lang, use_mt=use_mt) for x in data]
    if not isinstance(data, dict):
        return data
    out = {}
    for k, v in data.items():
        lk = str(k).lower()
        if lk in {"css", "custom_css", "_id", "id", "elType", "widgetType", "settings"}:
            pass
        if k == "settings" and isinstance(v, dict):
            settings = {}
            for sk, sv in v.items():
                sl = str(sk).lower()
                if sl in {"link", "url", "button_url"} or sl.endswith("_link"):
                    settings[sk] = _rewrite_link_obj(deepcopy(sv), lang)
                elif sl in TEXT_KEYS or sl.endswith("_html") or sl.endswith("_text"):
                    if isinstance(sv, str) and ("<" in sv and ">" in sv):
                        settings[sk] = translate_html(sv, lang, use_mt=use_mt)
                    elif isinstance(sv, str):
                        settings[sk] = translate_text(sv, lang, use_mt=use_mt)
                    else:
                        settings[sk] = translate_elementor(sv, lang, use_mt=use_mt)
                else:
                    settings[sk] = translate_elementor(sv, lang, use_mt=use_mt)
            out[k] = settings
            continue
        if isinstance(v, str) and (lk in TEXT_KEYS or lk.endswith("_html") or lk.endswith("_text")):
            out[k] = (
                translate_html(v, lang, use_mt=use_mt)
                if "<" in v and ">" in v
                else translate_text(v, lang, use_mt=use_mt)
            )
        else:
            out[k] = translate_elementor(v, lang, use_mt=use_mt)
    return out


def translate_title(title: str, lang: str) -> str:
    t = translate_text(html_lib.unescape(re.sub(r"<[^>]+>", "", title or "")), lang, use_mt=True)
    return t.strip() or title


def rankmath_for(title: str, lang: str, focus_tr: str = "led ekran") -> dict[str, str]:
    t = translate_title(title, lang)
    if lang == "en":
        desc = (
            f"{t}. Indoor and outdoor LED screens, rental and fine-pitch COB. "
            "Free site survey and B2B quote — LEDAJANS Istanbul."
        )
        focus = "led screen,led display,indoor led,outdoor led"
        if "contact" in t.lower():
            focus = "led screen quote,ledajans contact"
        seo_title = f"{t} | LEDAJANS"
    else:
        desc = (
            f"{t}. Indoor- und Outdoor-LED-Displays, Miete und Fine-Pitch-COB. "
            "Kostenlose Besichtigung und B2B-Angebot — LEDAJANS Istanbul."
        )
        focus = "led display,led bildschirm,indoor led,outdoor led"
        seo_title = f"{t} | LEDAJANS"
    if len(desc) > 160:
        desc = desc[:157] + "..."
    return {
        "rank_math_title": seo_title[:70],
        "rank_math_description": desc,
        "rank_math_focus_keyword": focus,
    }


def load_state(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"pages": {}, "posts": {}, "menus": {}, "templates": {}}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def self_test() -> int:
    en = translate_text("Teklif Al", "en", use_mt=False)
    de = translate_text("Teklif Al", "de", use_mt=False)
    assert en == "Get a Quote", en
    assert de == "Angebot holen", de
    href = rewrite_href("https://ledajans.com/led-ekran/", "en")
    assert href == "https://ledajans.com/en/led-screen/", href
    href2 = rewrite_href("https://ledajans.com/iletisim/", "de")
    assert href2 == "https://ledajans.com/de/kontakt/", href2
    html = translate_html('<a href="https://ledajans.com/hakkimizda/">Hakkımızda</a>', "en", use_mt=False)
    assert "about-us" in html and "About Us" in html, html
    rgb = translate_text("İç Mekan RGB Panel", "en", use_mt=False)
    assert rgb == "Indoor RGB Panel", rgb
    sw = translate_html(
        '<li><a href="https://ledajans.com/" hreflang="tr-TR" lang="tr-TR"><span class="menu-title">Türkçe</span></a></li>',
        "en",
        use_mt=False,
    )
    assert 'href="https://ledajans.com/"' in sw and "Türkçe" in sw, sw
    print("self-test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
