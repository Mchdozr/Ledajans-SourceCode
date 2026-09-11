# AGENT-HUB STATE

## Sprint
- Sprint: 2026-05 İlk Sprint / Tur-1
- Orchestrator: lider-orchestrator
- Öncelik Kuralı: teknik hata > indekslenme > içerik güncelleme > yeni içerik

## Hedef
- P0 savunma: `led ekran*` kümesi — SERP #1 koruma + GSC avg pozisyon ≤ 5
- P1 büyüme: COB/Smart Screen, İç/Dış Mekan LED, Rental, İç/Dış RGB Panel, Kontrol Kartları — top 10
- Kelime manifestosu: `AGENT-HUB/KEYWORD-GUARD.json`
- Kapsam: teknik SEO, indeksleme, içerik, iç link, GSC, SERP, performans, otonom deploy (kapılı)

## Agent Rolleri
- tech-seo, content, internal-link, gsc, serp-watch (rapor rolleri)
- Cursor kalıcı: `.cursor/agents/` (ceo-orchestrator, tech-seo, onpage-seo, performance, content-seo, internal-link, schema, visual-ux, gsc-serp, wordpress-deploy, qa-auditor, mcp-connector, risk-guardian)

## Mevcut Durum
- AGENT-HUB yapısı bu sprint başlangıcında oluşturuldu.
- İlk tur görev dağıtımı aktif.
- 20 dakikalık otonom kontrol döngüsü çalışıyor.
- 2026-08-03: Cursor stack araştırması + kalıcı alt ajanlar eklendi (`CURSOR-STACK-RESEARCH.md`). Backlog P-010…P-015 açıldı.
- 2026-08-11: Otonom koalisyon modu — `apply-with-gates`, `KEYWORD-GUARD.json`, `COALITION-PROTOCOL.md`.

## Çalışma Modu (Zorunlu): apply-with-gates

- **Keşif turu (09:30 TR):** Rapor + alarm; `run-coalition-cycle.py --phase discover`
- **Uygulama turu (13:00 TR):** T1/T2 otomatik; `coalition-apply.py` (açık FB veya BLOCKER yoksa)
- **Kapanış turu (17:00 TR):** Doğrulama + `DAILY-SUMMARY.md`
- **Deploy kilidi:** Açık `[FB:*]` varken `coalition-apply.py` çalışmaz
- **Risk katmanları:** T1/T2 otomatik; T3 (robots/canonical/noindex/ana sayfa hero) → BLOCKER, sadece log
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
- Zaman standardı: tüm dashboard/rapor saatleri `TR (Europe/Istanbul)` formatında yazılır.
- Hedef: siteyi gerçek bir web ekibi disipliniyle yönetmek (planlama, uygulama tasarımı, kalite kontrol, izleme).
