# AGENT-HUB TASKS

## Pending Backlog (Sprint-1 Başlangıç)

| ID | Öncelik | Rol | Görev | Durum |
|---|---|---|---|---|
| P-001 | P0 | tech-seo | Crawl/index engelleyen teknik hataları tespit et, dry-run düzeltme planı çıkar | In Progress |
| P-002 | P0 | gsc | Kapsam/indeks raporundan kritik dışlanan URL kümelerini çıkar | In Progress |
| P-003 | P1 | content | "led ekran" ve ticari alt kelimeler için mevcut sayfa optimizasyon listesi üret | Queued (P0 sonrası) |
| P-004 | P1 | internal-link | Para sayfalara iç link fırsatlarını çıkar, anchor öneri seti hazırla | Queued (P0 sonrası) |
| P-005 | P1 | serp-watch | Ana ve ticari alt kelimeler için baseline SERP takip tablosu kur | Queued (P0 sonrası) |
| P-006 | P2 | content | Yeni içerik ihtiyacını topic cluster olarak öner (yalnızca mevcut içerik güncellemesi sonrası) | Pending |

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

## Self-Spawn Kuralları
- Teknik veya indeksleme analizinde yeni bir uzmanlık ihtiyacı doğarsa TASKS'a `"[NEW:<rol>]"` etiketiyle eklenir.
- Yeni rol yalnızca mevcut rollerin kapsam dışı bıraktığı işi alır.
