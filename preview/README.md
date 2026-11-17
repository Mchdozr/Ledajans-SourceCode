# Yerel önizleme — bozuk görsel yenileme

Canlı ledajans.com sayfalarını, sunucuda bozuk/eksik olan 31 görselin **yeni** halleriyle gösterir. Canlıya hiçbir şey yazmaz.

## Çalıştırma (Node.js 18+)

```bash
node preview/server.mjs
```

Tarayıcıda: http://localhost:8090/__ (sayfa listesi) · http://localhost:8090/__onizleme (önce/sonra)

- Port değiştirmek için: `PORT=9000 node preview/server.mjs` (Windows PowerShell: `$env:PORT=9000; node preview/server.mjs`)
- Mobil banner WebP'lerini görmek için dar pencere/mobil emülasyon ya da adrese `?mobil=1`.
- Durdurmak: Ctrl+C

## Dosyalar

- `assets/replacements/wp-content/uploads/...` — 31 görsel; canlıda **aynı yola** konacak (aynı ad + format, içerik/URL değişmez).
- `assets/replacements/mobile-hero/` — 8 ürün banner'ının mobil 960px WebP'si (yamaya eklenecek; ayrı onay).
- `assets/replacements/LISANS.md` — Adobe Stock kaynakları.
