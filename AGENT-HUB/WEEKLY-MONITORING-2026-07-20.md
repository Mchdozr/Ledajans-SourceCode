# Haftalık SEO İzleme — 2026-07-20

## SERP: "led ekran" (ledajans.com)

| Alan | Değer |
|------|-------|
| Ölçüm UTC | 2026-07-20T06:01:12Z |
| Locale | tr-TR |
| Arama motoru | Google (proxy/API) |
| Hedef URL | https://ledajans.com/ |
| Desktop sıra | **2** (önceki: top5) |
| Mobile sıra | **2** (önceki: 6.78 GSC avg) |
| Veri kaynağı | ddg_lite_proxy |
| Birincil rakip | ledeksan.com |
| CSV eklenen satır | 2 |

### Top 5 organic (snapshot)

| # | URL |
|---|-----|
| 1 | https://www.ledeksan.com/ |
| 2 | https://ledajans.com/ |
| 3 | https://www.ledsanat.com/led-ekran/ |
| 4 | https://www.planar.com/products/led-video-walls/ |
| 5 | https://www.amazon.com.tr/led-ekran/s?k=led+ekran |

### Notlar
- Desktop: DDG lite proxy organic=10; attempt=1; matched_url=https://ledajans.com/
- Mobile: DDG lite proxy organic=10; attempt=1; matched_url=https://ledajans.com/; mobile=ddg_desktop_snapshot
- GSC `avg_position` ile canlı organic sıra farklı metriklerdir; ikisi birlikte izlenmeli.
- Son GSC avg_position (2026-06-05): **6.78** (`gsc_performance_2026-06-05`)

## Komutlar

```bash
cd /workspace
python3 AGENT-HUB/keyword_rank_weekly.py
```

Cron (automation): `0 6 * * *` UTC → `AGENT-HUB/run-keyword-rank-weekly.sh`

## Sonraki hafta
- `SERP-BASELINE.csv` trendini kontrol et
- GSC Performance export ile avg_position doğrula
- `python3 AGENT-HUB/audit-money-pages.py`
