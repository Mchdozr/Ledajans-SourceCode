# Haftalık SEO İzleme — 2026-06-29

## SERP — led ekran

- Ölçüm UTC: `2026-06-29T06:04:57Z`
- Script: `python3 AGENT-HUB/keyword_rank_weekly.py`
- `SERP-BASELINE.csv` yeni satır: **2**

| Cihaz | Sıra | Hedef URL | Kaynak | Not |
|---|---:|---|---|---|
| mobile | **2** | https://ledajans.com/ | duckduckgo_html_tr | DDG HTML kl=tr-tr; Google organic proxy değil; top_competitor=https://www.ledeksan.com/ |
| desktop | **2** | https://ledajans.com/ | duckduckgo_html_tr | DDG HTML kl=tr-tr; Google organic proxy değil; top_competitor=https://www.ledeksan.com/ |

## Trend (önceki sayısal ölçüme göre)

- **mobile**: 2 — ↑ 4.78 sıra (iyileşme)
  - Önceki: 6.78
- **desktop**: 2 — önceki ölçüm yok

- Son önceki kayıt: `2026-06-05T14:21:00Z` (gsc_performance_2026-06-05) → sıra **6.78**
  - Not: GSC `avg_position` ile DDG organic sırası doğrudan karşılaştırılmamalı.

## Cron

```bash
bash AGENT-HUB/run-keyword-rank-weekly.sh
```

## Sonraki hafta

- `SERPER_API_KEY` veya `SERPAPI_KEY` tanımlanırsa Google organic ölçümü otomatik önceliklenir.
- GSC Performance export ≤7 gün taze ise ortalama pozisyon yedek kaynak olarak kullanılır.
