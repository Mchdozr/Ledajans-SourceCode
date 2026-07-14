# Long-tail SEO — Yayın ve Ölçüm Checklist

Repo değişiklikleri tamamlandı. Canlıya almak için:

## WordPress (manuel)

1. **Para sayfa widget’ları** — `sss.html` güncellemeleri:
   - `Urunlerimiz/Ic-Mekan-Led-Ekran/sss.html`
   - `Urunlerimiz/Dis-Mekan-Led-Ekran/sss.html`
   - `Urunlerimiz/Rental-Ekran/sss.html`
   - `Urunlerimiz/Cob-Smart-Screen/sss.html`

2. **Hub** — `LED Ekran/led-ekran.html` (rehber kartları bölümü)

3. **Projeler** — `Anasayfa/widget-7-projeler.html`

4. **Blog** — 3 yeni yazı + güncellenmiş fiyat/seçim rehberleri:
   - `/blog/ic-mekan-led-ekran-fiyatlari-2026/`
   - `/blog/dis-mekan-led-ekran-fiyatlari-2026/`
   - `/blog/rental-led-ekran-kiralama-fiyatlari-2026/`

5. **SEO sayfaları** — deploy listesindeki 32 sayfa + güncellenen 10 öncelikli sayfa

6. **Schema** — `navigation-schema.html` (canonical URL’ler)

7. **Cache** temizle (W3TC)

## Deploy script (`.env` varsa)

```powershell
python deploy-to-wordpress.py
```

Dry-run (35 dosya):

```powershell
python deploy-to-wordpress.py --dry-run
```

## GSC

- Yeni blog URL’leri → URL Inspection → **Canlı URL’yi test et**
- Performance → Queries: `iç mekan led ekran fiyatları`, `dış mekan led ekran fiyatları`, `rental led ekran kiralama`

## Haftalık rutin

```powershell
powershell -File scripts/run-weekly-seo-check.ps1
```

GSC CTR/position: `AGENT-HUB/SERP-BASELINE.csv` güncelle.
