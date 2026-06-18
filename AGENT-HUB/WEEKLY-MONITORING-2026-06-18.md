# Haftalık SEO İzleme — 2026-06-18

## SERP — led ekran

| Cihaz | Sıra | Hedef URL | Rakip | Rakip sıra | Kaynak |
|---|---:|---|---|---:|---|
| mobile | 1 | https://ledajans.com/ | ledsanat.com | 2 | ddg_html_google_proxy |
| desktop | 2 | https://ledajans.com/ | ledeksan.com | 1 | ddg_html_google_proxy |

### Notlar
- Organik sıra: 1; önceki kayıt: 1 (2026-06-03 manual); DDG HTML tr-TR organik proxy (Google doğrudan scrape engelli); sonuç_sayısı=10
- Organik sıra: 2; önceki kayıt: top5 (2026-06-03 audit); DDG HTML tr-TR organik proxy (Google doğrudan scrape engelli); sonuç_sayısı=10

### Karşılaştırma
- Önceki organik mobil kayıt (2026-06-03): sıra **1**, kaynak `manual_web_check`
- Önceki organik desktop kayıt (2026-06-03): sıra **top5**, kaynak `audit_2026-06-03`
- Son GSC ortalama pozisyon (2026-06-05T14:21:00Z): **6.78** (Clicks=223)

## Komut
```bash
python3 AGENT-HUB/check-serp-weekly.py
```

## Sonraki kontrol
- Cron: `0 6 * * *` (günlük ölçüm, haftalık özet dosyası)
- GSC export geldiğinde: `python3 scripts/update-serp-baseline-from-gsc.py`
