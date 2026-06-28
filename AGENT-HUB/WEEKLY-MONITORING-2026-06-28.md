# Haftalık SEO İzleme — 2026-06-28

## SERP — led ekran

- Ölçüm UTC: `2026-06-28T06:05:12Z`
- Mobil: sıra **2** | URL `https://ledajans.com/` | kaynak `ddg_html_proxy`
- Masaüstü: sıra **1** | URL `https://ledajans.com/` | kaynak `ddg_html_proxy`
- Mobil haftalık delta: ↑ 5 sıra iyileşme
- Masaüstü haftalık delta: ↑ 4 sıra iyileşme
- Satır eklendi: `AGENT-HUB/SERP-BASELINE.csv`

### Notlar
- Mobil: DuckDuckGo HTML proxy (Google ile birebir değil); device=mobile; bulut IP Google SERP captcha veriyor — SERPER_API_KEY önerilir
- Masaüstü: DuckDuckGo HTML proxy (Google ile birebir değil); device=desktop; bulut IP Google SERP captcha veriyor — SERPER_API_KEY önerilir
- Kesin Google SERP için ortam değişkeni: `SERPER_API_KEY` veya `SERPAPI_KEY`

## Para sayfa (audit-money-pages.py)
- Son audit: **6/6** canonical OK

## GSC export
- Son klasör: `AGENT-HUB/DATA/gsc-performance-2026-06-05/`
- GSC tazelik: eski — yeni export gerekli
- Yeni export geldiğinde `scripts/update-serp-baseline-from-gsc.py` ile toplu güncelle

## Komutlar
```bash
cd /workspace
python3 AGENT-HUB/keyword_rank_weekly.py
python3 AGENT-HUB/audit-money-pages.py
python3 deploy-to-wordpress.py --dry-run
```

## Sonraki hafta
- `python3 AGENT-HUB/keyword_rank_weekly.py` (cron: `0 6 * * *` günlük 06:00 UTC)
