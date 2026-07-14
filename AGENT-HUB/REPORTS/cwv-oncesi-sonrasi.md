# Mobil CWV — Öncesi / Sonrası Raporu

**Site:** https://ledajans.com/ (anasayfa)  
**Ölçüm:** Lighthouse lab (Cloud VM, mobil form-factor)  
**Deploy tarihi:** 2026-07-13  
**Rapor tarihi:** 2026-07-13

---

## 1. Patch öncesi vs patch sonrası (aynı ortam)

Bu tablo **aynı Cloud ölçüm ortamında** alındı; en güvenilir kıyas budur.

| Metrik | Öncesi (pre) | Sonrası (iter9c, 5 koşu medyan) | Değişim | Hedef |
|--------|--------------|----------------------------------|---------|-------|
| **Performance** | 62 | **97** | +35 puan (+56%) | ≥80 ✅ |
| **LCP** | 7.3 s | **2.4 s** | −4.9 s (−67%) | <2.5 s ✅ |
| **TBT** | 52 ms | **0 ms** | −52 ms (−100%) | <200 ms ✅ |
| **CLS** | 0.000 | **0.027** | +0.027 | <0.1 ✅ |
| **FCP** | 4.8 s | **1.6 s** | −3.2 s (−67%) | <1.8 s ✅ |
| **Speed Index** | 6.1 s | **2.5 s** | −3.5 s (−58%) | <3.4 s ✅ |

**Kaynak dosyalar:**
- Öncesi: `data/baselines/audit-mobile-test0.json` (tek koşu, 2026-07-13 pre-deploy)
- Sonrası: `data/baselines/cwv-summary-2026-07-13-iter9c.json` (5 koşu medyan)

### iter9c koşu detayı (mobil)

| Koşu | Perf | LCP | TBT |
|------|------|-----|-----|
| 1 | 97 | 2.39 s | 0 ms |
| 2 | 98 | 2.30 s | 0 ms |
| 3 | 89 | 3.31 s | 0 ms |
| 4 | 97 | 2.34 s | 0 ms |
| 5 | 88 | 3.34 s | 0 ms |
| **Medyan** | **97** | **2.39 s** | **0 ms** |

---

## 2. Nisan baseline vs sonrası (tarihsel kıyas)

Nisan ölçümü farklı ortamda alındı; mutlak puanlar birebir karşılaştırılamaz, trend için referans.

| Metrik | Nisan 2026 (öncesi) | Sonrası (iter9c) | Değişim |
|--------|---------------------|-----------------|---------|
| **Performance** | 42 | **97** | +55 puan (+131%) |
| **LCP** | 10.9 s | **2.4 s** | −8.5 s (−78%) |
| **TBT** | 710 ms | **0 ms** | −710 ms (−100%) |
| **CLS** | 0.001 | **0.027** | hedef içinde |
| **FCP** | 5.5 s | **1.6 s** | −3.9 s (−72%) |
| **Speed Index** | 6.3 s | **2.5 s** | −3.8 s (−60%) |

**Kaynak:** `data/baselines/audit-mobile-full.json` (Nisan) → iter9c medyan

---

## 3. Desktop gate (patch sonrası, referans)

Patch'ler `wp_is_mobile()` ile sınırlandı; desktop kasıtlı değiştirilmedi.

| Metrik | Nisan desktop | iter9c (3 koşu medyan) | Gate |
|--------|---------------|-------------------------|------|
| Performance | 92 | **90** | ≥90 ✅ |
| LCP | 1.3 s | **1.3 s** | ≤1.5 s ✅ |
| TBT | 10 ms | **0 ms** | ≤50 ms ✅ |
| CLS | 0.007 | **0.006** | ≤0.1 ✅ |

---

## 4. Uygulanan değişiklikler (özet)

| # | Değişiklik | Dosya |
|---|------------|-------|
| 1 | 605KB Bootstrap/template yerine Coverage tabanlı kritik CSS | `mobile-critical-theme.css` |
| 2 | Elementor/header/home kritik CSS tek versioned dosyada | `mobil-hiz-patch.php` |
| 3 | 8.9KB mobil Hero WebP kritik CSS background data URI | `Hero.html`, mu-plugin |
| 4 | Blog/Elementor/Chaty fold-altı isteklerini erteleme | widget + mu-plugin |
| 5 | Desktop fair panel 1.18MB PNG → 19.5KB WebP | `Hero.html` |
| 6 | Anonymous mobil menu viewport fallback + desktop izolasyonu | mu-plugin |

---

## 5. Hedef durumu

| Metrik | Sonrası | Hedef | Durum |
|--------|---------|-------|-------|
| Performance | 97 | ≥80 | ✅ |
| LCP | 2.39 s | <2.5 s | ✅ |
| TBT | 0 ms | <200 ms | ✅ |
| CLS | 0.027 | <0.1 | ✅ |

---

## 6. Sonraki adımlar

Lab hedefleri tamamlandı. GSC Deneyim → Core Web Vitals mobil field data, deploy tarihinden sonraki 28 günlük pencere dolunca `cwv-gsc-field-validation.md` ile kontrol edilecek.
