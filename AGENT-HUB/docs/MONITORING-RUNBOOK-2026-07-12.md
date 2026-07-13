# İzleme Runbook — "led ekran" #1 Kurtarma (2026-07-12)

Bu turda uygulanan değişikliklerin etkisini haftalık ölçmek için standart süreç.

## Uygulanan değişiklikler (özet)
1. **Mobil CWV** (`wordpress-mobil-hiz-patch.php`): anasayfada GTM 4s ertelemesi + non-critical CSS async + chaty dequeue. Beklenen: LCP 10.9s ↓, TBT 710ms ↓ (bkz. `/opt/cursor/artifacts/cwv-mobil-analiz.md`).
2. **Hub `/led-ekran/`**: güven bandı, teknik karşılaştırma tablosu, FAQ 3→5, `WebPage` + `dateModified` schema.
3. **RankMath meta**: anasayfa marka+kapsam odağı (cannibalization ↓), hub head-term sahibi.
4. **İç link**: anasayfa→hub ("led ekran çözümleri"), dış-mekan blog→hub; dış-mekan yeni SEO metin bloğu (hub geri-besleme).
5. **İndeksleme**: robots.txt crawl-budget kuralları + aksiyon planı.
6. **Off-page/E-E-A-T**: backlink + rakip link gap + NAP standardı stratejisi.

## Deploy sırası (canlı)
```
# 0) Yedek al (WP + DB)
# 1) Performans patch: wp-content/mu-plugins/ledajans-perf-patch.php güncelle
# 2) RankMath meta:
python3 scripts/set-rankmath-p0-meta.py --apply
python3 scripts/verify-rankmath-p0-meta.py
# 3) İçerik: LED Ekran/led-ekran.html, widget-3.html, dis-mekan-led-ekran-text.html
#    Elementor'a yapıştır / deploy-to-wordpress.py --publish (uygun sayfalar)
python3 deploy-to-wordpress.py --dry-run   # önce doğrula
# 4) robots.txt köke yükle
# 5) Cache temizle (WP + CDN)
```

## Haftalık ölçüm (her Pazartesi)
1. **CWV (mobil)**:
   `npx lighthouse https://ledajans.com/ --only-categories=performance --form-factor=mobile --output=json --output-path=audit-mobile-after.json`
   → Perf skoru, LCP, TBT'yi `audit-mobile-full.json` (before) ile karşılaştır. Hedef: Perf ≥ 80, LCP < 2.5s, TBT < 200ms.
2. **Sıralama/CTR**: GSC → Performance → Query `led ekran` (28 gün). Yeni satırı `SERP-BASELINE.csv`'e ekle (`captured_at_utc, query, ..., rank_position, source=gsc_weekly`).
3. **İndeksleme**: GSC → Sayfa indeksleme trendi; "Tarandı - dizine eklenmedi" adedi düşüyor mu?
4. **Smoke**: `pwsh scripts/seo-smoke-test.ps1` (robots + sitemap + money pages 200).
5. **Backlink**: referring domains (Ahrefs/SEMrush) — yeni/kayıp.

## Hedef eşikleri
| Metrik | Baseline (2026-06-05) | 30 gün hedef | 90 gün hedef |
|---|---|---|---|
| `led ekran` avg pos | 6.78 | ≤ 4 | ≤ 2 (→ #1) |
| `led ekran` CTR | %2.9 | ≥ %4 | ≥ %6 |
| Mobil Perf | 42 | ≥ 70 | ≥ 85 |
| Mobil LCP | 10.9s | < 4s | < 2.5s |

## Geri alma (rollback)
- Cannibalization yanlış yönde giderse (anasayfa `led ekran` konumu düşerse) `HOMEPAGE` meta focus'una `led ekran` geri eklenir veya hub ile rol takas edilir.
- Performans patch sorun çıkarırsa mu-plugin devre dışı → önceki sürüme dön.
