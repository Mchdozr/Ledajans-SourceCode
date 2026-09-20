# Haftalık SEO İzleme — 2026-07-18

## SERP — `led ekran` (tr-TR, Google)

| Cihaz | Sıra | Hedef URL | Kaynak | Değişim |
|-------|-----:|-----------|--------|---------|
| desktop | 2 | https://ledajans.com/ | ddg_lite_proxy | önceki: top5 |
| mobile | 2 | https://ledajans.com/ | ddg_lite_proxy | önceki: 1 |

- Ölçüm zamanı (UTC): `2026-07-18T06:03:37Z`
- Birincil rakip: `ledeksan.com` (sıra 1)
- GSC referans (2026-06-05): avg position **6.78** (organic sıra ile aynı metrik değil)
- CSV güncellendi: `AGENT-HUB/SERP-BASELINE.csv` (+2 satır)

## Notlar
- Canlı organic sıra DuckDuckGo lite proxy ile ölçüldü; Google SERP yaklaşık göstergesidir.
- `SERPER_API_KEY` tanımlanırsa doğrudan Google SERP kullanılır.
- Mobile ölçümde DDG rate-limit nedeniyle desktop snapshot devralındı.

## Sonraki çalıştırma
```bash
python3 AGENT-HUB/keyword_rank_weekly.py
```

Cron/automation: `0 6 * * *` UTC (`AGENT-HUB/run-keyword-rank-weekly.sh`).
