# WordPress Uygulama Şifresi — Acil Rotate

Repoda düz metin şifre bulundu. **Hemen yapın:**

1. WP Admin → Kullanıcılar → Profilim → Uygulama Şifreleri
2. Eski "Deploy Script" (veya sızdırılmış) şifreyi **Sil**
3. Yeni şifre oluştur → kopyala
4. Repo kökünde `.env` oluştur (`.env.example` şablonu):

```env
WP_SITE_URL=https://ledajans.com
WP_USERNAME=ledajans
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

1. Doğrula: `python deploy-to-wordpress.py --dry-run`

`.env` asla commit edilmez (`.gitignore`).