# tester.ledajans.com → ledajans.com: İngilizce ve Almanca sayfaların taşınması

İnceleme: 27.11.2026 · Dosyalar: `sayfa-siniflandirma.csv`, `plesk-nginx-yonlendirmeler.conf`

## Mevcut durum
| | Sayı |
|---|---|
| Tester EN/DE sayfası | 295 (EN 142, DE 153) |
| Canlıda zaten olan (aynı adres) | 94 → güncelleme |
| Canlıda olmayan | 199 → yeni |
| Sadece canlıda olan | 11 (`/de/uber-uns/`, `/de/gob-vs-cob-smd-3/` gibi eski adresler) |
| Canlı EN/DE payı (GSC, Mart–Haziran) | gösterimin ~%8'i, tıklamanın ~%5'i |

Tester'ın kendisi güvenli bir hazırlık ortamı: `robots.txt` her şeyi kapatıyor, sayfalar `noindex, nofollow`. Google'da görünmüyor, çift içerik sorunu yok.

## Taşınırsa ne olur?
**"led ekran" (Türkçe) sıralaması:** Türkçe sayfalara dokunulmazsa doğrudan etki yok. Tek dolaylı risk şu: yüzlerce yeni sayfa bir anda eklenir ve içlerinde çevrilmemiş metin olursa, Google sitenin genel kalitesini düşük değerlendirebilir. Bunu aşağıdaki iki kural önler:
1. Çevrilmemiş 12 sayfa taşınmaz.
2. Sayfalar dalgalar halinde taşınır.

**İngilizce/Almanca:** Eski adresler bugün `/projeler/` sayfasına ya da anasayfaya gidiyor. Örnekler: `/en/case/indoor-led-display/` (946 gösterim), `/de/p10-panel-3/` gibi `-3` ekli adresler. Bunlar doğru sayfaya yönlenince dağılmış güç toplanır. 199 yeni sayfa Almanya ve uluslararası uzun kuyruk aramalarına açılır.

**GEO:** ChatGPT, Perplexity ve Gemini İngilizce sorularda İngilizce kaynağı tercih ediyor. Bugün İngilizce içeriğin çoğu eksik. Taşıma, LEDAJANS'ın İngilizce ve Almanca sorularda da alıntılanabilmesini sağlar.

## Bulunan sorunlar
| Sorun | Sayı | Ne yapılmalı |
|---|---|---|
| Gövde metni Türkçe kalmış | 12 sayfa (liste CSV'de, "ÖNCE ÇEVİR") | Çevrilmeden taşınmaz. 3'ü (`/en/airport-led-screen/`, `/de/flughafen-led-display/`, `/de/was-ist-gob-led/`) canlıda da aynı halde |
| İnce sayfa (<300 kelime) | 28 | 2. dalgada; mümkünse önce kısa bir açıklama eklenir |
| Birden fazla H1 | 16 | Taşımadan önce fazlası H2 yapılır |
| İç linkler `tester.ledajans.com`'a gidiyor | sayfa başına ~244 | Taşınan içerikte `tester.ledajans.com` → `ledajans.com` arama-değiştirme |
| noindex + robots Disallow | tümü | Taşınan sayfa canlıda `index, follow` olmalı; tester ayarı taşınmamalı |
| Canonical boş | tümü | Canlıda Rank Math kendi adresini canonical vermeli (taşıma sonrası 5 sayfada kontrol) |
| hreflang tester adreslerini gösteriyor | 285 | Canlıda tr ↔ en ↔ de çift yönlü olmalı. Türkçe karşılıkların hepsi (136) canlıda 200 dönüyor ✓ |

## En büyük risk: Türkçe sayfaların üzerine yazılması
"Tüm siteyi tester'dan canlıya it" türü bir taşıma (tam veritabanı push, All-in-One Migration ve benzerleri) **Türkçe sayfaları da tester'daki haliyle değiştirir.** Bu, "led ekran" sıralamasını doğrudan riske atar. Taşıma **yalnızca EN/DE yazı ve sayfaları** kapsamalı:
- Elementor verisi (`_elementor_data`), Rank Math alanları, Polylang dil bilgisi ve çeviri bağlantıları (TR ↔ EN ↔ DE) birlikte taşınmalı.
- Önerilen yöntem: iki sitenin REST API'si üzerinden sayfa sayfa kopyalayan bir script (depoda benzer `deploy-*.py` scriptleri var). Her iki sitede uygulama şifresi gerekir. İsterseniz yazarım.

## Güvenli taşıma sırası
**0. Hazırlık**
- Hostingden tam yedek (veritabanı + dosyalar). Mevcut HTML yedeği de var: `YEDEK/2026-11-24/`.
- Güncel GSC dökümü alınır (taban ölçüm).

**1. Tester'da düzeltme**
- 12 sayfa çevrilir.
- 16 sayfanın fazla H1'i H2'ye çevrilir.
- Taşınacak içerikte `tester.ledajans.com` → `ledajans.com` değişikliği yapılır.

**2. Dalga 1, hafta 1: ana sayfalar ve rehberler (~60 sayfa)**
- EN/DE anasayfa, iç mekan, dış mekan, kiralama, COB, GOB, RGB panel, kontrol kartları, fiyat rehberleri, şehir sayfaları, hakkımızda, iletişim.
- Canlıda zaten olan 94 sayfanın güncellemesi de bu dalgada. Adresleri aynı kaldığı için risk düşük.
- Hedefler canlıda 200 dönünce `plesk-nginx-yonlendirmeler.conf` eklenir.

**3. Dalga 2, hafta 2–3: model ve ürün sayfaları (~180 sayfa, haftada en fazla ~90)**
- Kontrol kartı modelleri, panel modelleri, rental ve COB modelleri.

**4. Dalga 3, hafta 4+: ince sayfalar (28)**
- Açıklama eklendikten sonra taşınır.

**Her dalgadan sonra:**
- Sitemap kontrol edilir.
- Bing IndexNow (Rank Math Instant Indexing) çalıştırılır.
- 5 örnek sayfa GSC URL denetimine sokulur: canonical, hreflang ve index durumu kontrol edilir.

## İzleme ve geri alma
- **Türkçe:** "led ekran" kümesinde 14 gün boyunca 2 basamaktan fazla düşüş olursa son dalganın sayfaları **noindex'e çekilir** (silinmez), sebebi incelenir.
- **EN/DE:** ilk 4 haftada gösterim ve indekslenen sayfa sayısı izlenir.
- Taşıma sonrası `llms.txt` içindeki `/en/home-en/` ve `/de/home-de/` adresleri `/en/` ve `/de/` yapılır; EN/DE ana sayfalar eklenir.
