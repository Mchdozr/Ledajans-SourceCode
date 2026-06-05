# GSC Indexlenmeyen URL Triage — 2026-06-05

Kaynak: GSC > Sayfa indeksleme > `Tarandı - şu anda dizine eklenmiş değil` CSV export  
Dosya: `C:\Users\kacma\Downloads\ledajans.com_FailingUrls_4_8_2026.csv`

## GSC neden özeti

| Neden | Adet | Karar |
|---|---:|---|
| Tarandı - şu anda dizine eklenmiş değil | 390 | Kalite/iç link/meta iyileştirmesi; sadece yararlı sayfalar güçlendirilmeli |
| Yönlendirmeli sayfa | 16 | Normal; kaynak URL değil hedef URL indexlenmeli |
| Bulunamadı (404) | 13 | Backlink/trafik varsa 301; yoksa zararlı değil |
| Yeniden yönlendirme hatası | 9 | Teknik hata; düzeltilecek |
| Kullanıcı tarafından seçilen standart sayfa olmadan kopya | 7 | Canonical kontrolü |
| Doğru standart etikete sahip alternatif sayfa | 7 | Normal |
| `noindex` etiketi tarafından hariç tutuldu | 6 | Bilinçliyse normal |
| Sunucu hatası (5xx) | 2 | Teknik hata; düzeltilecek |
| Robots.txt tarafından engellendi | 2 | Önemli URL ise robots kontrolü |
| Başka bir 4xx sorunu nedeniyle engellendi | 1 | Teknik hata |

## Faydalı ve işlem yapılan URL'ler

| URL | Karar | Yapılan |
|---|---|---|
| `/program-indir/` | Yararlı; GSC performans verisi de var | RankMath title/meta/focus güncellendi |
| `/dis-mekan-rgb-panel/` | Yararlı ürün sayfası | RankMath title/meta/focus güncellendi |

Canlı doğrulama: `scripts/verify-index-candidates-meta.py` → geçti.

## Düşük öncelik / index zorlanmamalı

- `/firma-bilgilerimiz/`
- `/en/our-company-information/`
- `/en/contact/`
- `/de/unsere-firmeninformationen/`
- `/de/kommunikation/`

Bu sayfalar kurumsal/dil varyasyonu. Ticari SEO katkısı P0/P1 sayfalara göre düşük.

## Teknik kontrol gerekenler

404 örnekleri:
- `/case/`
- `/en/case/`
- `/de/case/`
- `/en/case/indoor-rgb-panels/`
- `/de/case/rgb-panel-fuer-den-aussenbereich/`
- `/en/case/power-supply/`

Karar: backlink/trafik varsa ilgili Türkçe/İngilizce hedefe 301; yoksa 404 kalması sorun değil.

## Normal görünenler

Şu URL'ler büyük ihtimalle canonical/redirect nedeniyle kaynak URL olarak indexlenmiyor; hedef URL'ler kontrol edilmeli:

- `/p10-grafik-ekran-kullanimi/`
- `/nova-mrv-330-receiver/`
- `/hd-c30-kontrol-karti/`
- `/tf-qc1-kontrol-karti/`
- `/dip-led-panel-tamiri/`
- `/hd-c10-kontrol-karti/`
- `/p25-indoor-rgb-panel/`
- `/serit-led/`
- `/led-ekran-omru/`

Mevcut nginx/htaccess blog 301 dosyalarında bazıları `/blog/.../` hedefine taşınmış görünüyor. Canlı yönlendirme uygulanmışsa kaynak URL'leri indexletmeye çalışmamak doğru.
