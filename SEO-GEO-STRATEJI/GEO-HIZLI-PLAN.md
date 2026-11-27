# LEDAJANS — GEO Hızlı Plan (düşük risk, görünüm değişmez)

Hazırlanma: 27.11.2026 · Hazır dosyalar: `SEO-GEO-STRATEJI/hazir/`

**Hedef:** ChatGPT, Gemini, Perplexity, Copilot ve Google AI özetlerinde LEDAJANS'ın anılması ve link alması.
**Kısıt:** "led ekran" ve türevlerinde sıralama düşmeyecek; yazı stili ve sitenin görünümü değişmeyecek.

## Dokunulmayacaklar (sıralama riski)
- Anasayfa ve `/led-ekran/`: title, H1, görünen metin, URL.
- Hiçbir sayfanın URL'si, tasarımı, yazı tipi ve renkleri.
- Sayfa silme ve birleştirme yok; toplu iç link metni değişikliği yok.
- Aynı haftada birden fazla adım yok. Her adımdan sonra 7–14 gün izleme.

## Geri alma kuralı
"led ekran", "led ekran fiyatları", "iç/dış mekan led ekran", "led ekran kiralama", "led ekran panel" kelimelerinden birinde GSC ortalama sırası **14 gün boyunca 2 basamaktan fazla** düşerse son adım geri alınır. Yedek: `YEDEK/2026-11-24/`.

---

## Adım 0 — Başlangıç ölçümü (gün 1) · risk: yok
1. GSC → Performans → son 3 ay → **Sorgular** ve **Sayfalar** CSV'sini indir. Depoya `AGENT-HUB/DATA/gsc-2026-11-27/` olarak koy (karşılaştırma tabanı).
2. `hazir/ai-gorunurluk-olcum.csv` içindeki 20 soruyu ChatGPT, Gemini, Perplexity, Copilot ve Google'da sor. Her hücreye şunlardan birini yaz: `link` (LEDAJANS linki var) / `anıldı` (link yok) / `yok`. Ayda bir tekrarlanır.

## Adım 1 — Görünmez teknik düzeltmeler (hafta 1) · risk: yok
| # | İş | Neden | Nasıl |
|---|---|---|---|
| 1.1 | `llms.txt` için `charset=utf-8` | Dosya Türkçe ama sunucu karakter setini bildirmiyor; bazı botlar "HavalimanÄ±" gibi bozuk okuyor | `hazir/plesk-nginx-ekle.conf` 1. bölüm |
| 1.2 | Yeni `llms.txt` | Mevcut dosyaya teknik değerler, 8 kısa SSS, rehber linkleri ve tarih eklendi. Eski içerik aynen duruyor | `hazir/llms.txt` → sunucuda `/llms.txt` ile değiştir |
| 1.3 | Gösterim almış eski adresleri doğru sayfaya yönlendir | `/case/ic-mekan-led-ekran/` (3.251 gösterim), `/case/dis-mekan-led-ekran/` (2.278) ve diğerleri şu an `/projeler/`'e gidiyor; güç yanlış sayfaya akıyor | `hazir/plesk-nginx-ekle.conf` 2. bölüm (depodaki `PLESK-RENTAL-CASE-301.md` ile aynı yöntem) |
| 1.4 | Sitemap'ten 21 adet `/case/` URL'sini çıkar | Yönlenen adresi sitemap'te tutmak tarama bütçesini harcıyor | Rank Math → Sitemap → Portfolio post tipini kapat (ya da sadece `/case/` öğelerini noindex) |
| 1.5 | Sayfa önbelleği | Her istek PHP'ye gidiyor, ilk bayt 2,2–3,2 sn. ChatGPT ve Perplexity'nin canlı okuyan botlarının zaman aşımı kısa | Kurulu önbellek eklentisinde (depodaki notlara göre W3TC) Page Cache açılır; yoksa Plesk nginx caching. Bu ortamdan eklenti ayarı görülemiyor, önce mevcut durumu kontrol edin. Sonra 5 sayfayı kontrol et: menü, form, dil değiştirici çalışıyor mu? |

## Adım 2 — Bing ve anlık indeksleme (hafta 1) · risk: yok
- **Bing Webmaster Tools:** siteyi ekle (GSC'den içe aktarma 2 dakika), sitemap gönder. ChatGPT arama ve Copilot Bing dizinini kullanıyor; Bing'de görünmeyen sayfa orada da görünmez.
- **IndexNow:** Rank Math → Modüller → **Instant Indexing** aç. Değişen sayfa Bing ve Yandex'e anında bildirilir.

## Adım 3 — SSS schema'ları (hafta 2) · risk: yok (görünüm değişmez)
- 15 sayfada SSS metni görünüyor ama FAQPage schema'sı yok. Hazır bloklar: `hazir/schema-faq/*.html`.
- Bloklar sayfadaki görünen metinden **birebir** üretildi; Google'ın yanıltıcı işaretleme riski yok.
- Ekleme: Elementor'da SSS'nin altına bir **HTML** widget koyup bloğu yapıştır. Ekranda hiçbir şey görünmez.
- Sıra: önce blog ve rehber sayfaları (11 sayfa), 1 hafta sonra fiyat sayfaları, **en son anasayfa**.
- Kontrol: https://search.google.com/test/rich-results ile her sayfa.

## Adım 4 — Site dışı güven sinyalleri (hafta 2–6) · risk: yok
Yapay zekâ motorları "hangi firma?" sorusunda büyük ölçüde başka sitelerde geçen bilgileri kullanıyor.
- **Google Business Profile:** kategoriler, hizmet listesi, ürün listesi (iç/dış mekan, kiralama, COB), her ay 5–10 gerçek proje fotoğrafı, müşterilerden yorum isteme (proje tesliminde QR/link).
- **Bing Places:** Google profilinden içe aktar.
- **Tek cümlelik tanım her yerde aynı olsun:** "LEDAJANS, 2001'den beri İstanbul merkezli LED ekran satış, kiralama, kurulum ve teknik servis firmasıdır." LinkedIn, Instagram, YouTube, Facebook, firma rehberleri ve fuar katılımcı sayfalarında.
- **Firma rehberleri:** firmasec, yenibiris ve sektör dizinlerinde aynı ad, adres ve telefon (NAP birebir aynı).
- **Fuar ve basın:** SIGN İstanbul katılımcı sayfası, sektör haber sitelerine proje haberi (şehir, m², pitch, fotoğraf). Her haber ilgili ürün sayfasına link versin.
- **YouTube:** mevcut proje videolarının açıklamasına proje bilgisi ve ilgili sayfa linki.

## Adım 5 — Sadece fiyat ve rehber sayfalarında içerik (hafta 3–8) · risk: düşük
Görünüm aynı kalır: mevcut yazı stiliyle, mevcut bloklara metin ve tablo eklenir. Anasayfaya ve `/led-ekran/`'a dokunulmaz.
- **Fiyat aralığı tablosu:** 4 fiyat sayfasına m² ve günlük fiyat aralığı ekle (rakamlar sizden). AI motorları fiyat sorusunda rakam veren kaynağı alıntılıyor; şu an hiçbir fiyat sayfasında rakam yok.
- Fiyat sayfalarına "Son güncelleme: Kasım 2026" satırı; başlıktaki "Mayıs Güncel" ifadesi kaldırılır.
- **Rakam tutarlılığı:** Kurulum sayfasında "400–800 W/m²" yazıyor, ürün tablolarında ortalama 173–213 W/m². Anasayfa SSS'sinde "garanti teklifte netleşir", diğer her yerde "2 yıl garanti" yazıyor. Tek ifadeye bağlanmalı; çelişen kaynağa AI motorları güvenmez.
- Her adım tek sayfa, ardından 7 gün izleme.

## Adım 6 — Aylık ölçüm (her ayın ilk haftası)
1. GSC: "led ekran" kümesi sıraları + Adım 0 ile karşılaştırma.
2. `ai-gorunurluk-olcum.csv` güncelle.
3. Bing Webmaster: indekslenen sayfa sayısı.

---

## Özet takvim
| Hafta | İş | Risk |
|---|---|---|
| 1 | Ölçüm, nginx (charset + yönlendirme), yeni llms.txt, sitemap, önbellek, Bing + IndexNow | yok |
| 2 | SSS schema: 11 blog/rehber sayfası | yok |
| 3 | SSS schema: fiyat sayfaları; GBP ve rehber kayıtları | yok |
| 4 | Anasayfa SSS schema (görünmez); fiyat tablosu 1. sayfa | yok / düşük |
| 5–8 | Diğer fiyat sayfaları, rakam tutarlılığı, basın ve fuar linkleri | düşük |
