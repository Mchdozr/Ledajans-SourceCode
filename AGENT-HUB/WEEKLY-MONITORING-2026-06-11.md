# Haftalık SEO İzleme — 2026-06-11

## SERP — `led ekran` (Google, tr-TR, mobile)

| Alan | Değer |
|------|-------|
| Ölçüm UTC | 2026-06-11T06:00:21Z |
| Sıra | **1** |
| Hedef URL | https://ledajans.com/ |
| Kaynak | google_serp_browser |
| Not | Organik #1 Google TR; rakipler ledfon.com #2, ledurunleri.com #3; /led-ekran/ ilk sayfada görünmedi |

### Son ölçümler (led ekran)

| Tarih | Kaynak | Sıra | URL |
|-------|--------|-----:|-----|
| 2026-06-11 | google_serp_browser | 1 | https://ledajans.com/ |
| 2026-06-05 | gsc_performance_2026-06-05 | 6.78 | https://ledajans.com/ |
| 2026-06-03 | manual_web_check | 1 | https://ledajans.com/ |
| 2026-06-03 | manual_web_check | top3 | https://ledajans.com/led-ekran/ |
| 2026-06-03 | audit_2026-06-03 | top5 | https://ledajans.com/ |

## Smoke / teknik (önceki hafta ile aynı komutlar)

```bash
cd /workspace
python3 deploy-to-wordpress.py --dry-run
python3 AGENT-HUB/audit-money-pages.py
```

## Sonraki ölçüm

Cron: günlük 06:00 UTC — `python3 AGENT-HUB/record-serp-check.py ...`

Haftalık kayıt: bu dosya (`WEEKLY-MONITORING-2026-06-11.md`) + `SERP-BASELINE.csv`.
