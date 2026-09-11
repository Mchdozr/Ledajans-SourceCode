# Visual-UX — Header logo + menü ortalama (2026-09-11)

**Kapsam:** `Ust-Menu/ust-menu.html` + snippet `ledajans-header-2026` (`elementor_body_end`). Logo reupload yok. Hero/sertifika/footer dokunulmadı.

**Sorun:** Logo 168×76 wrap içinde üstte (Elementor `flex-wrap` + `align-content:flex-start`). Menü başlıkları 854×76 alanda sola yaslı.

## Viewport Issues
- 1440px ölçü: wrap 144×76, img 144×32, **logoDx=0 / logoDy=0** (tam orta).
- Menü 879×76; padL=padR=188.6 — başlık grubu ortada; telefonlar sağda.

## Copy Fixes
- Metin değişmedi.

## Visual/A11y Fixes
- `aa903d8 > .elementor-widget-wrap`: flex + nowrap + `align-items/align-content/justify-content:center` + `min-height/height:76px`.
- İç zincir (widget/container/gsc/logo): flex center, `width/height:100%/76px`.
- `#menu-anamenu-desktop` / `.548f702 .gva-main-menu`: `justify-content:center`, `align-items:center`, `width:100%`, `height:76px`.
- `li > a`: `inline-flex` + `align-items:center`.

## CSS Diff Özeti
```css
html body .elementor-element-aa903d8 > .elementor-widget-wrap {
  display: flex !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  align-content: center !important;
  justify-content: center !important;
  min-height: 76px !important;
}
html body #menu-anamenu-desktop,
html body .elementor-element-548f702 .gva-main-menu {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  width: 100% !important;
  height: 76px !important;
}
```

## QA Checklist
- [x] Repo `Ust-Menu/ust-menu.html` masaüstü CSS güncellendi
- [x] `--layout-only --apply` snippet 5026, location `elementor_body_end`, cache 200
- [x] Canlı: `aa903d8 > .elementor-widget-wrap` + align/justify/align-content center
- [x] Canlı: `#menu-anamenu-desktop` + justify-content:center
- [x] Playwright 1440px: logoDx=0, logoDy=0, menu pad simetrik
- [x] Logo media tekrar yüklenmedi (`ledajans-logo-white.webp`)
- [x] Secret commit yok
