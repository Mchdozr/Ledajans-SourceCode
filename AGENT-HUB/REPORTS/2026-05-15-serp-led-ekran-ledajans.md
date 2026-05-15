# SERP özeti — led ekran / ledajans.com (2026-05-15 UTC)

## Google `tr` organik “tekil sıra” (1–10)

**Bu çalıştırmada ölçülemedi (N/A).** Bulut çıkış IP’si ile yapılan doğrudan Google/Bing/Yandex HTML istekleri bot doğrulamasına veya JS-only SERP’e takıldı; **gerçek kullanıcı SERP sırası kişiselleşir** ve tek bir “kaçıncı sıra” doğrusu yoktur.

## Güvenilir ölçüm (önerilen)

1. **Google Search Console** → Performans → Sayfa veya Sorgu filtresi `led ekran` → **Ortalama konum** (tıklama ağırlıklı ortalama; “10.” sıra”dan farklı olabilir).
2. Ücretli/oturumlu **SERP API** veya rank tracker (aynı gün, `tr-TR`, mobil+masaüstü ayrı rapor).

## Haftalık raporlama (depo içi)

- Günlük cron bu betiği çağırabilir; betik **aynı ISO haftada yalnızca bir satır** ekler: `AGENT-HUB/REPORTS/serp-led-ekran-weekly-log.md`
- GSC değerini yazmak için `serp-led-ekran-manual.example.json` dosyasını `serp-led-ekran-manual.json` olarak kopyalayıp `google_avg_position` alanını doldurun **veya** çalıştırmadan önce ortam değişkeni `LEDAJANS_LED_EKRAN_GOOGLE_RANK` verin.

## Betik

`python3 AGENT-HUB/scripts/weekly_serp_led_ekran.py`
