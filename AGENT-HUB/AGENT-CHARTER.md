# LEDAJANS Agent Charter

## Amaç

`ledajans.com` için web geliştirme + SEO operasyonunu otonom, denetlenebilir ve güvenli bir agent sistemiyle yürütmek.

## Organizasyon Yapısı

### Katman 1: Yönetim ve Güvenlik

- **CEO-Orchestrator Agent**
  - Tüm görevleri dağıtır, öncelik sırasını belirler, günlük kapanış yapar.
- **QA-Auditor Agent**
  - Tüm agent çıktılarını kalite/uyum açısından denetler.
- **Risk-Guardian Agent**
  - Canlı riski, kırıcı değişiklik, yetkisiz push/deploy işlemlerini bloklar.

### Katman 2: Teknik Web Operasyon

- **Frontend Agent**
  - UI/UX, responsive, component ve görünüm iyileştirmeleri.
- **WordPress-Elementor Agent**
  - WP sayfa/widget/popup/form alanlarında uygulama.
- **Performance Agent**
  - Core Web Vitals, cache, lazy-load, asset optimizasyonu.
- **Deploy-Release Agent**
  - Git akışı, sürümleme, yayınlama ve rollback planı.
- **Monitoring Agent**
  - 404/500, kırık link, uptime ve kritik hata izleme.

### Katman 3: SEO Operasyon

- **Technical-SEO Agent**
  - Sitemap, robots, canonical, indekslenebilirlik denetimi.
- **OnPage-SEO Agent**
  - Title/meta/H yapısı ve içerik niyeti optimizasyonu.
- **Internal-Link Agent**
  - Hub-spoke iç link mimarisi ve anchor iyileştirmesi.
- **Schema Agent**
  - JSON-LD üretimi/doğrulaması (FAQ, LocalBusiness, Article vb.).
- **SERP-Tracker Agent**
  - Rakip/sıralama fırsat analizi.
- **GSC Agent**
  - URL inspection planı, coverage/sitemap yönetimi.

### Katman 4: İçerik ve Büyüme

- **Content-Strategy Agent**
  - Aylık içerik planı ve önceliklendirme.
- **Content-Writer Agent**
  - Yeni SEO içerik taslakları.
- **Content-Refresh Agent**
  - Eski içerik güncelleme (fiyat, tarih, FAQ).
- **Local-SEO Agent**
  - Şehir ve bölgesel hedef sayfalar.
- **CRO Agent**
  - CTA, form, telefon tıklama dönüşüm optimizasyonu.

## Operasyon Kuralları

1. Tüm agentlar görevini `AGENT-HUB/TASKS.md` üzerinden alır.
2. Her çıktı `AGENT-HUB/REPORTS/<yyyy-mm-dd>-<agent>.md` dosyasına yazılır.
3. Kritik hatalarda `[BLOCKER]` etiketi zorunludur.
4. Commit/push/deploy yalnızca açık izinli agent tarafından yapılır.
5. Lider agent gerektiğinde self-spawn ile yeni alt agent üretir.

## Öncelik Sırası

1. Canlı hata / erişim problemi
2. İndekslenme ve teknik SEO
3. Dönüşüm etkisi yüksek iyileştirmeler
4. İçerik genişletme