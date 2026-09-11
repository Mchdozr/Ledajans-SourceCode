# Visual-UX — Anasayfa iç mekan görseli (2026-09-11)

**Kapsam:** Yalnızca `Anasayfa/widget-4-Ic-Mekan.html` + sayfa 1248 indoor HTML widget. Header / hero / certs / fuar sırasına dokunulmadı.

## Viewport Issues
- Kırık `Basliksiz-1-6.png` kaldırıldı.
- Siyah stüdyo zemini chroma-key + trim ile şeffaf WebP; site `#f9fafb` zemini görünüyor.
- Wrapper’da kutu/çerçeve yok (`background` şeffaf, `border:0`, `box-shadow:none`).
- Desktop `position:absolute; height:100%; max-height:none` kaldırıldı — panel metin sütununu ezmiyor.

## Copy Fixes
- Metin değişmedi. `alt` aynı: İç Mekan LED Ekran - Indoor LED Ekran Çözümleri

## Visual/A11y Fixes
- Media id 5060 → `https://ledajans.com/wp-content/uploads/2026/09/ic-mekan-led-ekran-panel-transparent.webp` (RGBA, 766×962, köşe alpha=0)
- `object-fit: contain`; salınım: `translateY(±10px) rotate(±1deg)`, 4s, ease-in-out, infinite alternate
- `prefers-reduced-motion: reduce` → `animation: none`

## CSS Diff Özeti
```css
.ledajans-indoor-image-container { width: 70%; max-width: 380px; }
.ledajans-indoor-image { max-height: 420px; object-fit: contain; }
@media (min-width: 768px) {
  .ledajans-indoor-image-container { max-width: 440px; }
  .ledajans-indoor-image { max-height: 480px; }
}
@keyframes ledajans-indoor-float {
  from { transform: translateY(10px) rotate(-1deg); }
  to { transform: translateY(-10px) rotate(1deg); }
}
```

## QA Checklist
- [x] Canlı `src` = `ic-mekan-led-ekran-panel-transparent.webp` (RGBA, köşe alpha 0)
- [x] Indoor widget CSS’te `#000` / `#000000` yok
- [x] Wrapper `background: transparent` + `box-shadow: none` + `border: 0`
- [x] `@keyframes ledajans-indoor-float` duruyor
- [x] Opaque `ic-mekan-led-ekran-panel.webp` canlı HTML’de yok
- [x] Canlı `max-height: 420/480/500px`, `max-width: 480px`, `width: 70%`; `max-height: none` yok
- [x] Canlı keyframes: `translateY(±10px) rotate(±1deg)`, `4s ease-in-out infinite alternate`
- [x] Full homepage restore yok; ürün indoor hero’suna dokunulmadı
