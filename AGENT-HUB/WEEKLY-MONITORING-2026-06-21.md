# Haftalık SEO İzleme — 2026-06-21

## `led ekran` sıra özeti
- Sorgu: **led ekran**
- Hedef URL: `https://ledajans.com/`
- Ölçüm zamanı (UTC): `2026-06-21T06:09:01Z`
- Konum (`rank_position`): **6.78**
- Kaynak: `gsc_performance_2026-06-05`
- Trend: = stabil (önceki 6.78)
- Not: Clicks=223; Impressions=7691; CTR=2.9%; avg_position=6.78; live_serp_not_found
- `SERP-BASELINE.csv` satırı: bugün için zaten vardı

## Teknik smoke
- `python3 deploy-to-wordpress.py --dry-run` → 36/36 OK
- `python3 AGENT-HUB/audit-money-pages.py` → Kaynak: `audit-money-pages-2026-06-21.json` — canonical OK

## GSC veri tazeliği
- Son GSC export: `2026-06-05`
- Canlı Google SERP bulut IP'den engellendi; konum GSC ortalama pozisyonu ile raporlanır.
- Güncel sıra için GSC Performance export'u `AGENT-HUB/DATA/` altına koyup `python3 scripts/parse-gsc-export.py` çalıştırın.

## Sonraki hafta
```bash
python3 scripts/report-serp-led-ekran.py
```
