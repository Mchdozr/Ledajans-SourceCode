# Visual-UX — Fuar kartı arka plan + hero sağ hiza (2026-09-11)

**Kapsam:** Yalnızca `Anasayfa/Hero.html` + WP media `fuar-kart-arkaplan.webp` + `scripts/deploy-homepage-hero.py` (sayfa 1248). Header snippet dokunulmadı.

## Viewport Issues
- Masaüstü: fuar solda; metin + CTA + play sağda (`left: calc(min(450px, 38vw) + clamp + 2rem)`). `left:0` yok.
- Kart `::before`: cover + center; koyu overlay + yeni WebP.
- Mobil ≤768: fuar gizli; `::before` `background-image: none`; content normal akış.

## Copy Fixes
- Metin değişmedi.

## Visual/A11y Fixes
- Eski 1.2MB PNG (`Firefly_Gemini-Flash-8.png`) kaldırıldı.
- Yeni WebP (~54KB) + `linear-gradient(180deg, rgba(15,23,42,0.52), rgba(15,23,42,0.68))` — beyaz metin okunur, pinwheel görünür.

## CSS Diff Özeti
```css
@media (min-width: 769px) {
  .ledajans-hero-fair-card::before {
    background-image:
      linear-gradient(180deg, rgba(15, 23, 42, 0.52), rgba(15, 23, 42, 0.68)),
      url('https://ledajans.com/wp-content/uploads/2026/09/fuar-kart-arkaplan.webp');
    background-size: cover;
    background-position: center;
  }
}
```

## QA Checklist
- [x] WP media id 5057 → `https://ledajans.com/wp-content/uploads/2026/09/fuar-kart-arkaplan.webp`
- [x] Repo `Anasayfa/Hero.html` güncellendi
- [x] `python scripts/deploy-homepage-hero.py` → `widgets_updated=2`, `page_update=200`, cache 200
- [x] Canlı HTML: `fuar-kart-arkaplan.webp` var; `Firefly_Gemini-Flash-8.png` yok
- [x] Canlı HTML: content `left: calc(min(450px, 38vw)+…)` — `left:0` yok
- [x] Header dokunulmadı; secret commit yok
