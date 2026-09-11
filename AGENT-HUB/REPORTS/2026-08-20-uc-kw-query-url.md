# Üç KW Query-URL Kırılımı — 2026-08-20

Kaynak: GSC 2026-06-05 (tüm sorgular) + 2026-08-05 (filtre: sorgu=`led ekran`, son 12 ay). Canlı HEAD bu raporda canlı doğrulanır.

## Hedef sorgular — hangi URL sıralanıyor

| Sorgu | GSC konum | Gösterim / tık | Birincil görünen URL (kanıt) | Olması gereken |
|---|---:|---|---|---|
| iç mekan led ekran | 13.21 | 896 / 23 | `/ic-mekan-led-ekran/` (Haziran) + `/case/ic-mekan-led-ekran/` (daha yüksek gösterim) | `/ic-mekan-led-ekran/` |
| indoor led ekran | 15.75 | 184 / 8 | para + case karışık | `/ic-mekan-led-ekran/` |
| iç mekan led ekran fiyatları | 15.08 | 298 / 17 | blog + para | blog (fiyat) → para CTA |
| dış mekan led ekran | 15.34 | 860 / 13 | `/dis-mekan-led-ekran/` zayıf; `/case/dis-mekan-led-ekran/` güçlü | `/dis-mekan-led-ekran/` |
| outdoor led ekran | 17.76 | 378 / 6 | case + para | `/dis-mekan-led-ekran/` |
| dış mekan led ekran fiyatları | 20.78 | 167 / 5 | blog | blog → para |
| gob led ekran | — | satır yok | yok | `/gob-led-ekran/` |
| gob led panel | 6.0 | 3 / 0 | SKU / RGB panel | `/gob-led-ekran/` (ticari) |
| gob nedir | 2.0 | 1 / 0 | 404 sözlük | `/gob-led-nedir/` |

## 12 ay `led ekran` sayfa kırılımı (2026-08-05)

| URL | Gösterim | Konum |
|---|---:|---:|
| `/case/dis-mekan-led-ekran/` | 4658 | 11.7 |
| `/case/ic-mekan-led-ekran/` | 4270 | 11.77 |
| `/led-ekran/` | 137 | 57.07 |
| `/dis-mekan-led-ekranlar/` | 71 | 50.54 |
| `/ic-mekan-led-ekran/` | 17 | 37.71 |
| `/dis-mekan-led-ekran/` | 1 | 11 |

Sonuç: Google iç/dış ticari niyeti **case kopyalarına** bağlıyor; kanonik para sayfalar bu head terimde neredeyse yok.

## Karar

1. Case → kanonik 301 (öncelik).
2. `/dis-mekan-led-ekranlar/` → `/dis-mekan-led-ekran/`.
3. GOB para sayfa aç + sözlük 404 kapat.
4. RGB panel exact-match duvarı.
