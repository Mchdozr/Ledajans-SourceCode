# LED Ekran anahtar kelimesi — sıra özeti (2026-05-12)

## Google (led ekran, Türkiye)

Bu bulut ortamında Google SERP HTML’i yalnızca JavaScript ile dolduğu için **güvenilir Google sırası otomatik çekilemedi**. Resmi metrik için Search Console → Performans → sorgu: `led ekran` (average position ve tıklama verisi) kullanılmalıdır.

## Yahoo TR proxy (otomatik ölçüm)

- **Motor:** Yahoo arama, Türkçe arayüz parametresi `fr=yfp-t-tr`.
- **Metot:** Organik sonuçlarda `RU=/RK=` yönlendirme URL’leri; yahoo.com alanları elenir; **aynı kök domain yalnızca bir kez** sayılır (sitelink tekrarları birleştirilir).
- **Sonuç (2026-05-12 UTC):** `led ekran` sorgusunda ledajans.com, domain tekilleştirmeli listede **1.** sırada; üst URL: `https://ledajans.com/`.
- Bu değer **Google sırasının yerine geçmez**; haftalık trend için aynı betik ve CSV kullanılır.

## Haftalık raporlama

Aynı ölçümü tekrarlamak için (ör. mevcut günlük cron ile):

`python3 /workspace/AGENT-HUB/scripts/serp_led_ekran_yahoo_rank.py`

Her çalıştırma `AGENT-HUB/REPORTS/serp-led-ekran-yahoo-timeseries.csv` dosyasına bir satır ekler; haftalık karşılaştırma için CSV’deki son 7 satıra bakın. Google tarafı için Search Console dışa aktarımı veya harici rank tracker eklenmelidir.
