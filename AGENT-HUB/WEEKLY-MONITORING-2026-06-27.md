# Haftalık SEO İzleme — 2026-06-27

## SERP — led ekran

- Ölçüm UTC: `2026-06-27T06:02:07Z`
- Mobil: sıra **2** | URL `https://ledajans.com/` | kaynak `ddg_html_proxy`
- Masaüstü: sıra **2** | URL `https://ledajans.com/` | kaynak `ddg_html_proxy`
- Satır eklendi: `AGENT-HUB/SERP-BASELINE.csv`

### Haftalık delta
- Mobil: 6.78 (GSC 2026-06-05) → **2** (DDG proxy) — farklı kaynak; GSC ortalama pozisyon, DDG canlı proxy
- Masaüstü: top5 (audit 2026-06-03) → **2** (DDG proxy) — önceki desktop ölçümü farklı kaynak

### Notlar
- Mobil: DuckDuckGo HTML proxy (Google ile birebir değil); device=mobile; bulut IP Google SERP captcha veriyor — SERPER_API_KEY önerilir
- Masaüstü: DuckDuckGo HTML proxy (Google ile birebir değil); device=desktop; bulut IP Google SERP captcha veriyor — SERPER_API_KEY önerilir
- Kesin Google SERP için ortam değişkeni: `SERPER_API_KEY` veya `SERPAPI_KEY`

## Para sayfa (audit-money-pages.py)
- Son audit: **6/6** canonical OK

## GSC export
- Son klasör: `AGENT-HUB/DATA/gsc-performance-2026-06-05/` (22 gün önce)
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
