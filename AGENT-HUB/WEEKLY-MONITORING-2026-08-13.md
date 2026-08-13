# Haftalık SEO İzleme — 2026-08-13

## SERP — `led ekran` (tr-TR, Google hedef)

| Cihaz | Sıra | Hedef URL | Kaynak | Not |
|---|---:|---|---|---|
| mobile | 1 | https://ledajans.com/ | ddg_html_proxy | headless chrome failed: Command '['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=15000', '--user-agent=Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36', '--dump-dom', 'https://www.google.com/search?q=led+ekran&hl=tr&gl=tr&num=20&pws=0']' timed out after 50 seconds; DDG HTML proxy (Google değil — CAPTCHA fallback referansı) |
| desktop | 1 | https://ledajans.com/ | ddg_html_proxy | headless chrome failed: Command '['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=15000', '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', '--dump-dom', 'https://www.google.com/search?q=led+ekran&hl=tr&gl=tr&num=20&pws=0']' timed out after 50 seconds; DDG HTML proxy (Google değil — CAPTCHA fallback referansı) |

- Ölçüm zamanı (UTC): `2026-08-13T06:03:02Z`
- `SERP-BASELINE.csv` yeni satır: **2**
- Referans (GSC): Son GSC export (2026-06-05): avg_position=6.78 — Clicks=223; Impressions=7691; CTR=2.9%; avg_position=6.78

## Yorum

- Cloud IP Google CAPTCHA nedeniyle canlı Google organic parse bloklandı; DDG HTML proxy referans sırası raporlandı. Kesin Google sırası için `SERPER_API_KEY` veya GSC Performance export önerilir.

## Tekrar çalıştırma

```bash
cd /workspace && python3 AGENT-HUB/keyword_rank_weekly.py
```

Manuel doğrulama:

```bash
python3 AGENT-HUB/keyword_rank_weekly.py --mobile-rank 3 --desktop-rank 3
```

## Sonraki hafta

- Cron (UTC): `0 6 * * *` (automation)
- Komut: `bash AGENT-HUB/run-keyword-rank-weekly.sh`
