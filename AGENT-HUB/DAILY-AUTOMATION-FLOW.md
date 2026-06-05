# Daily Automation Flow

## Günlük Otonom Döngü

### 09:30 - Sabah Kontrol

1. CEO-Orchestrator:
  - `STATE.md` + `TASKS.md` okur.
  - Günü sprintlere böler.
2. Technical-SEO + Monitoring:
  - sitemap, robots, canonical, 404/500 kontrolü.
3. GSC Agent:
  - URL inspection günlük kotasını planlar.

### 13:00 - İçerik ve Yapısal İyileştirme

1. Content-Strategy + SERP-Tracker:
  - fırsat sorgu kümelerini günceller.
2. Content-Writer + Content-Refresh:
  - yeni içerik / güncelleme üretir.
3. Internal-Link + Schema:
  - hub-spoke ve JSON-LD iyileştirmelerini çıkarır.

### 17:00 - Kapanış ve Yayın Kararı

1. QA-Auditor:
  - tüm raporları kalite ve tutarlılık açısından doğrular.
2. Risk-Guardian:
  - canlı risk değerlendirmesi yapar.
3. Deploy-Release:
  - onaylı işleri yayın listesine alır.
4. CEO-Orchestrator:
  - `MASTER-PLAN.md`, `TASKS.md`, `DAILY-SUMMARY.md` günceller.

## Saat 17:15 Otomasyon

- Windows Scheduled Task: `Ledajans-Weekday-GitPull-1715`
- Görev: hafta içi her gün `git pull --ff-only origin master`
- Log: `AGENT-HUB/git-pull-log.txt`

## Blokaj Protokolü

- Kritik durumda rapora `[BLOCKER]` yazılır.
- Lider agent hemen görev önceliğini değiştirir.
- Gerekirse self-spawn ile yeni uzman agent açılır.