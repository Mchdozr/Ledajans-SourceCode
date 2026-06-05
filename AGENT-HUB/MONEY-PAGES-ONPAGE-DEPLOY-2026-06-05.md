# P0 Para Sayfa On-Page — 2026-06-05

## Staging güncellendi

| Canlı URL | Repo dosyaları (Elementor widget sırası) |
|-----------|------------------------------------------|
| `/led-ekran/` | `LED Ekran/led-ekran.html` → REST ile deploy |
| `/dis-mekan-led-ekran/` | `hero-banner.html` → `sol-menu` → `urun-ozellikleri` → `sss` |
| `/ic-mekan-led-ekran/` | `hero-banner.html` → `sol-menu` → `ic-mekan-led-ekran-text.html` → `urun-ozellikleri` → `sss` |
| `/rental-ekran/` | `hero-banner.html` → `sol-menu` → `urun-ozellikleri` → `sss` |

## Hub otomatik deploy

```powershell
python scripts/deploy-money-pages.py --apply
```

## Ürün sayfaları (Elementor HTML widget)

Her dosyayı ilgili widget’a yapıştır → Güncelle → önbellek temizle.

1. **Dış mekan** — `Urunlerimiz/Dis-Mekan-Led-Ekran/`
2. **İç mekan** — `Urunlerimiz/Ic-Mekan-Led-Ekran/`
3. **Rental** — `Urunlerimiz/Rental-Ekran/`

## Yapılan on-page

- H1 + hero alt metin P0 kelimeler
- CTA: fiyat rehberi + iletişim linkleri
- Ürün özellikleri paragrafı + iç link
- Sidebar: `/led-ekran/` hub linki, trailing slash düzeltme
- SSS altı rehber kutusu çapraz linkler
- İç mekan `urun-ozellikleri` yanlış “Rental” CTA metni düzeltildi
