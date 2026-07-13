# İndeksleme Temizliği — Aksiyon Planı (2026-07-12)

Kaynak: `INDEXING-TRIAGE-2026-06-05.md` (463 URL, ağırlık: 390 "Tarandı - dizine eklenmedi").
Amaç: tarama bütçesini `led ekran` head-term ve para sayfalara yönlendirmek; ince/duplike URL gürültüsünü azaltmak.

## 1. Güçlendirilen değerli URL'ler (iç link ile)
Bu turda hub `/led-ekran/` ve para sayfalara iç link akışı artırıldı:
- Anasayfa `widget-3.html` → `/led-ekran/` (contextual anchor: "led ekran çözümleri").
- `Blog/dis-mekan-led-ekran-fiyatlari-2026-rehber.html` → `/led-ekran/` (anchor: "led ekran modelleri").
- Yeni `Urunlerimiz/Dis-Mekan-Led-Ekran/dis-mekan-led-ekran-text.html` → hub + tüm para sayfalara "İlgili Ürün ve Sayfalar" kümesi.
- Hub sayfasına teknik karşılaştırma tablosu içinde ic/dis/rental/cob linkleri.

Etki: "Tarandı - dizine eklenmedi" durumundaki değerli ürün URL'leri iç link sinyali kazanır → indekslenme olasılığı artar.

## 2. robots.txt — tarama bütçesi koruması (uygulandı)
Eklenen `Disallow` kuralları parametreli/duplike URL taramasını keser:
`/*?s=`, `/*&s=`, `/*?replytocom=`, `/*?add-to-cart=`, `/*?orderby=`, `/author/`, `/wp-json/oembed/`.

## 3. noindex adayları (RankMath → Advanced → Robots Meta: noindex)
İnce veya arama-değeri düşük, tarama bütçesi tüketen sayfalar:
- Site içi arama sonuçları (`/?s=...`) — robots ile de engellendi.
- Etiket (tag) arşivleri ve `attachment` (medya ek) sayfaları — RankMath global "Noindex" ile kapatılmalı.
- Tarih (date) arşivleri.
- Yazar arşivi (`/author/`) — robots ile engellendi; ayrıca noindex önerilir.

> Not: `/en/`, `/de/` dil varyasyonları noindex YAPILMAMALI (uluslararası kapsam). Bunun yerine hreflang tutarlılığı korunur ve ana TR sitemap'te öncelik TR URL'lerdedir.

## 4. 301 adayları (404 / yönlendirme hataları)
`INDEXING-TRIAGE-2026-06-05.md` 404 listesi (`/case/`, `/en/case/...`, `/de/case/...`):
- Backlink/trafik olanlar → ilgili TR/EN hedefe 301.
- Uygulama dosyaları: `scripts/htaccess-BLOG-301-INSERT.txt`, `scripts/plesk-nginx-directives-MERGED.conf`.
- "Yeniden yönlendirme hatası" (9) ve "5xx" (2): sunucu/redirect zinciri düzeltilmeli (tek hop, 200 hedef).

## 5. Canonical tutarlılığı
- `Katalog/pages/15-arka-kapak.html` içindeki `https://www.ledajans.com` → `https://ledajans.com` (non-www kanonik host) ile hizalanmalı. (`audit-internal-links.py` bulgusu.)
- Kanonik host politikası: `robots.txt` başlığında ve tüm iç linklerde non-www.

## 6. Sitemap hijyeni (`sitemap_index.xml`)
- Yalnızca kanonik, indekslenebilir para/blog/rehber URL'leri kalmalı.
- noindex işaretlenen tag/attachment/date/author URL'leri sitemap'ten çıkarılmalı (RankMath bunu otomatik yapar; kontrol edilmeli).
- Değişiklik sonrası GSC → Sitemaps yeniden gönder; `led-ekran` ve para sayfaları için URL Inspection → "Request Indexing".

## 7. Doğrulama
- `python3 AGENT-HUB/audit-internal-links.py` → 0 yeni canonical ihlali (mevcut tek bulgu: madde 5).
- Deploy sonrası: `scripts/seo-smoke-test.ps1` (robots + sitemap + money pages 200).
- 14 gün GSC "Sayfa indeksleme" trend takibi.
