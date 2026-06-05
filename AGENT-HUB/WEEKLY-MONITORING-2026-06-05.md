# Haftalık SEO İzleme — 2026-06-05

## Smoke test
- Komut: `powershell -File scripts/run-weekly-seo-check.ps1`
- Sonuç: **PASS** (robots, sitemap, para sayfalar 200, deploy dry-run 36/36)

## Para sayfa (audit-money-pages.py)
- Kaynak: `audit-money-pages-2026-06-05.json`
- **6/6** canonical OK (`/`, `/led-ekran/`, ic/dis/rental, `/cob-ekran/`)

## P0 on-page + RankMath
- `verify-rankmath-p0-meta.py`: 4/4 title eşleşti
- `verify-money-pages-live.py`: hub dahil içerik sinyalleri OK (hub H1: LED Ekran Çözümleri ve Fiyatları)
- Canlı iç link taraması (8 para sayfa): **44 link, 0×404**

## Bu hafta tamamlanan (P0 paket)
- Widget/SSS güncellemeleri
- 12 SEO rehber sayfası WP deploy
- `/rehber/` alt URL düzleştirme
- GSC drilldown triage (aksiyon: toplu index yok)

## Açık (düşük öncelik / manuel)
- GSC Performance → `SERP-BASELINE.csv`
- Ana sayfa mobil LCP
- WP app password rotate

## Sonraki hafta
```powershell
powershell -File scripts/run-weekly-seo-check.ps1
```
