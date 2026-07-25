# Haftalık SEO İzleme — 2026-07-25

## SERP — led ekran

| Cihaz | Sıra | Hedef URL | Kaynak | Önceki | Delta |
|---|---:|---|---|---|---|
| mobile | 1 | https://ledajans.com/ | ddg_lite_jina_proxy | top3 | — |
| desktop | 2 | https://ledajans.com/ | yahoo_jina_proxy | top5 | — |

### Rakip özeti (mobile)

- #1 ledajans.com — LED Ekran - RGB Panel - LED Görüntü Sistemleri **(biz)**
- #2 ledeksan.com — Ledeksan - Led Teknolojileri
- #3 ledsanat.com — LED Ekran - Hızlı Teklif AL - LEDSANAT | LED Teknolojileri
- #4 ledekransistemleri.com.tr — LED Ekran Sistemleri 2025 | Fiyatları, Çeşitleri ve Kurulum 
- #5 ledshop.com.tr — LedShop.com.tr | Türkiyenin En İyi Led Ekran ve Led Tabela S

### Notlar
- Ölçüm zamanı (UTC): `2026-07-25T06:10:04Z`
- `SERP-BASELINE.csv` eklenen satır: **2**
- Mobile: Google CAPTCHA nedeniyle doğrudan ölçülemedi; DDG lite (jina proxy) ile tahmini organic sıra; device=mobile
- Desktop: Yahoo (jina proxy) organic sıra; device=desktop; Images bloğu hariç
- GSC avg_position (son kayıt 2026-06-05): **6.78** — farklı metrik; canlı organic ile karıştırma.

## Otomasyon

```bash
bash AGENT-HUB/run-keyword-rank-weekly.sh
```

Cron: `0 6 * * *` UTC (haftalık SERP snapshot).
Google doğrudan erişim için ortam değişkeni: `SERPER_API_KEY` veya `SERPAPI_KEY`.
