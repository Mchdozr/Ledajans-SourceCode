# Visual-UX — Anasayfa hero fuar kartı (2026-09-21)

**Kapsam:** `Anasayfa/Hero.html` — SIGNISTANBUL logosu, H1 sığdırma, tek CTA.

## Viewport
- 1440: SIGN kırmızı logo görünür; H1 kartın sağında, overlap yok (gap ~150px)
- 1280 / 1100: overlap yok, H1 clip yok
- Play butonu duruyor

## Copy
- Tek CTA: **Hemen Arayın** → `tel:+902122204004`
- LED Ekran Modelleri / Fiyat Teklifi Alın kaldırıldı

## Visual
- Kırık `signistanbul-3.png` (HTML 404) → `signistanbul-logo-1.webp` (kullanıcının SIGN logosu)
- Fair-reveal: `justify-content:flex-end` + daraltılmış title `clamp`

## QA
- [x] Logo naturalWidth 360, canlı src webp
- [x] Tek primary buton
- [x] Play wrap görünür
- [x] Elementor cache DELETE sonrası origin HTML yeni
