# SERP — "led ekran" / ledajans.com (2026-05-08)

## Özet

| Alan | Değer |
|------|--------|
| Anahtar kelime | `led ekran` |
| Hedef alan adı | `ledajans.com` |
| Ölçüm kaynağı | **DuckDuckGo Lite** (programatik POST; **Google SERP değildir**) |
| Yakalanan URL | `https://ledajans.com/` |
| **Sıra (DDG Lite)** | **1** |
| Zaman (UTC) | 2026-05-08T06:05:25Z |

## Google hakkında not

Canlı **Google** sırası kişiselleştirme, konum, cihaz ve bot koruması nedeniyle bu depoda doğrudan çekilmez. Ticari raporlama için **Google Search Console** (sorgu başına ortalama konum ve tıklanan URL) veya ücretli bir SERP API önerilir.

## Haftalık tekrar

1. Repo kökünden: `bash AGENT-HUB/run-weekly-serp-led-ekran.sh` veya `python3 AGENT-HUB/tools/weekly_serp_led_ekran.py`
2. Geçmiş satırları: `AGENT-HUB/SERP-LED-EKRAN-history.jsonl` (her başarılı koşuda bir JSON satırı eklenir)
3. Örnek cron (her Pazartesi 07:00 UTC): `0 7 * * 1 cd /workspace && python3 AGENT-HUB/tools/weekly_serp_led_ekran.py`

Manuel Google sırası otomasyona aktarılacaksa: `MANUAL_SERP_POSITION=5 MANUAL_SERP_URL='https://ledajans.com/led-ekran/' python3 AGENT-HUB/tools/weekly_serp_led_ekran.py --no-history` (örnek; `--no-history` olmadan da yazılır).

## DDG Lite — ilk 10 (aynı anlık ölçüm)

1. https://ledajans.com/
2. https://www.ledeksan.com/
3. https://www.ledurunleri.com/led-ekran-panelleri
4. https://www.ledgrafik.com/
5. https://www.ledsanat.com/led-ekran/
6. https://www.amazon.com.tr/led-ekran/s?k=led+ekran
7. https://www.modulerled.com.tr/
8. https://www.ledvizyon.com.tr/
9. https://www.ledtabela.com/tr/led-ekran
10. http://www.ledekranproje.com/
