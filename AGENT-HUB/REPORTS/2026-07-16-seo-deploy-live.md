# SEO Deploy Canlı — 2026-07-16

## Uygulanan komutlar
1. `deploy-elementor-widgets.py --apply` → 8/8 OK
2. `deploy-money-pages.py --apply` → hub güncellendi
3. `set-rankmath-p0-meta.py --apply` → 5/5 (anasayfa + P0 para sayfalar)
4. Blog `led-ekran-fiyatlari-2026` REST güncelleme (id=7250, publish korundu)

## Canlı doğrulama
- `verify-money-pages-live.py` → 4/4 geçti
- `verify-rankmath-p0-meta.py` → anasayfa title: `LED Ekran - RGB Panel - LED Görüntü Sistemleri`
- Anasayfa: `LED ekran üreticisi` + `LED ekran firmaları` metni canlıda
- Hub: `la-trust-bar`, H1 `LED Ekran Çözümleri ve Fiyatları`
- Blog: hub linki `LED ekran ve fiyatları` canlıda
- İç/dış mekan: JSON-LD blokları canlıda (4–5 adet)

## Sonraki adım (manuel)
- WP Admin → LiteSpeed Cache → Purge All (isteğe bağlı, CDN gecikmesi varsa)
- GSC → 48–72 saat sonra query-page: `led ekran` URL dağılımı
- Rich Results Test: iç/dış mekan Product schema
