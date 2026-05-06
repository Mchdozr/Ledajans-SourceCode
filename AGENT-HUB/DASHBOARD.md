# AGENT LIVE DASHBOARD

- Son yenileme: **2026-05-06 15:29:00 TR**
- Mod: report-only (commit/push yok)

## Rol Durumları

| Rol | Faz | Blocker Sayısı | Son Rapor Güncelleme |
|---|---|---:|---|
| 🟢 tech-seo | aktif | 2 | 15:28:43 TR |
| 🟢 gsc | aktif | 4 | 15:28:38 TR |
| 🟡 content | aktif | 5 | 15:28:36 TR |
| 🟡 internal-link | aktif | 2 | 15:28:39 TR |
| 🟡 serp-watch | aktif | 18 | 15:28:34 TR |

## Ajanlar Arası Canlı Diyalog Akışı

- **tech-seo**: **GSC raporuna itiraz:** `/Urunlerimiz/*` kümesi merkezli öncelikleme, mevcut URL yapısıyla teknik olarak doğrulanmış değil; diğer raporlarda aktif para sayfalar çoğunlukla kök altı slug'larda (`/led-ekran/`, `/ic-mekan-led-ekran/`, `/dis-mekan-led-ekran/`) geçiyor. Cluster tanımı path-varsayımıyla yapılırsa yanlış URL setinde "Validate Fix" dönebilir ve P0 eforu boşa gidebilir.
- **tech-seo**: **Internal-link raporuna itiraz:** `/dis-mekan-led-ekran` ve bazı hedeflerde trailing slash standardı tutarsız (`.../dis-mekan-led-ekran` vs `.../dis-mekan-led-ekran/`). Canonical/redirect standardı netleşmeden link enjeksiyonu önermek ölçümde canonical split ve crawl budget israfı yaratır.
- **gsc**: **Objection to tech-seo claim ("robots.txt aşırı kısıtlayıcı, P0 blocker")**: GSC reason dağılımı olmadan robots kaynaklı render/crawl engeli ana kök neden olarak kilitlenemez. Eğer `Blocked by robots.txt` veya `Indexed, though blocked by robots.txt` oranı düşükse, canonical/duplicate kümeleri daha yüksek öncelik almalıdır; aksi halde yanlış P0 sırası oluşur.
- **gsc**: **Objection to internal-link claim ("slug konsolidasyonu tamamlanmadan link enjeksiyonu dondurulsun")**: Link enjeksiyonunun tamamen durdurulması, halihazırda `Crawled - currently not indexed` olan para sayfalar için keşif sinyalini daha da zayıflatabilir. GSC açısından güvenli ara çözüm: yeni linkler yalnız mevcut kanonik URL setine sınırlı ve ölçümlü şekilde devam etmeli, sadece tartışmalı slug çifti dondurulmalıdır.
- **content**: **İtiraz #1 (tech-seo -> `llms.txt` önceliği):** Tech-SEO raporunda `llms.txt` P1 adımı teknik olarak faydalı olsa da, mevcut sprintin içerik/intent hedefi açısından dönüşüm etkisi düşük ve dikkat dağıtıcı. İçerik tarafında aynı eforun `/led-ekran/`, `/ic-mekan-led-ekran/`, `/dis-mekan-led-ekran/` ve `/rental-ekran/` sayfalarındaki ticari niyet netliğine ayrılması daha yüksek getiri üretir.
- **content**: **İtiraz #2 (internal-link -> anchor yoğun exact-match yaklaşımı):** Internal-link önerilerindeki exact-match anchor kullanımı (`led ekran`, `iç mekan led ekran`) kontrollü olsa da, içerik bağlamında fazla tekrar riski kullanıcı metin akışını yapaylaştırabilir. Anchor dağılımında daha fazla semantik varyasyon (örn. "iç mekan ekran çözümleri", "dış mekan görünürlüğü yüksek ekranlar") kullanmak intent tutarlılığını bozmadan okunabilirliği artırır.
- **internal-link**: [Content raporu](./2026-05-06-content.md) içindeki "`/blog/led-ekran-fiyatlari-2026/` ilk %30 bölümüne para sayfa linkleri ekleme" önerisine itiraz: erken ve yoğun commercial anchor enjeksiyonu, bilgi niyetli içerikte link bloklaşması yaratıp editoryal akışı bozabilir. Link mimarisi açısından blog -> hub (`/led-ekran/`) -> alt kategori kademesi korunmalı; doğrudan çoklu money-page dağıtımı tek adımda yapılmamalı.
- **internal-link**: [GSC raporu](./2026-05-06-gsc.md) içindeki "internal linklerde tek kanonik URL standardı uygula" ifadesi doğru yönlü olsa da eksik: yalnız URL standardizasyonu, anchor kümesindeki niyet ayrışması ve sayfa-şablon konumu kontrol edilmezse link equity yine yanlış sayfalara yığılır. İtiraz noktası, standardın sadece teknik URL tekilleştirme değil "kaynak tipi + anchor intent + tıklama derinliği" boyutlarıyla tanımlanması gerekliliği.
- **serp-watch**: **İtiraz (content):** `/dis-mekan-led-ekran/` için "harici linki nofollow + new tab ile sınırla" önerisi tek başına başarı metriği tanımlamıyor. Validasyon için değişiklik öncesi/sonrası en az 14 gün URL-level GSC CTR, average position ve internal click-through verisi olmadan bu aksiyonun SERP etkisi doğrulanamaz.
- **serp-watch**: **İtiraz (tech-seo):** `llms.txt` maddesi P1 olarak listelenmiş ancak sıralama etkisi için ölçülebilir bir acceptance metric belirtilmemiş. SERP takip açısından bu kalem, "rank/CTR/index" metriklerinde anlamlı değişim göstermediği sürece backlog'da deneysel olarak etiketlenmeli ve P0/P1 ticari sayfa metrikleriyle aynı öncelikte raporlanmamalı.

## Hızlı Dosya Kısayolları

- TASKS: `AGENT-HUB/TASKS.md`
- MASTER PLAN: `AGENT-HUB/MASTER-PLAN.md`
- DAILY SUMMARY: `AGENT-HUB/DAILY-SUMMARY.md`

## Orchestrator Son Log Satırları

- [2026-05-06 11:06:52 UTC] auto-orchestrator tick
- [2026-05-06 11:14:00 UTC] lider-orchestrator: ilk tur görev dağıtımı doğrulandı, çıktı yolları ve teslim formatı TASKS/MASTER-PLAN dosyalarına işlendi
- [2026-05-06 11:20:00 UTC] lider-orchestrator: kullanıcı kritik blokaj paketine onay verdi, icra fazına geçiş başlatıldı
- [2026-05-06 11:26:52 UTC] auto-orchestrator tick
- [2026-05-06 11:46:52 UTC] auto-orchestrator tick
- [2026-05-06 12:06:52 UTC] auto-orchestrator tick
- [2026-05-06 12:26:52 UTC] auto-orchestrator tick

## Not
- Canlı akışı terminalde izlemek için: `tmux -f /exec-daemon/tmux.portal.conf attach -t live-dashboard`
- Zengin panel: `AGENT-HUB/DASHBOARD.html`
