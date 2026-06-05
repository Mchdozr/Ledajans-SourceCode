# GSC Export Checklist (P0)

Son güncelleme (otomatik canlı crawl): **2026-06-05 14:30 UTC**

> **Indexed** sütunu: canlı crawl + sitemap; kesin durum için GSC URL Inspection ile doğrula.

## İndirilecek raporlar

1. **Indexing → Pages** — reason dağılımı
2. **Indexing → Page indexing** — excluded URL listesi
3. **Performance → Search results** — query + page (export)
4. **Sitemaps** — submitted / indexed sayıları

## Para sayfa URL Inspection (canlı test)

| URL | Indexed | Canonical | Last crawl | Sitemap | Not |
|-----|---------|-----------|------------|---------|-----|
| https://ledajans.com/ | GSC doğrula | https://ledajans.com/ | canlı 2026-06-05 (Last-Modified: Fri, 05 Jun 2026 13:57:17 GMT) | evet | OK |
| https://ledajans.com/led-ekran/ | GSC doğrula | https://ledajans.com/led-ekran/ | canlı 2026-06-05 (Last-Modified: n/a) | evet | OK |
| https://ledajans.com/ic-mekan-led-ekran/ | GSC doğrula | https://ledajans.com/ic-mekan-led-ekran/ | canlı 2026-06-05 (Last-Modified: n/a) | evet | OK |
| https://ledajans.com/dis-mekan-led-ekran/ | GSC doğrula | https://ledajans.com/dis-mekan-led-ekran/ | canlı 2026-06-05 (Last-Modified: n/a) | evet | OK |
| https://ledajans.com/rental-ekran/ | GSC doğrula | https://ledajans.com/rental-ekran/ | canlı 2026-06-05 (Last-Modified: n/a) | evet | OK |
| https://ledajans.com/cob-ekran/ | GSC doğrula | https://ledajans.com/cob-ekran/ | canlı 2026-06-05 (Last-Modified: n/a) | evet | OK |

## Kabul kriteri

- Reason yüzdeleri toplamı %100 (GSC export sonrası)
- P0 para sayfalarında `Duplicate` / `Crawled - currently not indexed` için aksiyon owner atanmış
- Export tarihi ile `SERP-BASELINE.csv` aynı hafta içinde

## Ham veri

Dosya: `AGENT-HUB/audit-money-pages-2026-06-05.json`
