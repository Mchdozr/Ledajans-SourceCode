# LCP 5 Adımlı Döngü — 2026-08-03

## Program
1. TTFB / Cache-Control temizliği  
2. Preload + font rekabeti + critical CSS  
3. Küçük LCP görseli (360w q50 → data-URI)  
4. Render-blocking / async CSS + fair-panel HTML kesimi  
5. Ölç → düzelt → deploy → tekrar

## Hedef
- LCP &lt; 4s · SEO 100 · Desktop patch NO-OP

## Ölçümler (Lighthouse mobil, simulate)

| Tur | Perf | SEO | LCP | FCP | TBT | TTFB | Not |
|-----|------|-----|-----|-----|-----|------|-----|
| baseline | 80 | 100 | 4.6s | - | - | 940ms | döngü öncesi |
| r1 (defer jq + 360w) | 77 | 100 | 5.0s | 2.4s | 110ms | 1190ms | jq defer kötüleştirdi |
| r2 (warm) | 76 | 100 | 5.1s | 2.5s | 150ms | 1120ms | cache yok |
| r3 (cache header + fair kes) | 74 | 100 | 5.1s | 3.2s | 120ms | **500ms** | TTFB düştü |
| r4 (jq defer geri al) | 78 | 100 | 4.8s | 2.5s | 120ms | 780ms | RB=None |
| **r5b (data-URI LCP)** | **77** | **100** | **4.7s** | 2.5s | 170ms | **580ms** | en iyi LCP bu tur |

Desktop: `verify-mobile-perf-live.py` → **VERIFY_OK**

## Canlı kod (v1.2.8)
- `wordpress-mobil-hiz-patch.php` mu-plugin
- Hero data-URI LCP + critical CSS (system font)
- Fair panel / desktop video HTML mobilde kesildi
- Cache-Control temizleme denendi (nginx hâlâ `max-age=0` ekliyor)

## Tavan (kod dışı)
- Sunucu: **nginx + PHP 7.4 (Plesk)** — LiteSpeed HTML cache yok
- HTML ~410–430 KiB, mainthread ~3–3.8s
- LCP &lt; 4s için: **FastCGI/nginx microcache veya CDN HTML cache** (TTFB ≤200–300ms) şart

## Karar
Kod tarafı 5 adım uygulandı ve ölçüldü. LCP 4.6→4.7s bandında; **&lt;4s hosting/cache işi**.

## Geri alma (2026-08-03)
Kullanıcı isteğiyle LCP döngüsü **geri alındı**: mu-plugin **v1.2.4**, Hero q60 (data-URI yok). CTA/SEO/beyaz buton korundu. Canlı deploy + `VERIFY_OK`.
