# LEDAJANS Cursor Stack Araştırma (Plugin · MCP · Ajan · SEO/UX/Perf)

Tarih: 2026-08-03  
Site: https://ledajans.com  
Amaç: Cursor içinde kalıcı alt ajan + MCP + plugin yığını ile SEO, görsel-metinsel ve performans seviyesini yükseltmek.

## 1) Mevcut durum (ölçüm)

| Metrik | Mobile | Desktop |
|--------|--------|---------|
| Performance | 0.42–0.49 | 0.89–0.92 |
| SEO | 1.0 | 1.0 |
| Best Practices | 1.0 | 1.0 |
| Accessibility | ~0.90 | ~0.91 |
| LCP | 6.5–10.9s | ~1.3s |
| FCP | 3.3–5.5s | ~1.0–1.3s |

Mobil darboğazlar: render-blocking (~2–4s), unused JS (~160KiB), unused CSS (~110–130KiB), main-thread, font-display, unsized images.  
A11y: color-contrast, heading-order, link-name.  
SEO teknik skor yüksek; CTR/snippet ve indeks kuyruğu ayrı savaş alanı (`SEO-KAPSAMLI-DENETIM-RAPORU-2026-04-29.md`).  
`psi-mobile.json`: Pagespeed API 429 (kota) — ölçüm için yerel Lighthouse tercih.

## 2) Cursor plugin / IDE yetenekleri

| İhtiyaç | Öneri | Not |
|---------|-------|-----|
| Canlı DOM / screenshot | Browser MCP | Sayfa doğrulama, CTA, CLS |
| SERP / scrape | Apify MCP | Auth gerekli (`needsAuth`) |
| Tasarım sync | Figma MCP | Hero/görsel uyum |
| Görev board | Linear / Asana / Slack | TASKS.md ile paralel |
| A11y | `scan-and-fix-accessibility` skill | Kontrast/heading |
| Cloud ops | `ledajans-cloud-run` skill | dry-run, orchestrator |
| WP içerik API | WordPress MCP eklentisi (aşağıda) | RankMath meta okuma/yazma |

Cursor Settings → Plugins / MCP: eksik auth olanları bağla (Apify, Canva). Secret’ları ortam değişkeninde tut.

## 3) MCP bağlama planı

### 3.1 Repoda eksik olanlar (kapatıldı / şablonlandı)
- `.cursor/agents/*` — 12 kalıcı ajan eklendi
- `.cursor/mcp.json.example` — WP + Apify şablonu
- `.cursor/rules/ledajans-subagents.mdc` — sorgusuz yönlendirme

### 3.2 WordPress MCP (canlı site — önerilen seçenekler)

RankMath kullanan LEDAJANS için öncelik sırası:

1. **WEBO MCP** (wordpress.org/plugins/webo-mcp) — RankMath meta merge, SEO article-analysis, mutate capability ayrımı
2. **Easy MCP AI** — RankMath + OAuth, GA/GSC köprüleri (ek entegrasyon)
3. **NIBWP** — Application Password + Abilities API; Elementor/RankMath tool yüzeyi
4. Fallback: mevcut `deploy-to-wordpress.py` + Application Password (MCP değil, REST)

Kurulum özeti:
1. WP’ye eklentiyi kur, token/OAuth al
2. Cursor → Settings → MCP → URL + Bearer (`LEDAJANS_WP_MCP_TOKEN`)
3. `.cursor/mcp.json.example` içeriğini yerel `mcp.json`’a kopyala (commit etme)
4. `mcp-connector` ajanı ile tool keşfi yap; mutate tool’ları onay kapısına al

### 3.3 Bu cloud oturumunda sunucu durumu (örnek tarama)
- ready: cursor-cloud, Figma, …
- needsAuth: Apify, Canva
- Browser/Appwrite: yükleme/ortam bağımlı

## 4) Görev atama modeli

Kaynak: `AGENT-HUB/AGENT-CHARTER.md` + `.cursor/agents/`

```
ceo-orchestrator
 ├─ tech-seo / gsc-serp          → P0 index
 ├─ performance / visual-ux      → mobil CWV + a11y
 ├─ onpage-seo / content-seo     → snippet + refresh
 ├─ internal-link / schema       → otorite + rich result
 ├─ wordpress-deploy             → dry-run → (onay) live
 └─ qa-auditor + risk-guardian   → kapı
```

Operasyon dosyaları: `TASKS.md`, `STATE.md`, `REPORTS/`, `auto_orchestrator.py` (20dk döngü).

Yeni backlog (bu araştırma sonrası):

| ID | Öncelik | Rol | Görev |
|----|---------|-----|-------|
| P-010 | P0 | performance | Mobil LCP &lt; 4s hedefi; render-blocking + hero preload doğrula |
| P-011 | P0 | tech-seo + gsc-serp | Index triage + para URL Inspection kuyruğu yenile |
| P-012 | P1 | onpage-seo | CTR düşük sorgular için title/meta revizyon |
| P-013 | P1 | visual-ux | Contrast + heading-order + link-name düzeltmeleri |
| P-014 | P1 | mcp-connector | WP MCP eklenti seçimi + Cursor bağlama checklist |
| P-015 | P2 | content-seo | Long-tail cluster publish (P-006 devamı) |

## 5) SEO + görsel-metinsel + performans yol haritası

### P0 — Performans (mobil)
- `wordpress-mobil-hiz-patch.php` canlı mu-plugin doğrula
- Render-blocking CSS/JS defer; Elementor/Swiper zaten footer’a taşınıyor — residual audit
- Hero LCP: `fetchpriority`, boyut, WebP; unsized-images düzelt
- Unused CSS/JS: sayfa bazlı dequeue listesini genişlet (`/projeler/` dahil)
- Font-display: optional/swap

### P0 — Teknik / indeks
- robots sert Disallow gözden geçir (`/*.php$`, plugins path)
- GSC excluded clusters → Validation Plan
- Canonical/www TLS zinciri

### P1 — On-page & metin
- Title uzun/kısa dağılımı (80 URL tarama: 34 uzun title, 25 bozuk H1)
- Meta description kırpılma; ana sayfa meta kısalt
- Para sayfa intent hizası (title/H1/body)

### P1 — Görsel UX
- Kontrast ve sıralı heading
- Hero tek kompozisyon; CTA netliği
- Figma MCP ile kritik sayfa mock vs canlı farkı (opsiyonel)

### P2 — İçerik büyüme
- `SEO-Icerik-Widgets` şehir/sektör gap’leri
- `llms.txt` güncelliği
- Schema Product/FAQ eksikleri

## 6) Kalıcı alt ajan envanteri

Konum: `.cursor/agents/` (project-level, git’te)

| Dosya | name |
|-------|------|
| ceo-orchestrator.md | ceo-orchestrator |
| tech-seo.md | tech-seo |
| onpage-seo.md | onpage-seo |
| performance.md | performance |
| content-seo.md | content-seo |
| internal-link.md | internal-link |
| schema.md | schema |
| visual-ux.md | visual-ux |
| gsc-serp.md | gsc-serp |
| wordpress-deploy.md | wordpress-deploy |
| qa-auditor.md | qa-auditor |
| mcp-connector.md | mcp-connector |
| risk-guardian.md | risk-guardian |

Çağrı: ana ajan ilgili işte Task/`subagent` olarak **sorgusuz** kullanır (rule: `ledajans-subagents.mdc`).

## 7) Doğrulama komutları

```bash
cd /workspace
python3 AGENT-HUB/auto_orchestrator.py && echo OK
python3 AGENT-HUB/live_dashboard.py && echo OK
python3 deploy-to-wordpress.py --dry-run
php -l wordpress-mobil-hiz-patch.php   # php varsa
```

## 8) Sonraki adımlar (manuel kullanıcı)
1. Cursor’da Apify (+ istenirse Canva) MCP auth
2. WP’ye WEBO MCP veya Easy MCP AI kur; token’ı Cursor MCP’ye ekle
3. Linear/Slack ile TASKS bildirim köprüsü (opsiyonel)
4. P-010…P-015 için cloud agent turu başlat
