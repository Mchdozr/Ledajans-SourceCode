# Koalisyon Protokolü

Tüm ajanlar bu protokole uyar. Kelime öncelikleri: `KEYWORD-GUARD.json`.

## Tur Zamanlaması (TR)

| Saat | Faz | Komut | Ajanlar |
|------|-----|-------|---------|
| 09:30 | Keşif | `run-coalition-cycle.py --phase discover` | ceo-orchestrator, gsc-serp, tech-seo |
| 13:00 | Uygulama | `coalition-apply.py` | wordpress-deploy, qa-auditor, risk-guardian |
| 17:00 | Kapanış | `run-coalition-cycle.py --phase close` | ceo-orchestrator, qa-auditor |

## Kelime Önceliği

1. **P0** — `led ekran*` (savunma): SERP #1, GSC avg ≤ 5
2. **P1** — 7 ürün kategorisi (büyüme): GSC avg ≤ 10

Alarm → otomatik sprint görevi (`TASKS.md` P-016…P-022 veya `[ALARM:P0]` / `[ALARM:P1]`).

## Tartışma Formatı

### İtiraz
```
[TO:<hedef-rol>] [FB:<BENZERSIZ-ID>] <mesaj>
```

### Çözüm
```
[RESOLVED:<FB-ID>] <çözüm özeti>
```

### Yeni rol
```
[NEW:<rol-adı>]
```

`auto_orchestrator.py` → `Auto Feedback Queue`. Açık FB varken deploy kilidi aktif.

## Deploy Kilidi

`coalition-apply.py` şu koşullarda **çalışmaz** (exit 2):

- Raporlarda çözülmemiş `[FB:*]` var
- `BLOCKER-ALERT.md` aktif
- `.coalition-status.json` → `"deploy_locked": true`

## Risk Katmanları

| Tier | Örnek | Uygulama |
|------|-------|----------|
| T1 | Blog, meta, iç link, schema | Otomatik |
| T2 | Performans patch, hero, alt text | Otomatik + rollback notu |
| T3 | robots, canonical, noindex, ana sayfa hero | BLOCKER — log only |

## Uygulama Kuyruğu

```
[APPLY:T1] scripts/publish-blog-post.py Blog/slug.html --publish
[APPLY:T2] deploy-to-wordpress.py (slug: led-ekran-nedir)
```

## CSS Kilidi (visual-ux)

- Blog: `ledajans-seo-article` + CTA `#f46f2c`
- Ürün sayfaları: mevcut `Urunlerimiz/` stillerine uyum
- Global tema CSS değişikliği yasak

## P0 Alarm Protokolü

Tetik: SERP rank ≥ 2 VEYA GSC `led ekran` pozisyonu +2 artış.

1. gsc-serp → rakip delta
2. onpage-seo → hub title/meta/CTR
3. internal-link → hub anchor
4. performance → ana sayfa LCP

## P1 Alarm Protokolü

Tetik: kategori GSC pozisyonu +3 VEYA hedef > 10.

1. onpage-seo → kategori intent
2. content-seo → SSS/gap
3. internal-link → cross-link
4. schema → Product/FAQ

## Doğrulama

```bash
python3 deploy-to-wordpress.py --dry-run
python3 scripts/run-coalition-cycle.py --phase discover
```
