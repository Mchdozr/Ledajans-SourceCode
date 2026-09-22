# Risk-Guardian — Anasayfa Widget 1 stant videosu

Tarih: 2026-09-22  
Kapsam: `Anasayfa/Hero.html` + `scripts/deploy-homepage-hero.py` + `wordpress-mobil-hiz-patch.php`  
Canlı widget yazımı: **BLOK** (medya 301 + onay cümlesi yok)

## Karar

| İş | Risk | Block/Allow | Gerekçe | Güvenli alternatif |
|---|---|---|---|---|
| Repo `Hero.html` (1280/crf28, poster WebP, mobil video `display:none`, `preload=none`, `data-src`) | P2 | **ALLOW** | H1/CTA duruyor; `StantVideo.mp4` / `as="video"` / robots / noindex / canonical yok. Dosya 311 557 B (~304 KiB). | — |
| `python scripts/deploy-homepage-hero.py --dry-run` | P2 | **ALLOW** | 2026-09-22 çalıştırıldı: `DRY_RUN: yazilmadi` (exit 0). Script canlı POST atmaz. Dry-run medya HEAD ve widget_id canlı doğrulaması yapmıyor. | Dry-run’a 3 asset HEAD (200 + `video/mp4` / `image/webp`) + `StantVideo` yok kapısı ekle. |
| Ham `StantVideo.mp4` WP Media | P0 | **BLOCK** | ~7.5 MB / ~11.9 Mbps; mobil LCP/TBT kırar. | Yalnız `hero-stant-1280.mp4` + 2 WebP. |
| Canlı Widget 1 yazımı (şimdi) | P0 | **BLOCK** | 3 yeni URL `301 → https://ledajans.com` (HTML). Preload/poster kırık LCP. Kullanıcı cümlesi `"widget1 arka planına ekle"` bu turda yok. | 1) Media 200  2) dry-run  3) açık cümle  4) yalnızca `--dry-run` olmadan script. |
| Plugin canlı (mu-plugin) widget’tan ayrı | P1 | **BLOCK** (tek başına) | Canlı mobil hâlâ `ldajsn2-mobile-q60.webp` preload. Widget-only stant poster + eski q60 = çift LCP adayı. Repo 1.2.5 atrium’u stant poster’a çeviriyor; canlıya yazılmamış. | Widget + plugin **aynı pencerede**, medya 200 olduktan sonra. Video preload yok. |
| robots / canonical / noindex | — | **ALLOW** (dokunma) | Canlı: `index, follow…`, canonical `https://ledajans.com/`, noindex yok. Diff’te yok. | Değiştirme. |
| Secret / `.env` commit | P0 | **BLOCK** | `.gitignore` satır 1: `.env`. Deploy şifre basmıyor. | Commit listesine `.env` / app password koyma; sohbette yazdırma. |
| Diğer widget / sayfa meta | P1 | **ALLOW** koşullu | Fallback `walk_replace(..., widget_id=122e243)` + `ledajans-hero`. `--dry-run`sız script canlı POST atar. | Flagsız çalıştırma; `widgets_updated!=1` ise abort. |

## Kanıt (canlı, 2026-09-22)

- Asset HEAD: `hero-stant-1280.mp4`, `hero-stant-poster.webp`, `hero-stant-poster-mobile.webp` → **301** `/`
- Mobil preload: `ldajsn2-mobile-q60.webp` (plugin) + atrium-v2 (mevcut widget)
- Canlı hero `data-src` hâlâ Firefly; ham `StantVideo.mp4` yok
- Repo video: 311 557 B, poster WebP 48 318 / 44 126 B

## Kapı (canlı widget)

1. WP Media: üç dosya, ham 7.5 MB yok; HEAD 200
2. `python scripts/deploy-homepage-hero.py --dry-run`
3. Kullanıcı: **widget1 arka planına ekle**
4. Plugin 1.2.5 aynı pencerede (q60/atrium kes, stant poster; `as=video` yok)
5. Sonra `python scripts/verify-mobile-perf-live.py`
