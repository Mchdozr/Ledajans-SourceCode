# SERP Watch Report - 2026-05-06

## Keyword Set
- anahtar kelime: led ekran | mevcut sıra: N/A | rakip: videowall.com.tr | fark: N/A | not: Baseline takip listesine eklendi; ölçüm bekleniyor.
- anahtar kelime: dış mekan led ekran | mevcut sıra: N/A | rakip: daktronics.com | fark: N/A | not: Ticari alt sorgu olarak izleme kapsamına alındı.
- anahtar kelime: mağaza led ekran | mevcut sıra: N/A | rakip: samsung.com/tr/business | fark: N/A | not: Dönüşüm odaklı sorgu; ilk ölçümle birlikte segmentlenecek.
- anahtar kelime: led ekran fiyatları | mevcut sıra: N/A | rakip: sahibinden.com | fark: N/A | not: Fiyat niyeti yüksek sorgu, ayrı izlenecek.

## Baseline Positions
- [BLOCKER] anahtar kelime: led ekran | mevcut sıra: N/A | rakip: videowall.com.tr | fark: N/A | not: SERP çekim kaynağı (GSC/harici rank tracker) henüz paylaşılmadığı için baseline doğrulanamadı.
- [BLOCKER] anahtar kelime: dış mekan led ekran | mevcut sıra: N/A | rakip: daktronics.com | fark: N/A | not: Ölçüm verisi yok; ilk snapshot alınmadan delta hesaplanamaz.
- [BLOCKER] anahtar kelime: mağaza led ekran | mevcut sıra: N/A | rakip: samsung.com/tr/business | fark: N/A | not: Lokasyon/country hedefi net değil, sıra verisi üretilemedi.
- [BLOCKER] anahtar kelime: led ekran fiyatları | mevcut sıra: N/A | rakip: sahibinden.com | fark: N/A | not: Mobil/desktop ayrımı tanımlanmadı; baseline seti beklemede.

## Competitor Delta
- [BLOCKER] anahtar kelime: led ekran | mevcut sıra: N/A | rakip: videowall.com.tr | fark: N/A | not: Kendi sıra değeri olmadan rakip delta hesaplanamadı.
- [BLOCKER] anahtar kelime: dış mekan led ekran | mevcut sıra: N/A | rakip: daktronics.com | fark: N/A | not: Rakip sıra snapshot'ı ve bizim baseline aynı gün alınmalı.
- [BLOCKER] anahtar kelime: mağaza led ekran | mevcut sıra: N/A | rakip: samsung.com/tr/business | fark: N/A | not: Rakip URL seviyesi eşleştirme doğrulanmadı.
- [BLOCKER] anahtar kelime: led ekran fiyatları | mevcut sıra: N/A | rakip: sahibinden.com | fark: N/A | not: Sorgu varyasyonları normalize edilmeden delta güvenilir değil.

## Volatility Notes
- anahtar kelime: led ekran | mevcut sıra: N/A | rakip: videowall.com.tr | fark: N/A | not: [BLOCKER] İlk haftalık volatilite notu için en az 2 ölçüm noktası gerekli.
- anahtar kelime: dış mekan led ekran | mevcut sıra: N/A | rakip: daktronics.com | fark: N/A | not: [BLOCKER] Veri yok; trend yönü (artış/azalış) atanamadı.
- anahtar kelime: mağaza led ekran | mevcut sıra: N/A | rakip: samsung.com/tr/business | fark: N/A | not: [BLOCKER] Sıra kaynağı standardize edilmeden volatilite takibi başlatılmayacak.
- anahtar kelime: led ekran fiyatları | mevcut sıra: N/A | rakip: sahibinden.com | fark: N/A | not: [BLOCKER] Ölçüm periyodu (günlük/haftalık) kilitlenmediği için oynaklık notu geçici.

## Execution Update - 2026-05-06 11:38 UTC
### Completed Analysis
- Baseline standardı netleştirildi: her anahtar kelime için tekil ölçüm kaydı `query + locale(tr-TR) + device(mobile/desktop) + search_engine(google) + serp_source + captured_at_utc + rank_position + target_url + primary_competitor + competitor_rank` alanlarıyla tutulmalı.
- Baseline kabul kriteri belirlendi: aynı gün içinde mobile ve desktop için en az 1'er ölçüm, aynı locale ve aynı sorgu normalizasyonu ile alınmış olmalı; bu koşul sağlanmadan `mevcut sıra` ve `fark` metrikleri "N/A" kalır.
- Volatilite başlangıç kuralı netleştirildi: trend/oynaklık yorumu için en az 2 zaman noktası (T0, T1) gerekir; güvenilir haftalık volatilite için minimum 3 ölçüm noktası (en az 7 gün yayılmış) gerekir.

### Proposed Changes (No Apply)
- `AGENT-HUB/REPORTS/2026-05-06-serp-watch.md` içinde "Baseline Positions" bölümüne şu standart not satırı eklensin: `Baseline Standard: tr-TR, Google, mobile+desktop, same-day snapshot, UTC timestamp required`.
- Ölçüm cadence planı aşağıdaki gibi sabitlensin:
  - Günlük: 09:00 UTC (mobile), 09:15 UTC (desktop) snapshot.
  - Haftalık: Çarşamba 12:00 UTC delta özeti (T-7 karşılaştırması).
  - Aylık: Her ayın ilk iş günü 10:00 UTC trend konsolidasyonu (MoM).
- Veri kalite kapıları eklensin:
  - Ölçüm kaynağı belirtilmemiş kayıtlar otomatik `[BLOCKER]`.
  - Locale/device eksik kayıtlar delta hesaplamasına dahil edilmez.
  - Aynı sorgunun yazım varyasyonları (ör. "led ekran fiyatı/fiyatları") normalize edilmeden tek satırda birleştirilmez.
- Rekabet karşılaştırması standardı eklensin: her sorgu için `primary_competitor` sabitlenir, değişiklik olursa not alanında gerekçe tutulur; aksi halde haftalık delta karşılaştırması bozulur.

### Data/Approval Needs
- [BLOCKER] İlk baseline için rank tracking kaynağı gerekli (GSC average position tek başına yeterli değilse harici tracker onayı gerekli).
- [BLOCKER] Hedef pazar netleşmeli: yalnızca `tr-TR` mi, yoksa çoklu ülke/language segmenti mi izlenecek.
- [BLOCKER] Nihai raporlama düzeyi onayı gerekli: domain-level rank mı, URL-level rank mı (öneri: URL-level).

### Next Step
- Onay sonrası ilk aynı-gün mobile+desktop snapshot alınarak `Baseline Positions` ve `Competitor Delta` bölümleri N/A'dan sayısal değerlere geçirilecek, ardından 7 günlük cadence döngüsü başlatılacak.

## Brainstorm Round - 2026-05-06 11:41 UTC

### Cross-Agent Objections
- **İtiraz (content):** `/dis-mekan-led-ekran/` için "harici linki nofollow + new tab ile sınırla" önerisi tek başına başarı metriği tanımlamıyor. Validasyon için değişiklik öncesi/sonrası en az 14 gün URL-level GSC CTR, average position ve internal click-through verisi olmadan bu aksiyonun SERP etkisi doğrulanamaz.
- **İtiraz (tech-seo):** `llms.txt` maddesi P1 olarak listelenmiş ancak sıralama etkisi için ölçülebilir bir acceptance metric belirtilmemiş. SERP takip açısından bu kalem, "rank/CTR/index" metriklerinde anlamlı değişim göstermediği sürece backlog'da deneysel olarak etiketlenmeli ve P0/P1 ticari sayfa metrikleriyle aynı öncelikte raporlanmamalı.
- **İtiraz (internal-link):** "Faz-1'de / ve /blog/ kaynaklarından 2-3 yüksek görünürlük link" önerisinde baz metrik eksik. Uygulama öncesi anchor bazlı internal click baseline ve hedef URL query cohort performansı (ör. led ekran, iç mekan led ekran) ölçülmeden faz etkisi izole edilemez.

### Self-Corrections
- Önceki SERP planında günlük snapshot saati önerildi ancak veri sağlayıcı gecikmesi (index update lag) için tolerans penceresi tanımlanmadı; düzeltme olarak her snapshot için `capture_window` alanı eklenecek (ör. 09:00-09:20 UTC).
- Rakip delta bölümünde tek rakip yaklaşımı korunurken SERP feature değişimleri (map pack, video, PAA) etkisini ayrı etiketleme eksikti; düzeltme olarak her ölçüm satırına `serp_features_present` alanı eklenecek.

### Proposed Changes (No Apply)
- `serp-watch` ölçüm şemasına yeni alanlar eklensin: `capture_window`, `serp_features_present`, `data_freshness_flag`, `measurement_note`.
- Çapraz doğrulama kuralı tanımlansın: content/internal-link kaynaklı her öneri için "ölçüm öncesi hipotez + başarı eşiği + gözlem penceresi" olmadan uygulama önceliği verilmesin.
- Deney kartı standardı eklensin (uygulamasız):  
  `Hypothesis` -> `Primary Metric (URL-level rank/CTR)` -> `Guardrail Metric (index coverage)` -> `Window (14d/28d)` -> `Rollback Condition`.

### Next Debate Question
- P0/P1 önerilerinde hangi minimum kanıt seti zorunlu olmalı: sadece GSC + SERP snapshot yeterli mi, yoksa internal click ve dönüşüm öncü sinyalleri de "go" kriterine dahil edilmeli mi?

## Execution Update - 2026-05-06 15:28 TR
### Completed Analysis
- Mevcut rapordaki `N/A` ve `[BLOCKER]` durumları yeniden doğrulandı; baseline üretimi için aynı gün mobile+desktop snapshot ön koşulu hâlâ sağlanmadığı için sayısal delta hesaplarına geçilmedi.
- Önceki turdaki ölçüm şeması önerileri (capture window, SERP feature etiketleme, veri tazeliği işareti) sprint hedefiyle uyumlu bulundu ve bu turda ekipten veri sağlayıcı netliği talebi önceliklendirildi.
- `tr-TR + Google + UTC zaman damgası` standardı korunarak metrik tutarlılığı riski yeniden değerlendirildi; locale/device eksikliği devam ettiği için oynaklık yorumu ertelendi.

### Team Sync Notes
- content önerileri: **Kabul** — ölçüm öncesi/sonrası 14 günlük pencere şartı SERP etki atfı için uygun.
- internal-link önerileri: **Revize** — anchor ekleme adımları değerli, ancak uygulama öncesi query cohort bazlı baseline zorunlu olmalı.
- tech-seo önerileri: **Kabul** — canonical ve indeksleme hijyeni tamamlanmadan rank dalgalanması analizi yanıltıcı kalır.
- [TO:gsc] [FB:SW-001] `led ekran`, `dış mekan led ekran`, `mağaza led ekran`, `led ekran fiyatları` için aynı gün (TR locale) mobile+desktop URL-level sıra snapshot'larını ve veri kaynağı bilgisini paylaş.

### Proposed Changes (No Apply)
- `AGENT-HUB/REPORTS/2026-05-06-serp-watch.md` için operasyon notu standardı netleştirilsin: her anahtar kelime satırına `source` ve `device_scope` metaverisi eklensin (teknik etki: veri tutarlılığı, SEO etki: doğru delta yorumu, risk: eksik veriyle yanlış önceliklendirme).
- Haftalık delta yorumuna geçiş kuralı sabitlensin: `min 2 snapshot + aynı locale/device + aynı hedef URL eşleşmesi` olmadan fark metriği yayınlanmasın (teknik etki: yanlış pozitiflerin azalması, SEO etki: güvenilir trend okuması, risk: raporlama gecikmesi).
- Rakip karşılaştırma notuna SERP özellik satırı eklensin (`PAA/Video/Map var-yok`) (teknik etki: feature kaynaklı oynaklığı ayrıştırma, SEO etki: fırsat alanı görünürlüğü, risk: manuel etiketleme yükü).

### QA / Risk Check
- [BLOCKER] GSC tarafında URL-level pozisyon verisi veya harici rank tracker kaynağı olmadan baseline kapanışı yapılamaz.
- Risk: Farklı zaman pencerelerinde alınan snapshot'lar yapay volatilite üretebilir; bu nedenle capture window standardı zorunlu tutulmalı.
- Kontrol listesi: (1) locale doğrulandı mı, (2) mobile+desktop birlikte var mı, (3) target URL sabit mi, (4) rakip URL eşleşmesi doğrulandı mı.

### Data/Approval Needs
- GSC/ölçüm sahibi ekipten veri kaynağı onayı: tek kaynak mı, hibrit kaynak mı kullanılacak.
- Orchestrator onayı: haftalık raporda URL-level metrik zorunlu alan olarak kilitlensin mi.
- İş birimi onayı: raporlamada birincil cihaz mobile mı olacak, yoksa mobile/desktop eşit ağırlıklı mı izlenecek.

### Next Step (Owner + ETA)
- Owner: serp-watch (bağımlı rol: gsc) | ETA: Tur+1 (yaklaşık 20 dk) — `SW-001` geri bildirimi yanıtlanır yanıtlanmaz baseline satırları sayısal değerlerle güncellenecek ve ilk güvenilir competitor delta hesaplanacak.
