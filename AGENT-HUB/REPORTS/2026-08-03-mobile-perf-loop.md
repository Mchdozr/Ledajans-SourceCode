# Mobile Perf Loop - 2026-08-03

## Hedef
- SEO: 100
- Performance: >= 70
- Desktop: patch etkisi yok
- LCP ideal: < 4s

## Olcum (Lighthouse mobil, lokal)

| Tur | Perf | SEO | LCP | FCP | TBT | Not |
|-----|------|-----|-----|-----|-----|-----|
| Onceki baseline | ~42-49 | 100 | 6.5-11s | - | yuksek | - |
| v1.1 sonrasi | 64 | 100 | 11.3s | 3.6s | 30ms | GTM delay |
| v1.2 (Firefly kes) | 76 | 100 | 5.1s | 2.5s | 20ms | 1.2MB PNG yok |
| v1.2.1 (q72 kes) | 73 | 100 | 4.8s | 3.6s | 30ms | q72=0 |
| v1.2.2 (logo/font) | 71 | 100 | 4.9s | 3.5s | 30ms | TTFB 1.56s |

## Desktop dogrulama
`verify-mobile-perf-live.py` → VERIFY_OK (desktop GTM delay / idle yok)

## Karar
- SEO hedefi: **TAMAM (100)**
- Perf hedefi: **TAMAM (>=70, 71-76)**
- LCP < 4s: **TTFB 1.2-1.6s** nedeniyle su an hosting/cache siniri; ek mobil HTML kesimi getirisi azaldi

## Sonraki (hosting — kod disi)
1. LiteSpeed / WP Rocket: ayri mobil cache + HTML cache
2. TTFB < 400ms hedefi
3. Logo PNG → kucuk WebP (~10-20KiB)
