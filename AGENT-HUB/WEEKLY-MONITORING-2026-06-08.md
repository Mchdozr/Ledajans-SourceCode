# Haftalık SEO İzleme — 2026-06-08

## SERP — `led ekran` (ledajans.com)

- Ölçüm UTC: `2026-06-08T06:24:14Z`

| Cihaz | Arama motoru | Sıra | Kaynak | Not |
|---|---|---:|---|---|
| desktop | google | **1** | google_desktop_browser | Tarayıcı ile doğrulandı (hl=tr, gl=tr); organik #1 |
| mobile | google | **2** | google_mobile_browser | Mobil viewport 390px; rakip #1: ledurunleri.com; yerel paket görünür |

## Trend

- GSC ort. pozisyon (2026-06-05): **6.78** → canlı Google desktop **#1**, mobile **#2**
- Mobil: 2026-06-03 manuel #1 → 2026-06-08 **#2** (ledurunleri.com #1)
- Desktop: organik birinci sonuç; ücretli reklam görülmedi

## Otomasyon

```bash
python3 AGENT-HUB/check-serp-rank.py --google-desktop 1 --google-mobile 2
```

Proxy kontrol (headless): Bing + DuckDuckGo otomatik eklenir.

Kayıt: `AGENT-HUB/SERP-BASELINE.csv`

## Sonraki hafta

```bash
python3 AGENT-HUB/check-serp-rank.py --google-desktop N --google-mobile N
```
