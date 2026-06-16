# Haftalık SEO İzleme — 2026-06-16

## SERP — led ekran (Google tr-TR)

- Ölçüm UTC: `2026-06-16T06:05:00Z`
- Hedef URL: `https://ledajans.com/`
- Kaynak: `live_google_serp_check`

### Sıra
- **mobile**: 1 (önceki: 6.78 @ 2026-06-05T14:21:00Z, kaynak: gsc_performance_2026-06-05)
- **desktop**: 1 (önceki: top5 @ 2026-06-03T11:20:00Z, kaynak: audit_2026-06-03)

### Notlar
Organik #1 (mobil+masaüstü aynı). Üst reklam yok; Görseller bandı ~7. sırada; ilgili aramalar alt bölüm. Önceki GSC avg_position=6.78 (2026-06-05) ile fark: canlı SERP daha iyi.

## Komut (sonraki hafta)

```bash
python3 scripts/check-serp-led-ekran.py \
  --mobile-rank <sıra> --desktop-rank <sıra> \
  --target-url https://ledajans.com/ \
  --source live_google_serp_check \
  --notes "Görseller + ilgili aramalar; ücretli reklam yok"
```

## Referans

- Detay satırlar: `AGENT-HUB/SERP-BASELINE.csv`
- Runbook: `AGENT-HUB/SEO-MONITORING-RUNBOOK.md`
