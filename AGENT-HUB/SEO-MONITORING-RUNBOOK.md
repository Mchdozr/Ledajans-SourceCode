# SEO İzleme Runbook (7 / 28 gün)

## Günlük (5 dk)

```powershell
powershell -File scripts/seo-smoke-test.ps1
```

## Haftalık (Gün 7)

| Metrik | Kaynak | Hedef |
|--------|--------|-------|
| `led ekran` avg position | GSC | Stabil veya ↑ |
| CTR ana sayfa + /led-ekran/ | GSC | ↑ veya stabil |
| Indexed para URL (6) | GSC Pages | 6/6 |
| Mobil LCP | Lighthouse / CrUX | <4s ara hedef |
| SERP satırları | `SERP-BASELINE.csv` | Güncel |

Haftalık SERP snapshot:

```bash
python3 scripts/capture-serp-baseline.py
```

## Aylık (Gün 28)

- Lighthouse mobile/desktop karşılaştırması (`audit-mobile-full.json` ile diff)
- Rakip seti güncelleme (ticari rakipler only)
- İç link matrisi: `SEO-Icerik-Widgets/ic-link-haritasi.html` durum sütunu

## Guardrail (değişiklik sonrası)

- SEO Lighthouse = 100
- CLS ≤ 0.1
- Canonical self-match
- robots.txt sitemap satırı = `sitemap_index.xml`

## Komutlar

```powershell
powershell -File scripts/seo-smoke-test.ps1
powershell -File scripts/run-weekly-seo-check.ps1
python AGENT-HUB/audit-money-pages.py
python deploy-to-wordpress.py --dry-run
```

Haftalık kayıt şablonu: `AGENT-HUB/WEEKLY-MONITORING-YYYY-MM-DD.md`
