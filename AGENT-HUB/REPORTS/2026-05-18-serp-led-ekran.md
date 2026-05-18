# led ekran — sıra raporu (2026-05-18)

## Özet

| Alan | Değer |
|------|--------|
| Anahtar kelime | `led ekran` |
| Ölçüm (UTC) | 2026-05-18 (bulut otomasyon çalıştırması) |
| **Proxy sıra (DuckDuckGo Lite, `kl=tr-tr`)** | **1** — hedef: `https://ledajans.com/` |
| Google organik sıra | Bu ortamda Google HTML SERP çekimi JS/consent nedeniyle güvenilir parse edilemiyor; kesin sıra için **Google Search Console** → Performans → sorgu `led ekran` → **Ortalama konum** kullanılmalıdır. |

## Haftalık raporlama

1. Her çalıştırmada: `python3 AGENT-HUB/scripts/serp_snapshot_led_ekran.py`  
   - Sonuç satırı `AGENT-HUB/SERP_HISTORY/led-ekran-tr.jsonl` dosyasına eklenir.  
   - Aynı betik `AGENT-HUB/REPORTS/serp-led-ekran-haftalik-ozet.md` dosyasını son ~8 gün kayıtlarıyla günceller.

2. Yalnızca özet (JSONL’den): `python3 AGENT-HUB/scripts/serp_snapshot_led_ekran.py --weekly-summary`

## Yöntem notu

DuckDuckGo Lite sonuçları Google ile aynı sırayı garanti etmez; fakat **aynı betik + aynı parametreler** ile haftadan haftaya **göreli trend** izlenebilir. Ticari karar için GSC veya ücretli rank tracker ile çapraz kontrol önerilir.
