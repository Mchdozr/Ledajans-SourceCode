#!/usr/bin/env python3
"""Canlı yedekten (YEDEK/<tarih>/html.tar.gz) önizleme sayfalarını üretir. CANLI SİTEYE DOKUNMAZ.

Çıktı:
  ONIZLEME/sonra/<dosya>.html   değiştirilmiş sayfalar
  ONIZLEME/degisiklikler.json   her sayfa için önce/sonra listesi + yönlendirmeler + robots
Kullanım: python3 ONIZLEME/build_preview.py
"""
from __future__ import annotations
import json, re, tarfile
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parent
YEDEK = ROOT.parent / "YEDEK" / "2026-11-24"
OUT = ROOT / "sonra"
BRIEFS = {b["id"]: b for b in json.loads((ROOT / "veri" / "briefs.json").read_text(encoding="utf-8"))["briefs"]}

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⭕️‍]+\\s*")
PH = re.compile(r"\[\[([^\]]*)\]\]")


def file_of(path: str) -> str:
    p = path.strip("/")
    return (p or "anasayfa").replace("/", "__") + ".html"


def load_originals() -> dict[str, str]:
    out = {}
    with tarfile.open(YEDEK / "html.tar.gz") as t:
        for m in t.getmembers():
            if m.isfile():
                out[Path(m.name).name] = t.extractfile(m).read().decode("utf-8", "replace")
    return out


# ---------- sayfa bazlı değişiklikler ----------
def B(i, k):
    return BRIEFS[i][k]

PAGES = {
    "/": dict(risk="orta", brief="b01", desc=B("b01", "desc"), faq_from_details=True,
              og_image="https://ledajans.com/wp-content/uploads/2026/09/dis-mekan-led-ekran-1.webp",
              not_="'led ekran' için en hassas sayfa. Title, H1 ve görünen metin DEĞİŞMEDİ; sadece açıklama, SSS schema ve og:image eklendi. Canlıya en son alınmalı."),
    "/led-ekran/": dict(risk="düşük", brief="b02", title=B("b02", "title"), desc=B("b02", "desc"), h1="LED Ekran Modelleri",
                        giris=B("b02", "giris"), not_="Title hâlâ 'LED Ekran' ile başlıyor. Anasayfadan 2–3 hafta önce uygulanmalı ve izlenmeli."),
    "/led-ekran-fiyatlari-2026/": dict(risk="yok", brief="b03", title=B("b03", "title"), desc=B("b03", "desc"), h1="LED Ekran Fiyatları 2026",
                                       giris=B("b03", "giris"), strip_text=[" (Mayıs Güncel)"], guncelleme=True, emoji=True),
    "/ic-mekan-led-ekran/": dict(risk="yok", brief="b04", title=B("b04", "title"), desc=B("b04", "desc"), giris=B("b04", "giris")),
    "/ic-mekan-led-ekran-fiyatlari-2026/": dict(risk="yok", brief="b05", title=B("b05", "title"), desc=B("b05", "desc"), giris=B("b05", "giris"), guncelleme=True, emoji=True),
    "/dis-mekan-led-ekran/": dict(risk="yok", brief="b06", title=B("b06", "title"), desc=B("b06", "desc"), giris=B("b06", "giris")),
    "/dis-mekan-led-ekran-fiyatlari-2026/": dict(risk="yok", brief="b07", title=B("b07", "title"), desc=B("b07", "desc"), giris=B("b07", "giris"),
                                                 faq_from_sc=True, guncelleme=True, emoji=True),
    "/rental-ekran/": dict(risk="yok", brief="b08", title=B("b08", "title"), desc=B("b08", "desc"), giris=B("b08", "giris")),
    "/rental-led-ekran-kiralama-fiyatlari-2026/": dict(risk="yok", brief="b09", title=B("b09", "title"), desc=B("b09", "desc"),
                                                       h1="LED Ekran Kiralama Fiyatları 2026", giris=B("b09", "giris"), guncelleme=True, emoji=True),
    "/istanbul-led-ekran/": dict(risk="yok", brief="b10", title=B("b10", "title"), desc=B("b10", "desc"), h1="İstanbul LED Ekran", giris=B("b10", "giris")),
    "/ankara-led-ekran/": dict(risk="yok", brief="b11", title=B("b11", "title"), desc=B("b11", "desc"), h2_to_h1="Ankara LED Ekran", index=True, emoji=True,
                               not_="Sayfa noindex'ten çıkarılıyor ve sitemap'e ekleniyor."),
    "/izmir-led-ekran/": dict(risk="yok", brief="b11", title="İzmir LED Ekran | Satış, Kurulum ve Kiralama – LEDAJANS",
                              desc="İzmir'de LED ekran satış, kurulum ve kiralama. Fuar, otel, AVM ve cephe projeleri için ücretsiz keşif, IP65 dış mekan modeller ve 2 yıl garanti.",
                              h2_to_h1="İzmir LED Ekran", index=True, emoji=True, not_="Sayfa noindex'ten çıkarılıyor ve sitemap'e ekleniyor."),
    "/ic-mekan-rgb-panel/": dict(risk="yok", brief="b12", title=B("b12", "title"), desc=B("b12", "desc"), h1="İç Mekan RGB LED Panel", giris=B("b12", "giris")),
    "/dis-mekan-rgb-panel/": dict(risk="yok", brief="b12", title="Dış Mekan RGB LED Panel | P2.5–P10 Outdoor – LEDAJANS",
                                  desc="Dış mekan RGB LED ekran paneli: P2.5–P10 outdoor modüller, IP65, yüksek parlaklık. Tabela ve LED ekran üreticileri için toptan satış ve teknik destek.",
                                  h1="Dış Mekan RGB LED Panel",
                                  giris="Dış mekan RGB LED panel, açık havada kullanılan LED ekran ve tabelaların yapı taşı olan, IP65 korumalı ve yüksek parlaklıklı modüldür. LEDAJANS dış mekan için P2.5'ten P10'a kadar panel sunar; paneller HUB75 kabloyla alıcı karta bağlanır ve 320×160 mm standart ölçüdedir."),
    "/p10-panel/": dict(risk="yok", brief="b13", title=B("b13", "title"), desc=B("b13", "desc"), h1="P10 LED Panel", demote_h1=True, giris=B("b13", "giris")),
    "/p5-outdoor-rgb-panel/": dict(risk="yok", brief="b14", title=B("b14", "title"), desc=B("b14", "desc"), h1="P5 Dış Mekan RGB LED Panel", demote_h1=True,
                                   giris="P5 dış mekan RGB LED panel, pikselleri arasında 5 mm mesafe bulunan, 320×160 mm ölçüsünde (64×32 piksel) tam renkli LED modüldür. Yaklaşık 5–15 metre izleme mesafesindeki tabela ve dış mekan ekranlar için uygundur. Aşağıdaki teknik bilgiler üretici föyünden alınmıştır."),
    "/p5-indoor-rgb-panel/": dict(risk="yok", brief="b14", title="P5 İç Mekan RGB LED Panel | 320×160 Indoor – LEDAJANS",
                                  desc="P5 iç mekan RGB LED panel: 5 mm piksel aralığı, 320×160 mm, 1/16 tarama. Mağaza ve salon ekranları için teknik föy, uyumlu kartlar ve toptan fiyat teklifi.",
                                  h1="P5 İç Mekan RGB LED Panel", demote_h1=True,
                                  giris="P5 iç mekan RGB LED panel, pikselleri arasında 5 mm mesafe bulunan, 320×160 mm ölçüsünde (64×32 piksel), 1/16 taramalı tam renkli LED modüldür. 5 metreden uzaktan izlenen mağaza ve salon ekranları için ekonomik bir seçenektir. Aşağıdaki teknik bilgiler üretici föyünden alınmıştır."),
    "/p2-vs-p3-led-ekran/": dict(risk="yok", brief="b15", title=B("b15", "title"), desc=B("b15", "desc"), h2_to_h1=B("b15", "h1"), giris=B("b15", "giris"), emoji=True),
    "/cob-ekran/": dict(risk="yok", brief="b16", title=B("b16", "title"), desc=B("b16", "desc"), h1="COB LED Ekran", giris=B("b16", "giris")),
    "/gob-led-ekran/": dict(risk="yok", brief="b17", title=B("b17", "title"), desc=B("b17", "desc"), h1="GOB LED Ekran", giris=B("b17", "giris")),
    "/magaza-vitrin-led-ekran/": dict(risk="yok", brief="b19", title=B("b19", "title"), desc=B("b19", "desc"), h1="Mağaza ve Vitrin LED Ekran", giris=B("b19", "giris")),
    "/kayan-yazi/": dict(risk="yok", brief="b20", title=B("b20", "title"), desc=B("b20", "desc"), h1="Kayan Yazı LED Tabela", demote_h1=True, giris=B("b20", "giris")),
    "/led-ekran-kurulum/": dict(risk="yok", brief="b22", title=B("b22", "title"), desc=B("b22", "desc"), h2_to_h1="LED Ekran Kurulumu", giris=B("b22", "giris"), emoji=True,
                                replace=[("400-800 W/m² arasında değişir",
                                          "modele göre değişir: LEDAJANS ürünlerinde ortalama tüketim 173–213 W/m² (rental) ve 200 W/m² (COB P1.25), maksimum tüketim 380–640 W/m² aralığındadır; dış mekan modellerde parlaklığa bağlı olarak daha yüksektir")]),
    "/kontrol-kartlari/": dict(risk="yok", brief="b23", title=B("b23", "title"), desc=B("b23", "desc"), h1="LED Ekran Kontrol Kartları", giris=B("b23", "giris")),
    "/program-indir/": dict(risk="düşük", brief="b24", title=B("b24", "title"), desc=B("b24", "desc"), h1="LED Ekran Programları – İndir", giris=B("b24", "giris"),
                            not_="Sitenin 2. trafik sayfası. 'hd player' sıralamasına dikkat; tek başına uygulanıp 2 hafta izlenmeli."),
    "/led-ekran-nedir/": dict(risk="yok", brief="b25", title=B("b25", "title"), desc=B("b25", "desc"), giris=B("b25", "giris"), emoji=True),
}

# ---------- bütün sayfalara uygulanan görsel düzeltmeleri (header/footer) ----------
ALT_BY_FILE = {
    "PH1.53-550x632.jpg": "Mimari maket üzerine kurulmuş kavisli iç mekan LED ekran",
    "PH1.53.jpg": "Mimari maket üzerine kurulmuş kavisli iç mekan LED ekran",
    "P3-550x632.jpg": "Sahnede çiçek görüntüsü gösteren iç mekan LED ekran",
    "P3.jpg": "Sahnede çiçek görüntüsü gösteren iç mekan LED ekran",
    "P1.25-2-550x632.jpg": "Toplantı salonunda üç bölümlü iç mekan LED ekran",
    "P1.25-2.jpg": "Toplantı salonunda üç bölümlü iç mekan LED ekran",
    "ec8726e1-1617-438d-927c-6904cf2506f4-550x632.jpg": "Salon sahnesinde duvara monte iç mekan LED ekran",
    "ec8726e1-1617-438d-927c-6904cf2506f4.jpg": "Salon sahnesinde duvara monte iç mekan LED ekran",
    "P2.5-550x632.jpg": "Balo salonunda şelale görüntüsü gösteren geniş iç mekan LED ekran",
    "P2.5.jpg": "Balo salonunda şelale görüntüsü gösteren geniş iç mekan LED ekran",
    "fb8143a3-9d69-45a3-859c-2e2db66c334a-550x632.jpg": "Fuar alanında dikey totem LED ekranlar",
    "fb8143a3-9d69-45a3-859c-2e2db66c334a.jpg": "Fuar alanında dikey totem LED ekranlar",
    "ledarabul.png": "LedAraBul logosu", "kacmasa.png": "Kacmasa logosu",
    "iso-9001-2015-1.webp": "ISO 9001:2015 kalite yönetim sistemi sertifikası",
    "iso-45001-2018-1.webp": "ISO 45001:2018 iş sağlığı ve güvenliği sertifikası",
    "taha-led-14064-1.webp": "ISO 14064-1 sera gazı raporlama uygunluk belgesi",
    "iso-10002-2018-1.webp": "ISO 10002:2018 müşteri memnuniyeti belgesi",
    "iso-14001-2015-1.webp": "ISO 14001:2015 çevre yönetimi sertifikası",
    "iso-27001-2022-1.webp": "ISO/IEC 27001:2022 bilgi güvenliği sertifikası",
    "iso-31000-2018-1.webp": "ISO 31000:2018 kurumsal risk yönetimi belgesi",
    # COB slider ("Slide 1…6")
    "Basliksiz-6-4.png": "COB LED ekran kabininin parçaları: ön panel, modül ve kasa",
    "Basliksiz-6-6.png": "COB LED modülünün ön ve arka yüzü",
    "Basliksiz-6-2.png": "İnce COB LED ekran kabini, ön ve arka görünüm",
    "Basliksiz-6-3.png": "COB LED ekran kabininin ön yüzü",
}
FORCE_ALT = {"Basliksiz-6-4.png", "Basliksiz-6-6.png", "Basliksiz-6-2.png", "Basliksiz-6-3.png"}
LANG_ALT = {"lang-item-tr": "Türkçe", "lang-item-en": "English", "lang-item-de": "Deutsch"}


def fix_alts(soup) -> list[tuple[str, str, str]]:
    changes = []
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        src = img.get("data-src") or img.get("src") or ""
        name = src.split("?")[0].rsplit("/", 1)[-1]
        # COB slider görsellerinde iki alt niteliği var (tarayıcı ilkini, 'Slide N' okur) → her zaman düzelt
        if alt and not alt.lower().startswith("slide") and name not in FORCE_ALT:
            continue
        new = ALT_BY_FILE.get(name)
        if not new:
            li = img.find_parent("li")
            if li:
                for c, v in LANG_ALT.items():
                    if c in (li.get("class") or []):
                        new = v
        if new:
            img["alt"] = new
            changes.append(("Alt metin", f"{name}: '{alt}'", new))
    return changes


def set_meta(soup, attr, key, value):
    tag = soup.find("meta", attrs={attr: key})
    old = tag.get("content") if tag else None
    if tag:
        tag["content"] = value
    else:
        tag = soup.new_tag("meta"); tag[attr] = key; tag["content"] = value; soup.head.append(tag)
    return old


def para_html(soup, text: str, cls: str):
    p = soup.new_tag("p"); p["class"] = cls
    pos = 0
    for m in PH.finditer(text):
        if m.start() > pos:
            p.append(NavigableString(text[pos:m.start()]))
        mk = soup.new_tag("mark"); mk["class"] = "lj-yer-tutucu"; mk.string = m.group(1).strip() or "sizden"
        p.append(mk); pos = m.end()
    p.append(NavigableString(text[pos:]))
    return p


def jsonld(soup, data):
    s = soup.new_tag("script"); s["type"] = "application/ld+json"
    s.string = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    soup.head.append(s)


def apply(path: str, html: str, spec: dict) -> tuple[str, list]:
    soup = BeautifulSoup(html, "html.parser")
    ch: list[tuple[str, str, str]] = []
    if spec.get("title"):
        old = soup.title.get_text(strip=True) if soup.title else ""
        soup.title.string = spec["title"]
        set_meta(soup, "property", "og:title", spec["title"]); set_meta(soup, "name", "twitter:title", spec["title"])
        ch.append(("Title", old, spec["title"]))
    if spec.get("desc"):
        old = set_meta(soup, "name", "description", spec["desc"])
        set_meta(soup, "property", "og:description", spec["desc"]); set_meta(soup, "name", "twitter:description", spec["desc"])
        ch.append(("Meta açıklama", old or "(yok)", spec["desc"]))
    if spec.get("index"):
        old = set_meta(soup, "name", "robots", "index, follow, max-snippet:-1, max-video-preview:-1, max-image-preview:large")
        ch.append(("Robots", old or "(yok)", "index, follow"))
    if spec.get("og_image"):
        old = set_meta(soup, "property", "og:image", spec["og_image"])
        ch.append(("og:image", old or "(yok)", spec["og_image"] + "  (geçici; 1200×630 özel görsel hazırlanmalı)"))
    if spec.get("emoji"):
        n = 0
        for h in soup.find_all(["h1", "h2", "h3"]):
            for s in h.find_all(string=True):
                new = EMOJI.sub("", s)
                if new != s:
                    s.replace_with(new); n += 1
        if n:
            ch.append(("Başlıklardaki emojiler", f"{n} başlıkta emoji", "kaldırıldı"))
    for old_t in spec.get("strip_text", []):
        for s in soup.find_all(string=re.compile(re.escape(old_t))):
            s.replace_with(s.replace(old_t, ""))
        ch.append(("Metin", old_t.strip(), "kaldırıldı"))
    h1s = soup.find_all("h1")
    if spec.get("h2_to_h1"):
        h2 = soup.find("h2")
        old = h2.get_text(" ", strip=True)
        h2.name = "h1"; h2.clear(); h2.append(spec["h2_to_h1"])
        ch.append(("H1 (sayfada yoktu)", f"ilk H2: {old}", spec["h2_to_h1"]))
        h1s = [h2]
    elif spec.get("h1") and h1s:
        old = h1s[0].get_text(" ", strip=True)
        if old != spec["h1"]:
            h1s[0].clear(); h1s[0].append(spec["h1"])
            ch.append(("H1", old, spec["h1"]))
    if spec.get("demote_h1") and len(h1s) > 1:
        for h in h1s[1:]:
            h.name = "h2"
        ch.append(("Fazla H1", f"{len(h1s)} adet H1", "1 H1, diğerleri H2'ye çevrildi"))
    for a, bnew in spec.get("replace", []):
        for s in soup.find_all(string=re.compile(re.escape(a))):
            s.replace_with(s.replace(a, bnew))
            ch.append(("Rakam tutarlılığı", a, bnew))
    if spec.get("giris") and h1s:
        p = para_html(soup, spec["giris"], "lj-onizleme-giris")
        h1s[0].insert_after(p)
        ch.append(("Giriş paragrafı (yeni)", "(yok)", spec["giris"].replace("[[", "«").replace("]]", "»")))
        if spec.get("guncelleme"):
            u = soup.new_tag("p"); u["class"] = "lj-guncelleme"; u.string = "Son güncelleme: Kasım 2026"
            p.insert_after(u); ch.append(("Güncelleme tarihi", "(yok)", "Son güncelleme: Kasım 2026"))
    if spec.get("faq_from_details"):
        sec = soup.find("section", class_="ledajans-projects-faq")
        qa = [{"@type": "Question", "name": d.summary.get_text(" ", strip=True),
               "acceptedAnswer": {"@type": "Answer", "text": d.p.get_text(" ", strip=True)}} for d in sec.find_all("details") if d.summary and d.p]
        jsonld(soup, {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qa})
        ch.append(("Schema", "FAQPage yok", f"FAQPage eklendi ({len(qa)} soru, sayfadaki mevcut SSS'den)"))
    if spec.get("faq_from_sc"):
        qa = []
        for p in soup.find_all("p"):
            st = p.find("strong")
            if st and st.get_text().startswith("S:"):
                q = st.get_text(" ", strip=True)[2:].strip()
                a = p.get_text(" ", strip=True).split("C:", 1)[-1].strip()
                qa.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
        if qa:
            jsonld(soup, {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qa})
            ch.append(("Schema", "FAQPage yok", f"FAQPage eklendi ({len(qa)} soru, sayfadaki S/C metninden)"))
    return str(soup), ch


def main():
    orig = load_originals()
    OUT.mkdir(exist_ok=True)
    report = {"sayfalar": [], "yonlendirmeler": REDIRECTS, "genel_alt": []}
    for path, spec in PAGES.items():
        f = file_of(path)
        html, ch = apply(path, orig[f], spec)
        soup = BeautifulSoup(html, "html.parser")
        alt_ch = fix_alts(soup)
        (OUT / f).write_text(str(soup), encoding="utf-8")
        report["sayfalar"].append({"yol": path, "dosya": f, "risk": spec.get("risk", "yok"), "brief": spec.get("brief"),
                                   "not": spec.get("not_", ""), "degisiklikler": ch, "alt_sayisi": len(alt_ch)})
    s = BeautifulSoup(orig["anasayfa.html"], "html.parser")
    report["genel_alt"] = fix_alts(s)
    (ROOT / "degisiklikler.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(PAGES)} sayfa üretildi → {OUT}")
    for p in report["sayfalar"]:
        print(f"  {p['yol']:45} {len(p['degisiklikler']):2} değişiklik, {p['alt_sayisi']} alt, risk={p['risk']}")


REDIRECTS = {
    "/case/ic-mekan-led-ekran/": "/ic-mekan-led-ekran/", "/case/dis-mekan-led-ekran/": "/dis-mekan-led-ekran/",
    "/case/kontrol-kartlari/": "/kontrol-kartlari/", "/case/rental-ekran/": "/rental-ekran/",
    "/case/ic-mekan-rgb-panel/": "/ic-mekan-rgb-panel/",
    "/led-ekran-kiralama/": "/rental-ekran/", "/led-ekran-tamiri/": "/dip-led-panel-tamiri/",
    "/led-ekran-servis/": "/dip-led-panel-tamiri/", "/p10-panel-kirmizi-4/": "/p10-panel/",
    "/dis-mekan-led-ekranlar/": "/dis-mekan-led-ekran/",
}

if __name__ == "__main__":
    main()
