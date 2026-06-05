# Nginx blog URL kurulumu (ledajans.com)

## Dosyalar

| Dosya | Ne zaman |
|-------|----------|
| `scripts/blog-nginx-301-only.conf` | WP kalici baglanti `/blog/%postname%/` **kaydedildikten sonra** (onerilen) |
| `scripts/blog-nginx-rules.conf` | Permalink henuz kokteyse (301 + gecici ic rewrite) |

## 1) Dosyayi sunucuya yukleyin

Ornek (Plesk / SSH):

```bash
# Yerel PC'den (PowerShell):
scp "C:\Users\kacma\Desktop\Ledajans-SourceCode\scripts\blog-nginx-301-only.conf" `
  root@SUNUCU:/var/www/vhosts/ledajans.com/conf/ledajans-blog-301.conf
```

Veya Plesk Dosya Yoneticisi ile ayni yola yukleyin.

## 2) Plesk — nginx include

1. **Websites & Domains** → **ledajans.com**
2. **Apache & nginx Settings** (Apache ve nginx Ayarlari)
3. **Additional nginx directives** (Ek nginx direktifleri) — **domain** kutusuna:

```nginx
include /var/www/vhosts/ledajans.com/conf/ledajans-blog-301.conf;
```

4. **OK** / Apply → **nginx reload** (Plesk genelde otomatik yapar)

## 3) WordPress kalici baglanti (ayni gun)

WP Admin → **Ayarlar → Kalici baglantilar** → Ozel:

```
/blog/%postname%/
```

→ **Kaydet**

## 4) Test

```text
https://ledajans.com/led-ekran-nasil-secilir-rehber/
  → 301 → https://ledajans.com/blog/led-ekran-nasil-secilir-rehber/  (200)

https://ledajans.com/blog/  → 200 (liste)
```

LiteSpeed Cache: **Purging All**

## Sorun

- **500 nginx error:** include yolu yanlis veya `rewrite` server blogunda — Plesk destek include'u `location /` icine tasir.
- **Sayfa 404 ama 301 calisiyor:** Kalici baglanti kaydedilmemis; `blog-nginx-rules.conf` (full) gecici veya permalink Kaydet.
- **Cift yonlendirme:** Rank Math 301 + nginx 301 ikisi birden acik olmasin; birini secin.

## Rank Math

Nginx kullaniyorsaniz Rank Math'te ayni 103 kurali **import etmeyin** (cift 301).
