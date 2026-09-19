# Haftalık SEO İzleme — 2026-07-01

## SERP — led ekran

- Ölçüm zamanı (UTC): `2026-07-01T06:07:12Z`

| Cihaz | Motor | Sıra | Hedef URL | Kaynak | Not |
|---|---|---:|---|---|---|
| mobile | duckduckgo_proxy | 2 | https://ledajans.com/ | duckduckgo_html_proxy | organic_rank=2; Google organic proxy; SERPER_API_KEY ile kesin ölçüm önerilir |
| desktop | duckduckgo_proxy | 2 | https://ledajans.com/ | duckduckgo_html_proxy | organic_rank=2; Google organic proxy; SERPER_API_KEY ile kesin ölçüm önerilir |

## Önceki ölçümle fark

- **mobile**: ilk duckduckgo_html_proxy ölçümü; önceki kayıt (gsc_performance_2026-06-05): 6.78 (GSC ort. pozisyon — organic ile birebir değil)
- **desktop**: ilk duckduckgo_html_proxy ölçümü; önceki kayıt (audit_2026-06-03): top5

## GSC

- Son 7 günde taze Performance export yok; panelden export sonrası `scripts/update-serp-baseline-from-gsc.py` ile güncellenebilir.

## Sonraki çalıştırma

```bash
cd /workspace && python3 AGENT-HUB/keyword_rank_weekly.py
```

Cron: `0 6 * * *` (UTC) — `AGENT-HUB/run-keyword-rank-weekly.sh`
