# On-page SEO — `/gob-led-nedir/` sözlük

Tarih: 2026-08-20  
Dosya: `SEO-Icerik-Widgets/sozluk/gob-led-nedir.html`  
Canlı: `https://ledajans.com/gob-led-nedir/`  
Odak KW: **gob led nedir**  
Kapsam: Rank Math içerik + görsel CSS; **kod yazılmadı**. Canlı meta yok.

## Query Mapping

| Intent / sorgu | Hedef URL | Bu sayfa |
|---|---|---|
| gob led nedir / gob nedir | `/gob-led-nedir/` | **Tanım / sözlük** — birincil |
| gob led ekran (ticari) | `/gob-led-ekran/` | Hub’a 1–2 link; burada hedefleme yok |
| gob vs cob / smd | `/gob-vs-cob-smd/` | Kısa fark + 1 link |
| ne zaman tercih | `/blog/gob-led-ekran-ne-zaman-tercih-edilir/` | 1 link |
| rental / taşıma | `/rental-ekran/` | 1 link |
| SMD tanımı | `/smd-led-nedir/` | 1 link |
| pitch | `/pitch-led-nedir/` | 1 link |

Cannibal: H2/title/odak **yalnızca** `gob led nedir`. “GOB LED ekran” yalnızca hub anchor’ında.

## Page-Level Gaps

| Rank Math / kural | Durum | Revizyon |
|---|---|---|
| ≥600 kelime | **Pass** (~900–1100 görünür) | 650–750’ye sıkıştır (vs bölümlerini kısalt → karşılaştırma sayfasına bırak) |
| İlk 100 kelime KW | **Fail** | Gövde “GOB LED (Glue…)” ile açılıyor; tam 3’lü yok. H2 yetmez. |
| H2 başında KW | **Pass** | `GOB LED Nedir? Dayanıklılık…` kalsın |
| Alt KW | **Fail** | `GOB LED koruma teknolojisi` — “nedir” yok |
| Yoğunluk %1–1,5 | **Fail** | Tam “gob led nedir” = **1** (yalnız H2). ~1000 kelimede %0,1 |
| `<img>` rich media | Pass (yanlış dosya) | `teknik-destek-scaled.png` **yasak** |
| Harici dofollow Wikipedia | **Fail** | Yok. ledarabul `noopener noreferrer` — Wikipedia sayılmaz |
| Inline CSS bölüm 13 | **Fail** | `<style>` yok; global Ek CSS’e bağlı |
| Widget H1 | **Pass** | Yok; WP H1 ayrı |

## Kısa checklist (uygulama)

### 1) İlk 100 kelime
İlk cümle: **GOB LED nedir** + Glue on Board + LEDAJANS. 2. kez aynı 100’de (2. cümle veya 2. p). Hub linki 2. paragrafta.

Taslak açılış: *“**GOB LED nedir?** SMD LED modül yüzeyine şeffaf epoksi dökülerek kapsüllerin kapatılmasıdır. **GOB LED nedir** sorusu paketleme değil, son işlem (post-process) tanımıdır.”*

### 2) H2
Mevcut kalsın: `GOB LED Nedir? Dayanıklılık Teknolojisi ve Avantajları`  
Başka H2’ye ticari “GOB LED ekran” koyma. İsteğe bağlı H2 gövde: `#gob-tanim` → “GOB LED nedir teknik tanımı”.

### 3) Alt + görsel URL
**Yasak:** `https://ledajans.com/wp-content/uploads/2026/04/teknik-destek-scaled.png`  
**Zorunlu:** `https://ledajans.com/wp-content/uploads/2025/12/Basliksiz-1-6.png`  
Alt: `GOB LED nedir Glue on Board koruma katmanı`  
`loading="lazy"` `width="900"` `height="500"` `class="aligncenter"`  
`<a href="https://ledajans.com/gob-led-ekran/">` (hub, görsel dosyasına değil)

### 4) Yoğunluk (650 kelimede)
Hedef: **8–10** tam eşleşme `gob led nedir` → **%1,2–1,5** (650×0,01=6,5; 650×0,015=9,75).  
7 altı zayıf; 11+ doldurma. “GOB LED” tek başına **sayılmaz**.

Yerler: (1) H2 (2) cümle 1 (3) ilk 100 2. kez (4) `#gob-tanim` H2/ilk cümle (5) avantaj veya kullanım gövdesi (6) sonuç (7) SSS 1. soru (8) alt — Rank Math alt’ı ayrı sayabilir; gövdeye 7–8 koy.

### 5) Harici
`https://en.wikipedia.org/wiki/LED_display` — anchor `Wikipedia LED display`  
`target="_blank" rel="noopener"` — **nofollow yok** (gob-vs sayfasındaki nofollow kopyalanmasın).

### 6) İç link listesi (1’er, çeşit anchor)

| Hedef | Anchor |
|---|---|
| `/gob-led-ekran/` | GOB LED ekran (hub; giriş + ilgili) |
| `/gob-vs-cob-smd/` | GOB vs COB vs SMD |
| `/smd-led-nedir/` | SMD LED nedir |
| `/pitch-led-nedir/` | pitch nedir |
| `/ic-mekan-led-ekran/` | iç mekan LED ekran |
| `/dis-mekan-led-ekran/` | dış mekan LED ekran |
| `/rental-ekran/` | rental ekran |
| `/blog/gob-led-ekran-ne-zaman-tercih-edilir/` | GOB LED ekran ne zaman tercih edilir |
| `/led-ekran/` | LED ekran çözümleri |
| `/` | LEDAJANS |
| `/iletisim/` | iletişim / FİYAT ALIN |

Kaldır/azalt: görsel `href` = png. ledarabul isteğe bağlı (Wikipedia asıl harici). Self `/gob-led-nedir/` yok.

### 7) CSS (görsel; Visual-UX ile aynı)
Widget başına `<style>` = `Ek-CSS-final.css` **bölüm 13** (`.ledajans-seo-article`, H2 turuncu çizgi, CTA `#f46f2c`, img radius 0.75rem).  
`font-family: inherit` — tema **Kumbh**; Huidu `ui-sans-serif` kopyalanmasın. Global Ek CSS’e dokunma.

## On-Page Update Draft

Title (mevcut Rank Math, bu turda değiştirme): `GOB LED Nedir? Glue on Board Teknolojisi - LEDAJANS` (~52 kr).  
Meta HTML yorumunu Rank Math ile hizala: KW başta, “GOB LED ekran” snippet’te yok.

İskelet (~650–750 kelime): H2 KW → 2 p (KW×2 + hub + Wikipedia) → TOC → `<img>` Basliksiz-1-6 → tanım → üretim (kısa) → avantaj → vs SMD/COB **2–3 cümle + karşılaştırma linki** → kullanım → ne zaman → sonuç + CTA → ilgili → 4 SSS.

## Rank Math checklist (uygulama sonrası)

- [ ] 650–750 kelime (widget)
- [ ] İlk 100’de `gob led nedir` (gövde, 2 kez)
- [ ] H2 başında KW
- [ ] Alt tam KW; src = Basliksiz-1-6.png
- [ ] 8–10 tam eşleşme (%1,2–1,5)
- [ ] Wikipedia dofollow
- [ ] İç link tablosu
- [ ] Inline bölüm 13 + font inherit
- [ ] Hub cannibal yok
- [ ] Canlı meta yok (onay + dry-run)

## Deferred New Content

- Yeni odak KW / yeni URL yok.
- Title/meta canlı bu turda yok.
- `/sozluk/gob-led-nedir/` 301 ayrı (tech-seo).
