# Orchestrator Consolidated Report - 2026-05-06

## Toplanan Raporlar
- `2026-05-06-tech-seo.md`: Şablon hazır, bulgu bekleniyor.
- `2026-05-06-gsc.md`: Şablon hazır, dışlanan kümeler bekleniyor.
- `2026-05-06-content.md`: Şablon hazır, sayfa bazlı gap analizi bekleniyor.
- `2026-05-06-internal-link.md`: Şablon hazır, kaynak/hedef eşleşmeler bekleniyor.
- `2026-05-06-serp-watch.md`: Şablon hazır, baseline sıra verisi bekleniyor.

## Durum Özeti
- Operasyonel altyapı tamam.
- Analitik bulgular henüz raporlara işlenmedi.
- Öncelik sırası korunuyor: teknik hata > indekslenme > içerik güncelleme > yeni içerik.

## Sprint-1 Aksiyon Planı

### Aşama 1 (P0): Teknik + İndekslenme
1. `tech-seo / P-001`
   - Robots, canonical, noindex, sitemap ve 4xx/5xx kaynaklı crawl/index engellerini çıkar.
   - Her madde için dry-run sonucu yaz; canlı değişiklik öncesi etki/risk notu ekle.
2. `gsc / P-002`
   - Excluded URL kümelerini neden bazında grupla (Crawled - currently not indexed, Discovered - currently not indexed, Duplicate vb.).
   - Etki skoruna göre indeksleme kuyruğu üret.

### Aşama 2 (P1): Mevcut İçeriği Güçlendirme
3. `content / P-003`
   - "led ekran" + ticari alt sorgular için mevcut URL’lerde title/H1/intent uyuşmazlıklarını çıkar.
   - Yeni sayfa açmadan revizyon taslaklarını hazırla.
4. `internal-link / P-004`
   - Para sayfalara bağlanacak kaynak URL listesini çıkar.
   - Anchor dağılımını (exact/partial/branded) dengele ve link enjeksiyon planını ver.
5. `serp-watch / P-005`
   - Anahtar kelime seti için baseline sıra ve rakip fark tablosunu başlat.
   - Haftalık volatilite not formatını sabitle.

### Aşama 3 (P2): Koşullu Yeni İçerik
6. `content / P-006`
   - Yalnızca P-003 sonrası boş kalan intent kümeleri için topic cluster öner.

## Çıktı Kalite Eşiği (Go/No-Go)
- Her raporda zorunlu alanlar dolu değilse görev "Done" sayılmayacak.
- P0 görevler tamamlanmadan P1 uygulamaya alınmayacak.
- Riskli teknik değişikliklerde dry-run kaydı olmayan öneri uygulanmayacak.
