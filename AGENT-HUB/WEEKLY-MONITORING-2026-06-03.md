# Haftalık SEO İzleme — 2026-06-03

## Smoke test
- Komut: `powershell -File scripts/seo-smoke-test.ps1`
- Sonuç: **PASS** (robots, sitemap, para sayfalar HTTP 200, redirect www/http)

## Para sayfa crawl (audit-money-pages.py)
| URL | Canonical | Sitemap | Robots |
|-----|-----------|---------|--------|
| / | OK | evet | index |
| /led-ekran/ | OK | evet | index |
| /ic-mekan-led-ekran/ | OK | evet | index |
| /dis-mekan-led-ekran/ | OK | evet | index |
| /rental-ekran/ | OK | evet | index |
| /cob-ekran/ | OK | evet | index |

## Mobil Lighthouse (kayıtlı)
| Sayfa | Perf | LCP | TBT |
|-------|------|-----|-----|
| /projeler/ (GTM+asset) | 72 | 5,14 sn | 85 ms |
| Ana sayfa (cache) | 60 | 9,63 sn | 267 ms |

Kaynak: `AGENT-HUB/lh-mobile-projeler-revert-2.json`, `lh-mobile-home-after-cache.json`

## GSC (manuel)
- Panelden URL Inspection ile **Indexed** onayı: `GSC-EXPORT-CHECKLIST.md`
- Performance export → `SERP-BASELINE.csv` güncelle

## Açık aksiyonlar
- Ana sayfa LCP ayrı backlog
- Ana sayfa / rental / COB meta description 160+ karakter (kısaltma önerisi: `RANKMATH-AUDIT.md`)

## Sonraki hafta
```powershell
powershell -File scripts/run-weekly-seo-check.ps1
```
