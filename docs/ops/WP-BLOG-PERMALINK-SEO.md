# Blog URL `/blog/` gecisi — SEO ve terminal

## Simdiki durum (canli)

- Yazilar: `https://ledajans.com/{slug}/` (kok)
- Repo ic linkler: `https://ledajans.com/blog/{slug}/`
- Bu uyumsuzluk: ic linkler 404 veya karisik sinyal uretebilir.

## SEO: geriye duser miyiz?

| Senaryo | Risk |
|---------|------|
| Sadece permalink degistir, **301 yok** | Yuksek — eski URL 404, sira kaybi |
| Permalink + **301** eski -> yeni | Dusuk — 1-3 hafta dalgalanma normal |
| Hic dokunma, repo `/blog/` linkleri | Orta — kirilan linkler / tutarsiz canonical |

**Oneri:** `/blog/%postname%/` + her eski kok URL icin 301. Uzun vadede repo ve GSC ile uyumlu.

## Terminal (REST — bu repo)

```powershell
# 1) Rapor
python scripts/wp-permalink-audit.py

# 2) 301 listesi (RankMath icin)
python scripts/set-blog-permalink.py --redirects-csv blog-301.csv

# 3) Permalink uygula (yonetici sifresi .env)
python scripts/set-blog-permalink.py --apply

# 4) RankMath > Redirects > blog-301.csv import (veya tek tek 301)
# 5) LiteSpeed onbellek temizle
```

## Sunucuda WP-CLI (varsa, daha guvenilir flush)

```bash
wp option update permalink_structure '/blog/%postname%/' --path=/var/www/vhosts/ledajans.com/httpdocs
wp rewrite flush --path=...
```

## RankMath olmadan

- Redirection eklentisi CSV import
- veya `.htaccess` / nginx `return 301` kurallari (hosting)

## Yayinlanmis yazilar

Mevcut 5 rehber zaten `publish` — degisiklikten once **GSC URL Denetimi** ile hangi URL'nin dizinde oldugunu not alin; 301 sonrasi "Dizine eklenmesini iste" yeni URL icin.
