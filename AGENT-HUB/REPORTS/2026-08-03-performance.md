# Performance Report - 2026-08-03

## Situation
- Lighthouse SEO/BP ~100; mobil Perf 42–49 (LCP 6.5–10.9s). SEO tarafı güçlü; öncelik mobil CWV.
- Apify MCP: kullanıcının masaüstü Cursor’unda bağlı olabilir; bu Cloud Agent oturumunda `needsAuth` (ayrı kimlik alanı).

## Decision
SEO meta/içerik turu ertelendi. Mobil performans patch uygulandı.

## Applied Changes
- `wordpress-mobil-hiz-patch.php`: site geneli GTM idle+delay, tema JS footer+defer, block-editor/components dequeue, FA async CSS, CF7/chaty ana sayfa mobil drop, hero preload q60.
- `Anasayfa/Hero.html`: `picture` + q60 only (DPR ile q72 LCP kaçışı kapatıldı), width/height.

## QA / Validation
- [ ] Patch’i `mu-plugins/ledajans-perf-patch.php` olarak canlıya koy
- [ ] Hero widget’ı WP’ye deploy et
- [ ] Mobil Lighthouse yeniden ölç (hedef LCP &lt; 4s, Perf ≥ 70)
- [ ] Ana sayfa ikonlar / CF7 iletişim sayfası duman testi

## Handoff
- `wordpress-deploy`: Hero dry-run → onaylı canlı
- `qa-auditor`: ikon + form regresyon
