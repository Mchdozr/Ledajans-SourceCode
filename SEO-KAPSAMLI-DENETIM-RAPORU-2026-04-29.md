# LEDAJANS SEO Kapsamli Canli Denetim Raporu

Tarih: 2026-04-29  
Site: https://ledajans.com

## 1) Yonetici Ozeti

- Teknik SEO temeli guclu (canonical/hreflang/schema mevcut, Lighthouse SEO 100/100).
- En buyuk problem mobil performans (LCP/TBT yuksek), bu da organik tiklama ve donusumu dolayli etkiliyor.
- GSC verisine gore ortalama konum iyi ama CTR dusuk (gorunurluk var, tiklama zayif).
- AI gorunurlugu icin temel schema iyi; fakat `llms.txt` ve AI-odakli icerik yapisi eksik.

## 2) Uygulanan Testler

- Lighthouse full audit (mobile + desktop)
- HTTP header analizi (cache, guvenlik, redirect)
- `robots.txt`, sitemap endpoint ve sitemap icerik analizi
- 80 URL orneklemde title/meta description/H1 kalite taramasi
- SERP gorunurluk taramasi (ticari sorgular)
- AI gorunurluk kontrolleri (`llms.txt`, schema, bot politikasi)

## 3) Performans Sonuclari (Canli)

### Mobile (Lighthouse)
- Performance: 42
- Accessibility: 90
- Best Practices: 100
- SEO: 100
- FCP: 5.5s
- LCP: 10.9s
- TBT: 710ms
- CLS: 0.001

### Desktop (Lighthouse)
- Performance: 92
- Accessibility: 91
- Best Practices: 100
- SEO: 100
- FCP: 1.0s
- LCP: 1.3s
- TBT: 10ms
- CLS: 0.007

### Mobile Darbogazlar
- Unused CSS: ~131 KiB
- Unused JavaScript: ~159 KiB
- Main-thread is yuku yuksek

## 4) Teknik SEO Bulgulari

### Guclu Yanlar
- Canonical duzeni mevcut
- Hreflang etiketleri mevcut (cok dilli yapi)
- JSON-LD zengin (Organization, FAQPage, LocalBusiness, Service, VideoObject vb.)
- Desktop Core Web Vitals guclu

### Risk / Sorunlar
1. Cift `Cache-Control` header goruluyor (tutarsizlik riski).
2. `robots.txt` kurallari fazla sert:
   - `Disallow: /wp-content/plugins/`
   - `Disallow: /*.php$`
3. `https://www.ledajans.com` tarafinda sertifika/host dogrulama riski (curl tarafinda hata alindi, redirect olsa da zincir kontrolu onerilir).
4. Ana sayfa meta description uzun (SERP'te kirpilma olasiligi).

## 5) On-Page Kalite Taramasi (Ilk 80 URL)

- Title kisa (<30): 11
- Title uzun (>65): 34
- Description kisa (<70): 20
- Description uzun (>170): 24
- Description eksik: 1
- H1 sayisi 1 degil: 25 URL

Sonuc: Snippet kalitesi ve baslik hiyerarsisinde standart disi dagilim var.

## 6) Guclu Anahtar Kelime Kumeleleri

Canli SERP + URL mimarisi + icerik sinyallerine gore guclu alanlar:

- led ekran
- dis mekan led ekran / outdoor led ekran
- ic mekan led ekran / indoor led ekran
- rental ekran / kiralik led ekran
- rgb panel
- colorlight kontrol karti
- huidu kontrol karti
- p10 panel ve teknik model sorgulari

Not: Kesin "en guclu ilk 10 sorgu" listesi icin Search Console sorgu export'u (impression/click/position) gerekir.

## 7) CTR ve Musteri Cekme Analizi

Mevcut durum (paylasilan GSC ozetine gore):
- Gosterim: 1.26K
- Tiklama: 17
- CTR: %1.3
- Ortalama konum: 3.7

Yorum:
- Konum fena degil, CTR dusuk.
- Snippet (title + description) ve sorgu-niyet uyumu gelistirilmeli.

## 8) AI Gorunurluk Analizi

### Mevcut
- Schema altyapisi guclu
- Hizmet ve urun tarafinda teknik icerik var

### Eksikler
- `llms.txt` yok (istek ana sayfaya donuyor)
- AI botlari icin net politika yok (`GPTBot`, `Google-Extended`, `CCBot`, `PerplexityBot`)
- AI cevaplarina uygun kisa, dogrudan, kanitli bilgi bloklari sinirli

### Oneri
- `/llms.txt` olustur (sirket ozeti, urunler, servis alanlari, iletisim, guven sinyalleri)
- SSS ve "fiyat/kurulum/garanti" bloklarini netlestir
- Urun sayfalarina kisa karar verdirici ozet + teknik tablo + CTA standardi ekle

## 9) Onceliklendirilmis Aksiyon Plani

### P0 (Hemen)
1. Mobil LCP/TBT iyilestirme (hero ust alan optimizasyonu, agir JS/CSS azaltimi)
2. `robots.txt` sadeleştirme (render engelleyen kurallari gozden gecir)
3. `www` HTTPS sertifika ve host kapsama duzeltmesi
4. Ticari niyetli title/meta yeniden yazimi (2026 + Istanbul + CTA)

### P1 (1-2 Hafta)
1. H1 standardizasyonu (her sayfada 1 adet, niyet odakli)
2. Kisa/uzun title-description normalizasyonu
3. Düşük CTR sorgular icin sayfa bazli snippet revizyonu

### P2 (2-4 Hafta)
1. `llms.txt` + AI crawler policy
2. "Fiyat", "kurulum", "bakim", "karsilastirma" icerik cluster'lari
3. Donusum odakli landing iyilestirmeleri (teklif formu, guven rozetleri, referanslar)

## 10) Sonuc

LEDAJANS teknik olarak guclu bir SEO temelinde. En buyuk buyume potansiyeli:
- Mobil performans (ozellikle LCP/TBT),
- CTR optimizasyonu,
- AI gorunurluk katmani.

Bu uc alan birlikte ele alindiginda organik tiklama ve ticari donusumde net artis beklenir.

