# Haftalık SEO İzleme — 2026-06-12

## SERP — led ekran

- Ölçüm UTC: `2026-06-12T06:09:08Z`
- Mobil: sıra **6.78** | URL `https://ledajans.com/` | kaynak `gsc_performance_2026-06-05`
- Masaüstü: sıra **6.78** | URL `https://ledajans.com/` | kaynak `gsc_performance_2026-06-05`
- Satır eklendi: `AGENT-HUB/SERP-BASELINE.csv`

### Notlar
- Mobil: GSC ortalama pozisyon (export 2026-06-05); device=mobile; Clicks=223; Impressions=7691; CTR=2.9%
- Masaüstü: GSC ortalama pozisyon (export 2026-06-05); device=desktop; Clicks=223; Impressions=7691; CTR=2.9%
- DDG proxy (referans, Google değil): sıra 1 — `https://ledajans.com/`
- Kesin Google SERP için ortam değişkeni: `SERPER_API_KEY` veya `SERPAPI_KEY`

## Para sayfa (audit-money-pages.py)
- Son audit: **6/6** canonical OK

## GSC export
- Son klasör: `AGENT-HUB/DATA/gsc-performance-2026-06-05/`
- Yeni export geldiğinde `scripts/update-serp-baseline-from-gsc.py` ile toplu güncelle

## Komutlar
```bash
cd /workspace
python3 AGENT-HUB/keyword_rank_weekly.py
python3 AGENT-HUB/audit-money-pages.py
python3 deploy-to-wordpress.py --dry-run
```

## Sonraki hafta
- `python3 AGENT-HUB/keyword_rank_weekly.py` (cron: `0 6 * * 1` Pazartesi 06:00 UTC)
