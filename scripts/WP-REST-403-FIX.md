# WordPress REST API nginx 403

## Belirti

- `python scripts/check-wp-env.py` → `http_status=403`, HTML `nginx Forbidden`
- `https://ledajans.com/wp-json/` tarayıcıda veya kimliksiz istekte **200** olabilir
- **Uygulama şifresi** ile (`Authorization: Basic ...`) istekte **403**

Bu, şifredeki `#` veya `(` karakterlerinden değil; sunucu/WAF’ın kimlikli REST isteğini kesmesidir.

## Yapılacaklar (sırayla)

### 1) Wordfence (varsa)

- **Security → Settings → WordPress REST API**
- “Allow REST API” / oturum açmış kullanıcı için izin açık olsun
- **Firewall → Blocking** → son engellenen isteklerde `wp-json` var mı bakın
- Gerekirse deploy IP’nizi allowlist’e ekleyin

### 2) Hosting paneli (ModSecurity / WAF)

Destek talebi metni:

> `/wp-json/` uç noktasına WordPress **Application Password** (HTTP Basic Auth) ile erişim 403 dönüyor. Kimliksiz GET 200, `Authorization` başlıklı istek nginx 403. Lütfen REST API ve Application Passwords için kural istisnası ekleyin.

### 3) nginx (sunucu erişiminiz varsa)

`limit_req` veya `deny` kurallarında `/wp-json/` ve `Authorization` header’ı kontrol edin.

### 4) Uygulama şifresini yenileyin

`.env` repoda veya sohbette göründüyse: WP Admin → Uygulama Şifreleri → eskiyi sil → yeni oluştur → `.env` güncelle.

## REST açılınca deploy

```powershell
python scripts/check-wp-env.py
# http_status=200

python deploy-to-wordpress.py --blog-only
python deploy-to-wordpress.py --blog-only --publish
```

Mevcut yazılar **slug** ile bulunup güncellenir (üzerine yazar).

## REST açılamazsa (geçici)

1. WP Admin → Yazılar → ilgili yazı → **Kod düzenleyici**
2. Repo `Blog/*-rehber.html` içeriğini yapıştır (zaten `ledajans-seo-article` sarmalı)
3. Önbellek temizle
