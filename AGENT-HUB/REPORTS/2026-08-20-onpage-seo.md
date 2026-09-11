# On-page SEO — `/gob-led-ekran/` metin widget

Tarih: 2026-08-20  
Dosya: `Urunlerimiz/Gob-Led-Ekran/gob-led-ekran-text.html`  
Hedef KW: `gob led ekran`  
Kapsam: Rank Math içerik uyarıları (kod yazılmadı)

## Query Mapping

| Intent / sorgu | Hedef URL | Widget rolü |
|---|---|---|
| gob led ekran (ticari) | `/gob-led-ekran/` | Para sayfa — tanım kısa, satış/pitch/teklif uzun |
| gob led nedir | `/gob-led-nedir/` | Sözlük; burada 1 iç link |
| gob vs cob / smd | `/gob-vs-cob-smd/` | Karşılaştırma; burada 1 iç link |
| gob panel / RGB GOB SKU | `/ic-mekan-rgb-panel/` | Modül toptan; ekran ≠ panel ayrımı |
| iç mekan kasa | `/ic-mekan-led-ekran/` | Tam ekran hub |
| cob premium | `/cob-ekran/` | Alternatif paket |
| kiralama / taşıma | `/rental-ekran/` | **Eksik** |
| rehber | `/blog/gob-led-ekran-ne-zaman-tercih-edilir/` veya `/blog/` | **Eksik** |

## Page-Level Gaps

Kaynak: widget HTML (style hariç ~**161 kelime**; Rank Math 151 — tablo/H2 farkı). Tam sayfa hero CSS bg + SSS ayrı; Rank Math “content length” bu widget’ı görüyor.

| Rank Math | Durum | Revizyon |
|---|---|---|
| 151 kelime → 600+ | Fail | Widget gövdesini **620–700** kelimeye çıkar (SSS’ye güvenme) |
| Giden/harici link yok | Fail | 1 harici: Wikipedia LED display |
| Tüm harici nofollow | Fail (harici yok) | Wikipedia **dofollow** — `rel="noopener"`; **nofollow yok** |
| Rich media / `<img>` yok | Fail | Gerçek `<img>`; hero `background-image` sayılmaz |
| İlk 100 kelime KW | **Pass** | H2 + ilk cümlede var; açılışı koru |
| H2 KW | **Pass** | `GOB LED Ekran – Glue on Board` |
| Alt KW | Fail | `<img alt>` içinde tam KW |
| Yoğunluk | ~%2,5 (4/161) — kısa metinde şişik | 620+ kelimede **7–9** tam eşleşme → **%1,1–1,5** |
| İç link | 6/8 | `rental-ekran` + blog ekle |

Mevcut iç linkler: `ledajans.com/`, `/gob-led-nedir/`, `/ic-mekan-rgb-panel/`, `/gob-vs-cob-smd/`, `/iletisim/`, `/ic-mekan-led-ekran/`, `/cob-ekran/`.

H1 dokunma (hero). Widget tek H2. CSS: `control-cards-*`, font inherit, CTA `control-cards-link` (#F46F2C).

## On-Page Update Draft

**Görsel (zorunlu, mevcut medya):**  
`https://ledajans.com/wp-content/uploads/2025/12/Basliksiz-1-6.png`  
Alt: `GOB LED ekran Glue on Board korumalı yüzey`  
Caption: epoksi düz yüzey, alçak montaj / temas.  
`loading="lazy"` `width="900"` `height="500"`; `src` hero ile aynı dosya — CSS bg yetmez.  
Yedek (daha az GOB-spesifik): `https://ledajans.com/wp-content/uploads/2022/12/Arka-plani-kaldir-projesi-2-9.png`

**Harici (1, dofollow):**  
`https://en.wikipedia.org/wiki/LED_display` — anchor `Wikipedia LED display`  
`target="_blank" rel="noopener"` — **nofollow ekleme** (ic-mekan widget’taki nofollow bu uyarıyı üretir).

**İç link (anchor çeşitliliği, 1’er):**

| Hedef | Anchor |
|---|---|
| `/ic-mekan-led-ekran/` | iç mekan LED ekran |
| `/gob-led-nedir/` | GOB LED nedir |
| `/gob-vs-cob-smd/` | GOB vs COB vs SMD |
| `/ic-mekan-rgb-panel/` | iç mekan RGB GOB paneller |
| `/iletisim/` | teklif alın / fiyat alın |
| `/cob-ekran/` | COB ekran |
| `/rental-ekran/` | rental ekran |
| `/blog/gob-led-ekran-ne-zaman-tercih-edilir/` | GOB LED ekran ne zaman tercih edilir (veya `/blog/`) |

**KW yerleri (tam “gob led ekran”, 7–9 kez):** 1) H2 2) ilk cümle 3) ilk 100 kelime içinde 2. kez 4) H3 “Neden GOB LED ekran?” 5) kullanım gövdesi 6) kapanış/teklif 7) img alt. Tablo başlığı “GOB” tek başına sayılmaz.

**Bölüm iskeleti (~650 kelime, H2 tek):**  
Giriş (KW + LEDAJANS + pitch P1.25–P2.5) → `<img>` → H3 Neden GOB LED ekran? → H3 GOB vs SMD vs COB (tablo + Wikipedia) → H3 Kullanım / pitch → H3 Bakım-maliyet (modül bazlı) → H3 Teklif (iletişim, 25 yıl, 2 yıl garanti) → ilgili sayfalar listesi.

**CTA:** `control-cards-highlight` + `control-cards-link` → `/iletisim/` “Fiyat alın”. Yeni CSS yok.

## Rank Math checklist (uygulama sonrası)

- [ ] ≥ 600 kelime (widget gövdesi)
- [ ] İlk 100 kelimede `gob led ekran`
- [ ] H2’de KW (mevcut H2 kalsın)
- [ ] En az bir H3’te KW
- [ ] `<img alt>` içinde KW
- [ ] Yoğunluk %1–1,5 (7–9 / ~650)
- [ ] 8 iç link hedefi
- [ ] 1 dofollow Wikipedia
- [ ] H1 hero’da tek; widget H1 yok
- [ ] Canlı meta değişikliği yok (onay + dry-run gerekir)

## Deferred New Content

- Yeni blog / yeni odak KW yok; mevcut `/blog/gob-led-ekran-ne-zaman-tercih-edilir/` yeterli.
- Title/meta bu turda yok; içerik skoru önce.
- `teknik-destek-scaled.png` GOB yüzeyi değil — kullanma.
