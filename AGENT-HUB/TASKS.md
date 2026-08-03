# AGENT-HUB TASKS

## Pending Backlog (Sprint-1 Başlangıç)

| ID | Öncelik | Rol | Görev | Durum |
|---|---|---|---|---|
| P-001 | P0 | tech-seo | Crawl/index engelleyen teknik hataları tespit et, dry-run düzeltme planı çıkar | Done |
| P-002 | P0 | gsc | Kapsam/indeks raporundan kritik dışlanan URL kümelerini çıkar | Done |
| P-003 | P1 | content | "led ekran" ve ticari alt kelimeler için mevcut sayfa optimizasyon listesi üret | Done |
| P-004 | P1 | internal-link | Para sayfalara iç link fırsatlarını çıkar, anchor öneri seti hazırla | Done |
| P-005 | P1 | serp-watch | Ana ve ticari alt kelimeler için baseline SERP takip tablosu kur | Done |
| P-006 | P2 | content | Yeni içerik ihtiyacını topic cluster olarak öner (yalnızca mevcut içerik güncellemesi sonrası) | Done |
| P-010 | P0 | performance | Mobil LCP &lt; 4s: render-blocking, hero preload, unused CSS/JS; patch doğrula | In Progress (patch uygulandı — canlı mu-plugin + Hero deploy gerekli) |
| P-011 | P0 | tech-seo / gsc-serp | Index triage + para URL Inspection kuyruğu yenile; open FB’leri kapat | Pending |
| P-012 | P1 | onpage-seo | CTR düşük sorgular için title/meta revizyon taslağı | Pending |
| P-013 | P1 | visual-ux | color-contrast, heading-order, link-name düzeltme planı | Pending |
| P-014 | P1 | mcp-connector | WP MCP eklenti seçimi + Cursor MCP bağlama checklist | Pending |
| P-015 | P2 | content-seo | Long-tail cluster publish checklist (P-006 devamı) | Pending |

## Cursor kalıcı ajanlar (2026-08-03)

Konum: `.cursor/agents/`. Detay: `AGENT-HUB/CURSOR-STACK-RESEARCH.md`.

## Beklenen Çıktı Formatı (Rol Bazlı)

### tech-seo
- Başlık: `# Tech SEO Report - <yyyy-mm-dd>`
- Bölümler: `Scope`, `Findings(P0/P1)`, `Dry-Run Patch Plan`, `Apply Plan`, `Risk`, `Next Actions`
- Zorunlu alanlar: etkilenen URL, sorun tipi, öncelik, dry-run sonucu, önerilen değişiklik

### gsc
- Başlık: `# GSC Report - <yyyy-mm-dd>`
- Bölümler: `Coverage Snapshot`, `Excluded Clusters`, `Indexing Priority Queue`, `Validation Plan`
- Zorunlu alanlar: URL kümesi, dışlanma nedeni, etki skoru, önerilen aksiyon

### content
- Başlık: `# Content Report - <yyyy-mm-dd>`
- Bölümler: `Query Mapping`, `Page-Level Gaps`, `On-Page Update Draft`, `Deferred New Content`
- Zorunlu alanlar: hedef anahtar kelime, hedef URL, eksik alan, revizyon önerisi

### internal-link
- Başlık: `# Internal Link Report - <yyyy-mm-dd>`
- Bölümler: `Money Pages`, `Source Pages`, `Anchor Set`, `Link Injection Plan`
- Zorunlu alanlar: kaynak URL, hedef URL, anchor, yerleşim önerisi

### serp-watch
- Başlık: `# SERP Watch Report - <yyyy-mm-dd>`
- Bölümler: `Keyword Set`, `Baseline Positions`, `Competitor Delta`, `Volatility Notes`
- Zorunlu alanlar: anahtar kelime, mevcut sıra, rakip, fark, not

## 1. Tur Görev Dağıtım Planı

| Tur | Rol | Atanan Görevler | Çıktı Dosyası | Durum |
|---|---|---|---|---|
| 1 | tech-seo | P-001 | `AGENT-HUB/REPORTS/2026-05-06-tech-seo.md` | Assigned |
| 1 | gsc | P-002 | `AGENT-HUB/REPORTS/2026-05-06-gsc.md` | Assigned |
| 1 | content | P-003 | `AGENT-HUB/REPORTS/2026-05-06-content.md` | Assigned |
| 1 | internal-link | P-004 | `AGENT-HUB/REPORTS/2026-05-06-internal-link.md` | Assigned |
| 1 | serp-watch | P-005 | `AGENT-HUB/REPORTS/2026-05-06-serp-watch.md` | Assigned |
| 1 | content (deferred) | P-006 | `AGENT-HUB/REPORTS/2026-05-06-content.md` | Blocked (ön koşul: P-003) |

## İlk Tur Alt Agent Talimatları (Zorunlu Protokol)

- Global çalışma modu: `report-only`
- Alt agent kuralları:
  - Commit/push YASAK
  - Sadece `AGENT-HUB/*.md` dosyalarına yaz
  - Kod değişikliği gerekiyorsa yalnızca `proposed changes` olarak raporla, uygulama yapma
  - Push sadece kullanıcı saat verip açık onayladığında yapılır
- Standart prompt: `AGENT-HUB/AGENT-PROMPT-STANDARD.md`

### tech-seo (P-001)
- Çıktı dosyası: `AGENT-HUB/REPORTS/2026-05-06-tech-seo.md`
- Teslim formatı: `Scope`, `Findings(P0/P1)`, `Dry-Run Patch Plan`, `Apply Plan`, `Risk`, `Next Actions`
- Zorunlu alanlar: etkilenen URL, sorun tipi, öncelik, dry-run sonucu, önerilen değişiklik
- Kritik durumda: satıra `[BLOCKER]` etiketi ekle

### gsc (P-002)
- Çıktı dosyası: `AGENT-HUB/REPORTS/2026-05-06-gsc.md`
- Teslim formatı: `Coverage Snapshot`, `Excluded Clusters`, `Indexing Priority Queue`, `Validation Plan`
- Zorunlu alanlar: URL kümesi, dışlanma nedeni, etki skoru, önerilen aksiyon
- Kritik durumda: satıra `[BLOCKER]` etiketi ekle

### content (P-003)
- Çıktı dosyası: `AGENT-HUB/REPORTS/2026-05-06-content.md`
- Teslim formatı: `Query Mapping`, `Page-Level Gaps`, `On-Page Update Draft`, `Deferred New Content`
- Zorunlu alanlar: hedef anahtar kelime, hedef URL, eksik alan, revizyon önerisi
- Kritik durumda: satıra `[BLOCKER]` etiketi ekle

### internal-link (P-004)
- Çıktı dosyası: `AGENT-HUB/REPORTS/2026-05-06-internal-link.md`
- Teslim formatı: `Money Pages`, `Source Pages`, `Anchor Set`, `Link Injection Plan`
- Zorunlu alanlar: kaynak URL, hedef URL, anchor, yerleşim önerisi
- Kritik durumda: satıra `[BLOCKER]` etiketi ekle

### serp-watch (P-005)
- Çıktı dosyası: `AGENT-HUB/REPORTS/2026-05-06-serp-watch.md`
- Teslim formatı: `Keyword Set`, `Baseline Positions`, `Competitor Delta`, `Volatility Notes`
- Zorunlu alanlar: anahtar kelime, mevcut sıra, rakip, fark, not
- Kritik durumda: satıra `[BLOCKER]` etiketi ekle

## Self-Spawn Kuralları
- Teknik veya indeksleme analizinde yeni bir uzmanlık ihtiyacı doğarsa TASKS'a `"[NEW:<rol>]"` etiketiyle eklenir.
- Yeni rol yalnızca mevcut rollerin kapsam dışı bıraktığı işi alır.

## Sürekli Web Ops Döngüsü (20dk)
- Her turda tüm roller diğer raporları okuyup sadece itiraz değil, operasyonel çıktı üretir.
- Zorunlu ek blok:
  - `## WebOps Round - <yyyy-mm-dd HH:mm TR>`
  - `### Findings`
  - `### Cross-Team Notes`
  - `### Proposed Changes (No Apply)`
  - `### QA/Validation Plan`
  - `### Owner & ETA (Round-based)`
- Kural: Her rol bu turda en az 1 somut iş üretir (bugfix önerisi, içerik revizyonu, ölçüm planı, QA checklist).
- Kritik durumlar `[BLOCKER]` ile işaretlenir ve `MASTER-PLAN.md`'ye taşınır.
- Orchestrator görevi: round sonunda kabul edilen maddeleri sprint kuyruğuna işleyip rol sahipliği atamak.

## Otomatik Feedback -> Çözüm Döngüsü
- İtiraz/geri bildirim formatı zorunlu: `[TO:<rol>] [FB:<id>] <mesaj>`
- Hedef ajan çözüm ürettiğinde kendi raporuna şunu ekler: `[RESOLVED:<id>] <çözüm özeti>`
- `auto_orchestrator.py` bu etiketleri otomatik okuyup `Auto Feedback Queue` tablosunu günceller.
- Durum akışı: `Open` (yanıt bekliyor) -> `Closed` (çözüm üretildi).
- Kural: `Open` feedback, hedef rolün bir sonraki turunda öncelikli ele alınır.

## Auto Feedback Queue

| FB-ID | Kaynak Rol | Hedef Rol | Durum | Geri Bildirim | Kaynak Rapor |
|---|---|---|---|---|---|
| CONTENT-IL-001 | content | internal-link | Open | `/led-ekran/` ve alt para sayfalar için 1 exact-match + semantik varyasyon dağılımına uygun örnek anchor setini bir sonraki turda paylaş. | `2026-05-06-content.md` |
| GSC-TS-004 | gsc | tech-seo | Open | `/Urunlerimiz/*` için son 28 gün bazında reason kırılımına karşılık gelen dry-run aksiyon matrisi paylaş: `Duplicate/Google chose different canonical`, `Crawled - currently not indexed`, `Blocked by robots.txt` için URL adedi + önerilen fix tipi. | `2026-05-06-gsc.md` |
| IL-2026-05-06-01 | internal-link | gsc | Open | `/guc-kaynaklari/` vs `/power-supply/` için nihai kanonik URL kararını ve GSC URL Inspection sonucunu paylaş; karar gelmeden ilgili anchor ailesi genişletilmeyecek. | `2026-05-06-internal-link.md` |
| SW-001 | serp-watch | gsc | Open | `led ekran`, `dış mekan led ekran`, `mağaza led ekran`, `led ekran fiyatları` için aynı gün (TR locale) mobile+desktop URL-level sıra snapshot'larını ve veri kaynağı bilgisini paylaş. | `2026-05-06-serp-watch.md` |
| TS-SEO-001 | tech-seo | gsc | Open | Para sayfa registry için "kanonik URL listesi + exclusion nedeni" eşleşmesini tek tabloda paylaş; tech-seo tarafı bunu P0 kapanış kriteri doğrulamasında kullanacak. | `2026-05-06-tech-seo.md` |
