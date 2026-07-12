# Manuel yapıştırma rehberi (2026-07-12)

**Not:** Bu adımlar artık REST ile otomatik yapılıyor (`scripts/deploy-elementor-widgets.py`, `scripts/deploy-site-files.py`). Referans için bırakıldı.

## `/dis-mekan-led-ekran/` — SEO metin nerede?

Sayfa yapısı (yukarıdan aşağı):

1. **Hero banner** — H1 "Dış Mekan LED Ekran" (widget `3f7d957`)
2. Ürün slider / Tayor / OFC serisi blokları
3. **SEO metin bloğu** — `control-cards-title` başlıklı bölüm (**FAQ'nın hemen üstünde**)
4. **SSS / FAQ** — "Dış Mekan LED Ekran Hakkında Sık Sorulan Sorular"

Elementor: Sayfalar → Dış Mekan LED Ekran → Elementor ile düzenle → FAQ section'ın **hemen üstündeki** HTML widget.

Kaynak dosya: `Urunlerimiz/Dis-Mekan-Led-Ekran/dis-mekan-led-ekran-text.html`

## `robots.txt` nereye?

Plesk yolu: `httpdocs/robots.txt` (site kökü, `wp-config.php` ile aynı seviye)

Canlı URL: https://ledajans.com/robots.txt

## Diğer dosyalar

| Dosya | Elementor / Plesk |
|-------|-------------------|
| `LED Ekran/led-ekran.html` | `/led-ekran/` ana HTML widget |
| `Anasayfa/widget-3.html` | Anasayfa Hakkımızda HTML widget |
| `wordpress-mobil-hiz-patch.php` | `wp-content/mu-plugins/ledajans-perf-patch.php` |

## Otomatik deploy

```bash
python3 scripts/deploy-elementor-widgets.py --apply
python3 scripts/deploy-site-files.py --apply
```
