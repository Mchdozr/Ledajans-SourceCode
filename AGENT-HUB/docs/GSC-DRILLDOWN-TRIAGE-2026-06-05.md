# GSC Drilldown Triage — 2026-06-05

Kaynak ZIP: `C:\Users\kacma\Downloads\ledajans.com-Coverage-Drilldown-2026-06-05 (1).zip`

Çıkarılan CSV: `AGENT-HUB/DATA/gsc-coverage-drilldown-2026-06-05/Tablo.csv`

Audit raporu: `AGENT-HUB/REPORTS/2026-06-05-gsc-drilldown-audit.md`

## Özet

| Grup | Adet | Karar |
|---|---:|---|
| Taranan URL | 390 | Tamamı işlendi |
| Yararlı / kontrol edilebilir 200 URL | 28 | Sadece seçili ticari URL'ler güçlendirilmeli |
| Normal yönlendirme/canonical/noindex | 39 | Toplu aksiyon yok |
| Teknik hata / 404 ağırlıklı | 321 | Desene göre küçük gruplar halinde ele alınmalı |

## Desen Sayımı

| Desen | Adet | Not |
|---|---:|---|
| `/feed/` | 49 | Düşük değer; index zorlanmaz |
| `/wp-json`, `/wp-content`, `/wp-includes`, sitemap | 16 | Normal sistem URL'leri |
| `/en/`, `/de/` | 16 | Dil/legacy düşük öncelik |
| `/case/` | 10 | İlgili para sayfaya 301 adayı |
| `/urunler/` | 5 | İlgili ürün kök URL'ye 301 adayı |
| `/gva_template/` | 6 | Tema template URL'leri; index zorlanmaz |
| `/blog/?p=` | 4 | Eski post ID; hedef biliniyorsa 301 |
| `/rehber/` | 1 | Yeni kök rehber URL'ye 301 adayı |
| `/sozluk/` | 1 | Yeni kök sözlük URL'ye 301 adayı |

## Öncelikli Aksiyon

1. `/case/` ve `/urunler/` eski ticari URL'leri hedef kök sayfalara 301 ile bağla.
2. `/rehber/toplanti-odasi-led-ekran/` → `/toplanti-odasi-led-ekran/`
3. `/sozluk/gob-led-nedir/` → `/gob-led-nedir/`
4. Feed, WP asset/API, tema template ve dil feed URL'lerinde index isteme.

## Durum

Bu rapor yalnızca triage içindir. Toplu index isteği veya toplu noindex uygulanmadı.
