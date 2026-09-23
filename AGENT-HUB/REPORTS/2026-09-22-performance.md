# Performance Report — 2026-09-22

Kapsam: Anasayfa Widget 1 stant videosu. Canlı deploy yok.

## Ölçülen dosyalar

| Dosya | Boyut | Not |
|---|---|---|
| Ham `StantVideo.mp4` | **7303 KiB** / 11.87 Mbps | 1920×1080, H.264+AAC, 5.04s — **kullanılmadı** |
| `hero-stant-1280.mp4` | **304 KiB** / 0.49 Mbps | 1280×720, H.264, **ses yok** (`-an`), crf28, faststart |
| `hero-stant-poster.webp` | **47 KiB** | 1280×720, desktop LCP |
| `hero-stant-poster-mobile.webp` | **43 KiB** | 768×1024 crop, mobil LCP |
| Mevcut atrium mobil (repo) | 797 KiB | karşılaştırma |

Slow 4G (~1.6 Mbps) indirme tahmini: ham ~36s; 1280 encode ~1.5s; mobil poster ~0.22s; atrium mobil ~4.0s.

## LCP riski

- **Ham 7.5 MB `data-src` olursa** mobil LCP/TBT çöker (decode + 7 MiB). Yasak.
- **Video preload** LCP’yi 304 KiB + video decode kadar geciktirir. Hero’da `as="video"` yok; `preload="none"`.
- **Doğru yol:** LCP = poster WebP. Desktop idle’da 304 KiB video LCP’den sonra gelir.
- Mobil poster **43 KiB** vs atrium **797 KiB** → ~**754 KiB** LCP adayı tasarrufu (repo). Canlı v2 boyutu WP’de ayrı; yine poster ≪ video.

## Mobil video kapalı kalsın mı?

**Evet — kapalı kalsın.** ≤768’de mevcut `display: none` duruyor; JS `innerWidth > 768` olmadan `source` eklemiyor. 304 KiB + decode, baseline LCP 6.5–10.9s / TBT bandını bozar. Mobil LCP stant still.

## Preload değişikliği

| Yer | Önce | Sonra |
|---|---|---|
| `Hero.html` | atrium-v2 image preload (mobil+desktop) | stant poster WebP + `media` (768 / 769). **Video preload yok** |
| `wordpress-mobil-hiz-patch.php` | `hero-atrium-led-mobile.webp` (media yok) | `hero-stant-poster-mobile.webp`; mobil buffer `as="video"` / `*.mp4` preload keser. v1.2.5 |

Desktop poster preload yalnızca Hero `min-width: 769px`. Patch hâlâ mobil-only (`wp_is_mobile`).

## Uygulanan (repo)

- `#ledajansHeroVideo`: `muted playsinline loop`, `preload=none`, idle `requestIdleCallback`, `saveData` skip, `prefers-reduced-motion` video yok
- Overlay/blur visual-ux spec (beyaz stant kontrast)
- `scripts/verify-mobile-perf-live.py` stant imzası
- Asset: `Anasayfa/hero-stant-1280.mp4` + iki WebP

## Doğrulama

- `php -l wordpress-mobil-hiz-patch.php` → **No syntax errors**
- Yerel Hero imza: ham mp4 yok, Firefly yok, video preload yok, `preload=none`, mobil CSS video off, reduced-motion var → **ALL_OK**
- Canlı `verify-mobile-perf-live.py`: widget + medya yüklenmeden **VERIFY_FAIL beklenir**

## Handoff

1. WP Media: `hero-stant-1280.mp4`, `hero-stant-poster.webp`, `hero-stant-poster-mobile.webp` → `/uploads/2026/09/` (URL 404 olursa LCP düşer)
2. Hero widget + mu-plugin **aynı anda**; onay + dry-run (`risk-guardian`)
3. Sonra: `python scripts/verify-mobile-perf-live.py` + mobil Lighthouse (hedef LCP poster, video request yok)
