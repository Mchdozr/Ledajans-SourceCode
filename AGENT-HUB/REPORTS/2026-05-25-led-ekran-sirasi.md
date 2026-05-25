# led ekran — ledajans.com sıra raporu (2026-05-25)

## Özet

| Alan | Değer |
|------|--------|
| Sorgu | `led ekran` |
| Hedef | `ledajans.com` (organik, Google Türkiye niyeti: `hl=tr`, `gl=tr`) |
| Ölçüm kaynağı (bu çalıştırma) | **SerpAPI yok** — bulut IP üzerinden doğrudan Google HTML çekimi **403 / robot doğrulaması** ile sonuçsuz kaldı; DuckDuckGo HTML de **anomaly** sayfasına düşüyor. |

## Bugünkü “kaçıncı sıra” cevabı

**Bu ortamda sayısal organik sıra üretilemedi** (canlı SERP erişimi engelli). Güvenilir tek seferlik ölçüm için aşağıdakilerden biri kullanılmalıdır:

1. **SerpAPI anahtarı** ile repodaki betik: `python3 AGENT-HUB/serp_led_ekran_weekly.py`  
   Ortam: `export SERPAPI_API_KEY="..."`  
   Çıktı: `AGENT-HUB/REPORTS/serp-led-ekran-weekly.jsonl` (tarihçe) + `serp-led-ekran-weekly-latest.md` (son özet).

2. **Google Search Console** → Performans → sorgu `led ekran` → *Ortalama konum* (tıklama ağırlıklıdır; klasik “10. sıradaki URL” ile aynı değildir, yine de trend takibi için uygundur).

3. **Manuel kontrol:** Türkiye çıkışlı, gizli pencere, kişiselleştirme kapalı; sayfa başına ~10 sonuç sayarak doğrulama.

## Haftalık raporlama

- Otomatik kayıt: `AGENT-HUB/REPORTS/serp-led-ekran-weekly.jsonl` (her başarılı/ başarısız koşu bir satır).
- Önerilen zamanlama: **haftada bir** (ör. Pazartesi 09:00 `Europe/Istanbul`) — Cursor Automation günlük tetikliyorsa, yalnızca Pazartesi koşacak şekilde cron ifadesini `0 9 * * 1` yapın veya betiği haftalık harici cron’a bağlayın.

## Sonraki adım

`SERPAPI_API_KEY` (veya eşdeğer SERP sağlayıcı) CI / sunucu sırlarına eklendikten sonra bu branch’teki betik tekrar çalıştırıldığında **sayısal sıra** otomatik yazılır.
