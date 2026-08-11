# AGENT-HUB STATE

## Sprint
- Sprint: 2026-08 Koalisyon / apply-with-gates
- Orchestrator: ceo-orchestrator
- Öncelik Kuralı: P0 led ekran* > teknik hata > indeks > P1 kategori > performans > içerik

## Hedef
- P0 savunma: `led ekran*` kümesi — SERP #1 koruma + GSC avg pozisyon ≤ 5
- P1 büyüme: COB/Smart Screen, İç/Dış Mekan LED, Rental, İç/Dış RGB Panel, Kontrol Kartları — top 10
- Kelime manifestosu: `AGENT-HUB/KEYWORD-GUARD.json`
- Kapsam: teknik SEO, indeksleme, içerik, iç link, GSC, SERP, performans, otonom deploy (kapılı)

## Agent Rolleri
- tech-seo, content, internal-link, gsc, serp-watch (rapor rolleri)
- Cursor kalıcı: `.cursor/agents/` (ceo-orchestrator, tech-seo, onpage-seo, performance, content-seo, blog-ajan, internal-link, schema, visual-ux, gsc-serp, wordpress-deploy, qa-auditor, mcp-connector, risk-guardian)

## Mevcut Durum
- AGENT-HUB yapısı aktif; 20 dakikalık orkestratör döngüsü çalışıyor.
- 2026-08-03: Cursor stack + kalıcı alt ajanlar (`CURSOR-STACK-RESEARCH.md`). Backlog P-010…P-015.
- 2026-08-11: Otonom koalisyon — `apply-with-gates`, `KEYWORD-GUARD.json`, `COALITION-PROTOCOL.md`.

## Çalışma Modu (Zorunlu): apply-with-gates

- **Keşif turu (09:30 TR):** Rapor + alarm; `python3 scripts/run-coalition-cycle.py --phase discover`
- **Uygulama turu (13:00 TR):** T1/T2 otomatik; `python3 scripts/coalition-apply.py` (açık FB veya BLOCKER yoksa)
- **Kapanış turu (17:00 TR):** Doğrulama + `DAILY-SUMMARY.md`
- **Deploy kilidi:** Açık `[FB:*]` / `[OBJECT:*]` varken `coalition-apply.py` çalışmaz
- **Spawn:** Lider `[NEW:<rol>]`; uzmanlar `[SPAWN-REQ]` → lider Kabul/Red
- **Tartışma:** `[IDEA|OBJECT|AGREE|FB]`; 2 turda kapanmayan OBJECT → `[CEO-DECISION]`
- **Risk katmanları:** T1/T2 otomatik; T3 (robots/canonical/noindex/ana sayfa hero) → BLOCKER
- **CSS kilidi:** `visual-ux` — `ledajans-seo-article`, CTA `#f46f2c`, global CSS yasak
- Kurulum: `AGENT-HUB/COALITION-SETUP.md`

## Sürekli Worker Operasyon Modu (20dk)
- Model: koalisyon döngüsü; keşif → tartışma → QA → risk → uygulama → doğrulama.
- Her rol raporunda:
  - `### Situation` (KEYWORD-GUARD alarm durumu dahil)
  - `### Decision`
  - `### Proposed Changes` (T1/T2 için uygulanabilir diff; T3 için yalnız öneri)
  - `### QA/Validation`
  - `### Handoff`
- Zaman standardı: `TR (Europe/Istanbul)`.
