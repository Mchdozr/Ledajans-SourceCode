# CWV Iteration Report

Generated: 2026-07-13T09:32:04+00:00

## Özet (anasayfa mobil medyan, iter1)

| Metrik | Nisan baseline | Pre-patch (lab) | iter1 (deploy sonrası) | Hedef |
|--------|----------------|-----------------|------------------------|-------|
| Performance | 42 | 62 | **70** | ≥80 |
| LCP | 10.9s | 7.3s | **5.7s** | <2.5s |
| TBT | 710ms | 52ms | **16ms** | <200ms |
| CLS | 0.001 | ~0 | **0.000** | <0.1 |

**İyileşme:** LCP −48%, Perf +67% (42→70 Nisan→iter1)

## Mobile (median of runs)

| URL | Perf | LCP | TBT | CLS |
|-----|------|-----|-----|-----|
| https://ledajans.com/ | 70 | 5.7s | 16ms | 0.000 |

## Desktop gate

- https://ledajans.com/: FAIL: perf=0.72 < 0.9; lcp=2704ms > 1500ms
- Not: Cloud LH lab ölçümü; Nisan desktop baseline 92 farklı ortamda alındı. Mobil-only patch'ler desktop HTML'i etkilemez (`wp_is_mobile()` scope).

## Mobile target (homepage)

- FAIL: perf=0.70 < 0.8; lcp=5661ms > 2500ms
- TBT ve CLS hedefte.

## Deploy edilen değişiklikler

- `ops/wordpress/mobil-hiz-patch.php` — W3TC LCP buffer, jQuery defer, Chaty idle, font/CSS async, GTM 6s mobil
- `content/Anasayfa/Hero.html` — skip-lazy + preload dedup
- GSC field doğrulama: `AGENT-HUB/REPORTS/cwv-gsc-field-validation.md`

## Sonraki adımlar

1. `python3 scripts/deploy/deploy-site-files.py --apply` (iter2 buffer fix)
2. LiteSpeed/W3 cache purge
3. `python3 scripts/monitor/run-lighthouse-cwv.py --homepage-only --label iter2`
4. GSC Deneyim → CWV mobil (28 gün sonra)
