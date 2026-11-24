# Canlı site yedeği — 24.11.2026

Giriş gerektirmeyen, herkese açık yedek. Üretmek için: `python3 scripts/backup-public-site.py --out YEDEK/<tarih>`

| Dosya | İçerik |
|---|---|
| `html.tar.gz` | Sitemap'teki 286 URL'nin canlı HTML'i (TR, EN, DE). Açmak için: `tar -xzf html.tar.gz` |
| `rest.tar.gz` | REST API `context=view`: pages, posts, media, categories (başlık, içerik, slug, tarih) |
| `meta.csv` | Her URL için title, açıklama, robots, canonical, H1, og:image, kelime sayısı |
| `sitemaps/`, `robots.txt`, `llms.txt` | O günkü halleri |
| `yonlendirmeler.csv` | Bilinen eski adreslerin o günkü yönlendirme hedefi |

**Bu yedekte olmayanlar:** Elementor ham verisi (son hali `CANLI-SITE/`, 30.09.2026; yenilemek için WordPress uygulama şifresi gerekir), Rank Math ayarları, veritabanı ve görsel dosyaları. Canlıya herhangi bir değişiklik almadan önce hosting panelinden tam veritabanı ve dosya yedeği alınmalıdır.
