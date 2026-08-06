# MASTER PLAN - 2026-05-06

## 0) İlk Tur Görev Dağıtımı (Lider-Orchestrator)

- tech-seo -> `AGENT-HUB/REPORTS/2026-05-06-tech-seo.md`
- gsc -> `AGENT-HUB/REPORTS/2026-05-06-gsc.md`
- content -> `AGENT-HUB/REPORTS/2026-05-06-content.md`
- internal-link -> `AGENT-HUB/REPORTS/2026-05-06-internal-link.md`
- serp-watch -> `AGENT-HUB/REPORTS/2026-05-06-serp-watch.md`

Teslim kuralı: Her raporda ilgili rol şablon başlıkları dolu olacak, kritik durum varsa satır bazında `[BLOCKER]` etiketi kullanılacak.

## 1) Critical / High Issues (Öncelik Sırasıyla)

### Critical (P0)

1. Crawl/Index engelleri (robots.txt, noindex, canonical çakışmaları, sitemap tutarsızlıkları, 4xx/5xx)
2. GSC'de dışlanan kritik URL kümeleri (özellikle para sayfalar ve "led ekran" intent URL'leri)

### High (P1)

1. Mevcut para sayfalarda intent uyuşmazlığı (title/H1/meta ve içerik odak kayması)
2. İç link yapısında para sayfalara zayıf akış (kaynak-hedef-anchor dengesizliği)
3. Baseline SERP izleme eksikliği (ölçülemeyen ilerleme riski)

## 2) 7 Günlük Uygulama Planı (Gün Gün)

### Gün 1

- `P-001` için teknik tarama ve dry-run tespit tablosu oluştur.
- Çıktı: `AGENT-HUB/REPORTS/2026-05-06-tech-seo.md`

### Gün 2

- `P-002` için GSC dışlanan URL kümelerini neden bazlı grupla ve etki skoru ver.
- Çıktı: `AGENT-HUB/REPORTS/2026-05-06-gsc.md`

### Gün 3

- P0 çıktılarıyla düzeltme backlog'u netleştir, riskli maddeleri yalnız dry-run ile işaretle.
- Çıktı: `AGENT-HUB/TASKS.md` durum güncellemesi + `AGENT-HUB/DAILY-SUMMARY.md`

### Gün 4

- `P-003` mevcut sayfa optimizasyonu (title/H1/meta/içerik intent hizası) taslaklarını hazırla.
- Çıktı: `AGENT-HUB/REPORTS/2026-05-06-content.md`

### Gün 5

- `P-004` iç link matrisi (kaynak URL -> hedef para sayfa -> anchor tipi) oluştur.
- Çıktı: `AGENT-HUB/REPORTS/2026-05-06-internal-link.md`

### Gün 6

- `P-005` baseline SERP tablosu + rakip farkı + volatilite notları başlat.
- Çıktı: `AGENT-HUB/REPORTS/2026-05-06-serp-watch.md`

### Gün 7

- Haftalık konsolidasyon, Go/No-Go kontrolü, P-006 için koşul kontrolü.
- Çıktı: `AGENT-HUB/REPORTS/<tarih>-orchestrator.md` + `AGENT-HUB/DAILY-SUMMARY.md`

## 3) Hangi Değişiklik Hangi Dosyada Yapılacak (Net Liste)

### Orkestrasyon ve Takip Dosyaları

- `AGENT-HUB/REPORTS/2026-05-06-tech-seo.md` -> teknik bulgular, dry-run planı, risk
- `AGENT-HUB/REPORTS/2026-05-06-gsc.md` -> dışlanan kümeler, index öncelik kuyruğu
- `AGENT-HUB/REPORTS/2026-05-06-content.md` -> mevcut sayfa içerik revizyonları
- `AGENT-HUB/REPORTS/2026-05-06-internal-link.md` -> iç link kaynak/hedef/anchor planı
- `AGENT-HUB/REPORTS/2026-05-06-serp-watch.md` -> baseline ve rakip fark tablosu
- `AGENT-HUB/TASKS.md` -> görev durumları, yeni rol üretimi `[NEW:<rol>]`
- `AGENT-HUB/DAILY-SUMMARY.md` -> günlük ilerleme ve blokajlar

### Site Üzerinde Uygulanacak Hedef Dosyalar

- `/workspace/Anasayfa/*` -> ana sayfa SEO alanları (başlık, heading, içerik blokları)
- `/workspace/Urunlerimiz/*` -> para sayfa içerik ve ticari intent revizyonları
- `/workspace/Blog/*` -> destekleyici içeriklerden para sayfalara iç link enjeksiyonu
- `/workspace/*sitemap*` (varsa) -> sitemap URL kapsam ve güncellik
- `/workspace/*robots*` (varsa) -> crawl direktif düzeltmeleri

## 4) Hangi İşler Otomatik, Hangileri Manuel

### Otomatik

- Görev durumu ve rapor konsolidasyonu (AGENT-HUB dosyalarına yazım)
- Teknik bulgu şablonlama ve dry-run plan kaydı
- İç link fırsat matrisi üretimi
- SERP baseline tablo üretim şablonu

### Manuel

- GSC panel doğrulaması ve "Validate Fix" akışı
- Canlı robots/canonical/noindex değişiklik onayı
- İçerik metni son editoryal kalite kontrolü
- Üretim yayını sonrası nihai SERP yorumlama

## 5) Beklenen SEO Etkisi (Kısa)

- Kısa vadede: crawl/index engelleri temizlenirse para sayfaların indekslenme ve görünürlük oranı artar.
- Orta vadede: mevcut sayfa optimizasyonu + iç link güçlendirmesiyle "led ekran" ve ticari alt sorgularda sıra kazanımı beklenir.
- Ölçüm: P-005 baseline'a göre haftalık pozisyon farkı ve indekslenen URL artışı takip edilir.

## 6) Sürekli Brainstorm / Karşı-Argüman Döngüsü

- Frekans: Her 20 dakikada 1 tur.
- Her rol, diğer 4 rol raporunu okuyup kendi raporuna şu blokları ekler:
  - `### Cross-Agent Challenges`
  - `### Counter Arguments`
  - `### Consensus Update`
- Kural: Çelişki varsa kanıtla itiraz et; çözülemeyen noktalarda `[BLOCKER]` bırak.
- Kod değişikliği asla uygulanmaz; sadece `Proposed Changes (No Apply)` güncellenir.
- Orchestrator görevi:
  - Çatışmaları toplayıp `TASKS.md` durumlarını güncellemek
  - Gerekirse `TASKS.md` içine `[NEW:<rol>]` açmak
  - Kritik blokajı tek onay mesajına indirmek

## Auto Update Log

- 2026-05-06 11:06 UTC | Raporlar: 2026-05-06-content.md, 2026-05-06-gsc.md, 2026-05-06-internal-link.md, 2026-05-06-serp-watch.md, 2026-05-06-tech-seo.md | Aksiyon: TASKS.md durumları güncellendi
- 2026-05-06 11:18 UTC | Raporlar: 2026-05-06-content.md, 2026-05-06-gsc.md, 2026-05-06-internal-link.md, 2026-05-06-serp-watch.md, 2026-05-06-tech-seo.md | Aksiyon: TASKS.md durumları güncellendi
- 2026-05-06 11:46 UTC | Raporlar: 2026-05-06-content.md, 2026-05-06-gsc.md, 2026-05-06-internal-link.md, 2026-05-06-serp-watch.md, 2026-05-06-tech-seo.md | Aksiyon: Değişiklik algılandı, no-op
- 2026-05-06 12:29 UTC | Raporlar: 2026-05-06-content.md, 2026-05-06-gsc.md, 2026-05-06-internal-link.md, 2026-05-06-serp-watch.md, 2026-05-06-tech-seo.md | Aksiyon: Auto Feedback Queue güncellendi

- 2026-05-06 12:29 UTC | Raporlar: 2026-05-06-content.md, 2026-05-06-gsc.md, 2026-05-06-internal-link.md, 2026-05-06-serp-watch.md, 2026-05-06-tech-seo.md | Aksiyon: TASKS.md durumları güncellendi; Auto Feedback Queue güncellendi

- 2026-08-03 09:11 UTC | Raporlar: 2026-05-06-content-agent.md, 2026-05-06-content.md, 2026-05-06-gsc.md, 2026-05-06-internal-link-agent.md, 2026-05-06-internal-link.md, 2026-05-06-serp-watch-agent.md, 2026-05-06-serp-watch.md, 2026-05-06-tech-seo-agent.md, 2026-05-06-tech-seo.md, 2026-06-05-gsc-drilldown-audit.md, 2026-06-05-gsc-live.md, 2026-06-05-gsc-performance.md | Aksiyon: Değişiklik algılandı, no-op
