# Visual-UX — Sertifika kart görselleri (2026-09-11)

**Kapsam:** `Anasayfa/sertifikalar-anasayfa.html` + `Kurumsal/Sertifikalarimiz/sertifikalarimiz.html`. Canlı yazım onaylı restore.

## Viewport Issues
- Anasayfa kartı 148×104 / 200×132; PDF ilk sayfa A4 dikey (≈1469×2021). `object-fit: contain` + `display: block`.
- Marquee `transform` + `loading="lazy"` kartları boş bırakabiliyordu → anasayfada `eager`.

## Copy Fixes
- Alt metinler ISO adını koruyor (9001, 45001, 14064, 10002, 14001, 27001, 31000).
- `href` = PDF; `img` = WebP thumb.

## Visual/A11y Fixes
- 7 PDF doğrulandı (`TAHA LED  14064.pdf` çift boşluk).
- Thumb: PyMuPDF ilk sayfa WebP.
- WP `upload_max_filesize` ~2MB: 6 ISO PDF sıkıştırıldı; 14064 orijinal (607 KB).
- Yeni medya: `*-1.webp` / `*-1.pdf` (2026/09).
- Kart `img`: `display:block; height:100%; max-width:100%`.

## CSS Diff Özeti
```css
.ledajans-home-cert-card img {
  display: block;
  width: auto;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
```

## QA Checklist
- [x] Canlı anasayfa 7 img + 7 PDF HTTP 200 (`image/webp` / `application/pdf`)
- [x] Canlı `/sertifikalarimiz/` 7 img + 7 PDF HTTP 200
- [x] `ledajans-home-certs` index 153139 < `ledajans-about` 181570
- [x] `la-fuar-popup` yok
- [x] Secret commit yok
