# GSC CWV Field Data — Doğrulama Runbook

**Tarih:** 2026-07-13  
**Lab sonuç (iter1 medyan):** Mobil Perf 70, LCP 5.7s, TBT 16ms, CLS 0.000

## Neden GSC?

Lighthouse lab ölçümleri Cloud VM'den Türkiye sunucusuna gider; Nisan baseline (Perf 42, LCP 10.9s) ile aynı ortam değil. **Field data (CrUX/GSC)** gerçek kullanıcı deneyimini yansıtır; deploy sonrası **28 gün** gecikmeli güncellenir.

## Kontrol adımları

1. [Google Search Console](https://search.google.com/search-console) → **Deneyim** → **Core Web Vitals**
2. **Mobil** URL grubunu aç → `https://ledajans.com/` dahil mi kontrol et
3. Metrikler:
   - LCP: hedef **≤2.5s** (iyi)
   - INP/FID: etkileşim
   - CLS: **≤0.1**
4. **Önemli URL'ler** sekmesinde anasayfa + para sayfaları (`/led-ekran/`, `/ic-mekan-led-ekran/`, `/dis-mekan-led-ekran/`)
5. Deploy tarihi: **2026-07-13** — karşılaştırma için önceki 28 günlük dönemle kıyasla

## Beklenen etki (deploy edilen patch'ler)

| Patch | Beklenen field etkisi |
|-------|----------------------|
| W3TC lazyload LCP istisnası + skip-lazy | LCP ↓ (Nisan'da img.lazy sorunu vardı) |
| Çift preload temizliği | Erken keşif |
| Chaty/jQuery mobil erteleme | TBT ↓ |
| Mobil font fallback + CSS async | FCP/LCP ↓ |

## PageSpeed Insights (field)

```
https://pagespeed.web.dev/analysis?url=https://ledajans.com/&form_factor=mobile
```

CrUX verisi varsa "Discover what your real users are experiencing" bölümünü kaydet.

## Sonraki iterasyon

Lab hedefi (Perf≥80, LCP<2.5s) tutmazsa `scripts/monitor/run-lighthouse-cwv.py --label iterN` ile tekrar ölç; GSC field 28 gün sonra nihai doğrulama.
