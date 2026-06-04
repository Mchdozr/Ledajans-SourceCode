# Haftalık SERP İzleme — 2026-06-04

**Ölçüm penceresi:** 2026-06-04 (UTC)  
**Veri dosyası:** `AGENT-HUB/SERP-BASELINE.csv`

## Özet — "led ekran"

| Cihaz | Google TR organik sıra | Hedef URL | Kaynak |
|-------|------------------------|-----------|--------|
| Desktop | **2** | https://ledajans.com/ | google-organic-browser |
| Mobile | **2** | https://ledajans.com/ | google-organic-browser |

**Birincil rakip (üstte):** ledfon.com (#1)  
**Hemen altında:** ledurunleri.com, Trendyol (ürün kartı)

## Yorum

- Ana ticari sorgu `led ekran` için ledajans.com **ilk sayfa, 2. organik pozisyonda** (mobil ve masaüstü tutarlı).
- İlk sıra ledfon.com tarafında; delta takibi için `SERP-BASELINE.csv` haftalık satırlarıyla kıyaslanacak.
- Bulut ortamında headless Google istekleri CAPTCHA veriyor; cron için `SERPER_API_KEY` secret önerilir (`capture_serp_baseline.py`).

## Sonraki hafta

- Aynı sorgu + cihaz için yeni satır ekle (cron veya `python3 AGENT-HUB/capture_serp_baseline.py`).
- Volatilite: en az 2 haftalık ölçüm sonrası Δ rank hesaplanır.

## Komutlar

```bash
cd /workspace
# API key varsa otomatik:
python3 AGENT-HUB/capture_serp_baseline.py

# Manuel browser doğrulaması sonrası:
python3 AGENT-HUB/capture_serp_baseline.py --manual-rank 2 --manual-url https://ledajans.com/
```
