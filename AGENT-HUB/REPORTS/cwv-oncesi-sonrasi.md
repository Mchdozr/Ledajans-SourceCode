# Mobil CWV — Öncesi / Sonrası Raporu

**Site:** https://ledajans.com/ (anasayfa)  
**Ölçüm:** Lighthouse lab (Cloud VM, mobil form-factor)  
**Deploy tarihi:** 2026-07-13  
**Rapor tarihi:** 2026-07-13

---

## 1. Patch öncesi vs patch sonrası (aynı ortam)

Bu tablo **aynı Cloud ölçüm ortamında** alındı; en güvenilir kıyas budur.

| Metrik | Öncesi (pre) | Sonrası (iter1 medyan) | Değişim | Hedef |
|--------|--------------|------------------------|---------|-------|
| **Performance** | 62 | **70** | +8 puan (+13%) | ≥80 |
| **LCP** | 7.3 s | **5.7 s** | −1.6 s (−22%) | <2.5 s |
| **TBT** | 52 ms | **16 ms** | −36 ms (−69%) | <200 ms |
| **CLS** | 0.000 | **0.000** | — | <0.1 |
| **FCP** | 4.8 s | **3.7 s** | −1.1 s (−23%) | <1.8 s |
| **Speed Index** | 6.1 s | **4.2 s** | −1.9 s (−31%) | <3.4 s |

**Kaynak dosyalar:**
- Öncesi: `data/baselines/audit-mobile-test0.json` (tek koşu, 2026-07-13 pre-deploy)
- Sonrası: `data/baselines/cwv-summary-2026-07-13-iter1.json` (3 koşu medyan)

### iter1 koşu detayı (mobil)

| Koşu | Perf | LCP | TBT |
|------|------|-----|-----|
| 1 | 70 | 5.7 s | 19 ms |
| 2 | 70 | 5.7 s | 16 ms |
| 3 | 64 | 7.2 s | 16 ms |
| **Medyan** | **70** | **5.7 s** | **16 ms** |

---

## 2. Nisan baseline vs sonrası (tarihsel kıyas)

Nisan ölçümü farklı ortamda alındı; mutlak puanlar birebir karşılaştırılamaz, trend için referans.

| Metrik | Nisan 2026 (öncesi) | Sonrası (iter1) | Değişim |
|--------|---------------------|-----------------|---------|
| **Performance** | 42 | **70** | +28 puan (+67%) |
| **LCP** | 10.9 s | **5.7 s** | −5.2 s (−48%) |
| **TBT** | 710 ms | **16 ms** | −694 ms (−98%) |
| **CLS** | 0.001 | **0.000** | iyileşti |
| **FCP** | 5.5 s | **3.7 s** | −1.8 s (−33%) |
| **Speed Index** | 6.3 s | **4.2 s** | −2.1 s (−33%) |

**Kaynak:** `data/baselines/audit-mobile-full.json` (Nisan) → iter1 medyan

---

## 3. Desktop gate (patch sonrası, referans)

Patch'ler `wp_is_mobile()` ile sınırlandı; desktop kasıtlı değiştirilmedi.

| Metrik | Nisan desktop | iter1 lab | Not |
|--------|---------------|-----------|-----|
| Performance | 92 | 72 | Farklı ölçüm ortamı (Cloud → TR sunucu) |
| LCP | 1.3 s | 2.7 s | Lab gecikmesi |
| TBT | 10 ms | ~0 ms | — |
| CLS | 0.007 | 0.005 | — |

---

## 4. Uygulanan değişiklikler (özet)

| # | Değişiklik | Dosya |
|---|------------|-------|
| 1 | W3TC lazyload LCP istisnası (`skip-lazy`, eager, q60 src) | `mobil-hiz-patch.php`, `Hero.html` |
| 2 | Çift preload temizliği | `Hero.html`, mu-plugin |
| 3 | Mobilde jQuery defer (anasayfa) | `mobil-hiz-patch.php` |
| 4 | Chaty scroll/idle erteleme (tüm mobil sayfalar) | `mobil-hiz-patch.php` |
| 5 | Font mobil fallback + CSS async genişletme | `mobil-hiz-patch.php` |
| 6 | GTM gecikme 4s→6s (mobil) | `mobil-hiz-patch.php` |

---

## 5. Hedef durumu

| Metrik | Sonrası | Hedef | Durum |
|--------|---------|-------|-------|
| Performance | 70 | ≥80 | ❌ Kısmen |
| LCP | 5.7 s | <2.5 s | ❌ İyileşti, hedef değil |
| TBT | 16 ms | <200 ms | ✅ |
| CLS | 0.000 | <0.1 | ✅ |

---

## 6. Sonraki adımlar

1. iter2 buffer fix deploy (`deploy-site-files.py --apply`) + cache purge
2. `run-lighthouse-cwv.py --label iter2` ile yeniden ölçüm
3. GSC Deneyim → Core Web Vitals mobil (field data, ~28 gün) — `cwv-gsc-field-validation.md`
