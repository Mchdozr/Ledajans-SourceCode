# Visual-UX — `/gob-led-nedir/` (2026-08-20)

**Kapsam:** Sözlük widget `SEO-Icerik-Widgets/sozluk/gob-led-nedir.html` görselsiz; `<style>` yok, `ledajans-seo-article` yalnızca global Ek CSS’e bağlı. Yeni global CSS yazılmadı.

**Kaynak:** `Blog/huidu-wf1-wf2-wf4-led-kontrol-karti.html` gömülü stil + `Ek-CSS-final.css` bölüm 13.

## Viewport Issues
- Widget stilsiz: gri kutu, turuncu H2 çizgisi, CTA butonu ve img radius görünmüyor.
- Tablo yok; yine de gömülü stilde tablo kuralları (Huidu/bölüm 13 parity) gerekli.
- Mobil: ≥640px padding artışı; tablo varsa yatay scroll.

## Copy Fixes
- Metin uygun. CTA metni zaten **FİYAT ALIN** (`a.ledajans-seo-cta` → `/iletisim/`).
- Gömülü stilde `font-family: inherit` — Huidu’daki `ui-sans-serif` stack kopyalanmasın (site Kumbh).

## Visual/A11y Fixes
- Gövde metin `#374151` / başlık `#111827` / link-CTA `#f46f2c` — a11y kontrast mevcut palet.
- CTA `min-height: 48px`, beyaz yazı `!important`.
- Heading sırası: H2 → H3 (İlgili / SSS) — dokunulmadı.

## CSS Diff Özeti
- Global Ek CSS’e dokunulmadı.
- Uygulama: Huidu’daki `<style>` bloğunu widget başına kopyala; **font inherit**; img `border-radius: 0.75rem` (bölüm 13).

## QA Checklist
Widget içine gömülecek CSS özeti (8–12 madde) parent yanıtta.
