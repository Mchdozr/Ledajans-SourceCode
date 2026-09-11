# Visual-UX — Anasayfa dış mekan görseli (2026-09-11)

**Kapsam:** Yalnızca `Anasayfa/widget-5-Dis-Mekan.html` + sayfa 1248 outdoor HTML widget. Indoor / hero / certs / slider’a dokunulmadı. Outdoor animasyon yok; indoor float duruyor.

## Viewport Issues
- Kırık `Basliksiz-5.png` (boş mavi) outdoor `img.ledajans-outdoor-image` içinden kaldırıldı.
- Indoor ile aynı kutu: container `width: 70%` / `72%`, `max-width: 380 / 440 / 480px`; img `max-height: 420 / 480 / 500px`; `object-fit: contain`.
- Kart çerçevesi (`border-radius` + `box-shadow` + `overflow: hidden`) kaldırıldı — indoor wrapper ile aynı.
- Desktop `height: 560px` + `max-height: none` yok.

## Copy Fixes
- Metin değişmedi. `alt` aynı: Dış Mekan LED Ekran - Outdoor LED Ekran Çözümleri

## Visual/A11y Fixes
- Media id 5061 → `https://ledajans.com/wp-content/uploads/2026/09/dis-mekan-led-cephe.webp` (RGB, 1024×892, ~191KB, kırpma yok)
- `width="1024"` `height="892"` + `loading="lazy"`
- Outdoor `@keyframes` / `animation` yok

## CSS Diff Özeti
```css
.ledajans-outdoor-image-container { width: 70%; max-width: 380px; }
.ledajans-outdoor-image { max-height: 420px; object-fit: contain; }
@media (min-width: 768px) {
  .ledajans-outdoor-image-container { max-width: 440px; }
  .ledajans-outdoor-image { max-height: 480px; }
}
@media (min-width: 1024px) {
  .ledajans-outdoor-image-container { width: 72%; max-width: 480px; }
  .ledajans-outdoor-image { max-height: 500px; object-fit: contain; }
}
```

## QA Checklist
- [x] WP media 201 → id 5061, `image/webp`, RIFF, 191130 byte
- [x] `python scripts/deploy-homepage-outdoor.py --dry-run` → DRY_RUN
- [x] `python scripts/deploy-homepage-outdoor.py` → widgets_updated=1, page_update=200, cache 200
- [x] Canlı outdoor `src` = `dis-mekan-led-cephe.webp`
- [x] Canlı `section.ledajans-outdoor` içinde `Basliksiz-5` yok
- [x] Canlı outdoor CSS indoor ile eşleşiyor: 420/480/500, 70%/72%, max-width 380/440/480, contain
- [x] Canlı outdoor `@keyframes`/`animation` yok; indoor float duruyor
- [x] Indoor `ic-mekan-led-ekran-panel-transparent.webp`, hero, certs duruyor
- [x] Full homepage restore yok
