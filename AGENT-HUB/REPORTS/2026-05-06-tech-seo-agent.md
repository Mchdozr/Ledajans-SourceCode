# ledajans.com Teknik SEO Raporu (2026-05-06)

## Critical

### [BLOCKER] AGENT-HUB/TASKS.md dosyası bulunamadı
- Bulgu: Kural gereği görev kaynağı olması gereken `AGENT-HUB/TASKS.md` repoda yok.
- Önerilen aksiyon: `AGENT-HUB/TASKS.md` dosyasını oluşturup görev tanımını netleştir; rapor scope’unu bu dosyaya göre yeniden doğrula.

### [BLOCKER] `https://www.ledajans.com` SSL sertifika uyuşmazlığı
- Bulgu: `www` hostu TLS doğrulamasında hostname mismatch veriyor.
- Önerilen aksiyon: `www.ledajans.com` için geçerli SAN içeren sertifika tanımla ve `https://ledajans.com/` adresine 301 zorla.

### [BLOCKER] Soft 404 (olmayan URL ana sayfaya dönüyor)
- Bulgu: Test edilen olmayan URL gerçek 404 yerine ana sayfaya yönleniyor.
- Önerilen aksiyon: Olmayan URL’lerde doğrudan `404` kodu + özel 404 template döndür; toplu homepage redirect kuralını kaldır.

## High

### 500 hata akışı yanlış yönlendirme riski
- Bulgu: `/500` isteği de ana sayfaya 301 veriyor, gerçek 5xx davranışı doğrulanamıyor.
- Önerilen aksiyon: Sunucuda gerçek `500` yanıtı ve özel 500 sayfası tanımla; 5xx durumlarını ana sayfaya yönlendirme.

### Schema eksikliği (`/case/*` sayfaları)
- Bulgu: Örneklenen case URL’lerinde JSON-LD bulunamadı.
- Önerilen aksiyon: Case şablonlarına minimum `WebPage`, `BreadcrumbList` ve uygun içerik tipi (`Service`/`Product`) schema ekle.

## Medium

### Sitemap endpoint standardizasyonu
- Bulgu: `robots.txt` içinde `sitemap-index.php` var, ayrıca `sitemap.xml` de aktif.
- Önerilen aksiyon: Tek sitemap endpoint standardı belirle ve robots + Search Console’da aynı endpoint’i kullan.

### Redirect chain ve canonical bütünlüğü için otomatik kontrol eksik
- Bulgu: Örneklemde canonical self-referans doğru, ancak host/redirect sorunları nedeniyle sinyal kırılması riski var.
- Önerilen aksiyon: CI veya cron ile haftalık kontrol ekle (redirect chain, canonical tekilliği, 404/500 status, schema varlığı).
