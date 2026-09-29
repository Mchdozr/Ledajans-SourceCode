# IA cleanup 2026-09-23

Canlı: ledajans.com. Staging yok.

## Uygulandı

- 11 çöp URL taslağa alındı. Canlı yanıt tek hop 301 → `https://ledajans.com/` (site 404 kuralı). Redirection eklentisindeki hub hedefleri (id 133–144) kayıtlı ama istekleri o eklenti cevaplamıyor (hits 0).
- noindex: Ankara, İzmir, otel, stadyum, `/en/colorlight-4/`, `/en/huidu-2/`, `/en/blog-2/` ve taslağa alınan kopyalar.
- `/led-ekran/` title: LED Ekran Modelleri | İç-Dış Mekan ve Kiralama | LEDAJANS. H1: LED Ekran Çözümleri.
- Fiyat title: LED Ekran Fiyatları 2026 | LEDAJANS. URL aynı. Blog path hâlâ tek hop 301.
- İstanbul, fuar, mağaza vitrin title Türkçe. Markalarımız title Türkçe; H1 hâlâ Our Brands.
- Rank Math Instant Indexing: 26 kanonik URL gönderildi (`success`).
- Redirection `preferred_domain=nowww` kaydedildi. `https://www` hâlâ 200.

## Bilerek yapılmadı

- www nginx 301, footer `twiter.com`, hreflang, portfolio sitemap (23 URL zaten 301), `/cozumler/`, toplu EN/DE noindex.

## Rollback

- Taslakları yayına al: post 648, 650, 654, 658, 670, 642, 640, 656, 662, 666; sayfa 848.
- Rank Math title yedekleri: `AGENT-HUB/_tmp-hero-frames/ia-backup/meta-*.json`
- noindex listesi: `AGENT-HUB/_tmp-hero-frames/ia-backup/noindex-ids.json`
- Redirect kayıtları: id 133–144
