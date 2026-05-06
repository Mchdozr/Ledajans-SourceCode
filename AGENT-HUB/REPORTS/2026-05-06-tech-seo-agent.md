# ledajans.com Teknik SEO Sağlık Kontrolü (2026-05-06)

Bağlam notu: `AGENT-HUB/STATE.md` ve `AGENT-HUB/TASKS.md` dosyaları repoda bulunamadı; denetim canlı site üzerinden yapıldı.

## 1) Critical

### 1.1 `https://www.ledajans.com` SSL sertifika uyuşmazlığı
- Bulgusu: `www` hostunda TLS doğrulaması başarısız (hostname mismatch), URL güvenli şekilde açılamıyor.
- Etki: `www` varyantına gelen kullanıcı ve bot trafiği kırılır; crawl ve indexleme kaybı, güven kaybı ve potansiyel trafik düşüşü oluşur.
- Önerilen aksiyon: `www.ledajans.com` için SAN içeren geçerli sertifika tanımla ve 301 ile tek kanonik hosta (`https://ledajans.com/`) yönlendir.

### 1.2 Soft 404 problemi (olmayan URL’ler ana sayfaya 301/200 dönüyor)
- Bulgusu: `https://ledajans.com/this-page-definitely-does-not-exist-404-test` isteği gerçek 404 yerine ana sayfaya dönüyor.
- Etki: Google soft-404 algılar, crawl bütçesi boşa gider, alakasız URL’lerin indekslenmesi ve kalite sinyali kaybı oluşur.
- Önerilen aksiyon: Var olmayan URL’lerde doğrudan `404` HTTP kodu + özel 404 şablonu döndür; toplu ana sayfa yönlendirmesini kaldır.

## 2) High

### 2.1 500 hata yönetimi doğrulanamıyor / muhtemel yanlış yönlendirme
- Bulgusu: `/500` isteği de ana sayfaya 301 veriyor; özel hata yönetimi sinyali zayıf.
- Etki: Gerçek sunucu hatalarında botlar doğru hata semantiğini alamaz; geçici sorunlar yanlış içerik sinyali üretir.
- Önerilen aksiyon: Uygulama/web server seviyesinde gerçek `500` yanıtı ve özel 500 sayfası tanımla; 5xx yanıtlarını ana sayfaya yönlendirme.

### 2.2 Önemli landing/case sayfalarında schema eksikliği
- Bulgusu: Örneklenen `/case/...` sayfalarında JSON-LD bulunamadı (`jsonld=0`), blog ve ana sayfada var.
- Etki: Zengin sonuç uygunluğu düşer, varlık/konu ilişkileri arama motorlarına zayıf aktarılır.
- Önerilen aksiyon: Case şablonlarına en az `WebPage` + `BreadcrumbList` + içerik tipine uygun (`Product`/`Service`/`Article`) schema ekle.

## 3) Medium

### 3.1 Sitemap endpoint tutarsızlığı riski
- Bulgusu: `robots.txt` içinde `Sitemap: https://ledajans.com/sitemap-index.php` tanımlı, ayrıca `https://ledajans.com/sitemap.xml` da aktif.
- Etki: Teknik olarak çalışsa da izleme ve hata ayıklamada gereksiz karmaşıklık yaratır.
- Önerilen aksiyon: Tek bir standart sitemap giriş noktası belirle ve robots + Search Console’da aynı endpoint’i kullan.

### 3.2 Canonical standardizasyonu izlenmeli
- Bulgusu: Örneklenen sayfalarda canonical tekil ve doğru; ancak host varyantı (`www`) kritik hatalı olduğu için bütünlük riski var.
- Etki: Host seviyesinde canonical sinyali kırılırsa URL birleştirme kalitesi düşebilir.
- Önerilen aksiyon: Sertifika + 301 host konsolidasyonu düzeltildikten sonra canonical’ı tüm şablonlarda otomatik test ile doğrula.

## 4) Hızlı kazanımlar (quick wins)

1. Search Console’da `https://ledajans.com/` için URL Denetimi ile soft-404 örneklerini yeniden test et ve düzeltme sonrası yeniden gönder.
2. Nginx/WordPress kuralında “olmayan URL -> ana sayfa” kuralını kaldırıp standart 404 akışını aktif et.
3. `www` hostu için sertifika eklendikten sonra `curl -I https://www.ledajans.com` çıktısını 301 + geçerli TLS olacak şekilde doğrula.
4. Case şablonuna minimum JSON-LD ekleyip Rich Results Test ile canlı doğrulama yap.
5. Teknik takip için haftalık otomatik kontrol listesi ekle: robots, sitemap, canonical tekilliği, 404/500 status, schema varlığı.

## Kontrol özeti (ham bulgular)
- Redirect: `http://ledajans.com` -> `301` -> `https://ledajans.com/` (doğru)
- Robots: `200` (`/robots.txt` erişilebilir)
- Sitemap: `200` (`/sitemap.xml`, 153 URL tespit edildi)
- Canonical: Örneklenen 5 URL’de tek canonical ve self-referans
- Schema: Ana sayfa/blogda var, case sayfalarında eksik
- 404: Gerçek 404 yerine ana sayfaya yönlendirme (kritik)
- 500: Doğrulama URL’i de ana sayfaya yönleniyor (yüksek risk)
