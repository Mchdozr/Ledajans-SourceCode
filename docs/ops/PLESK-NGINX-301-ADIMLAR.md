# Plesk — blog 301 (Rank Math CSV olmadan)

## Onceden

- `.htaccess` blog blogu: **silin** (islemiyor)
- `include ... ledajans-blog-301.conf`: **silin**
- Rank Math tek kural: kalabilir (nginx calisinca cift olmaz, isterseniz silin)

---

## Adim A — Tek satir test (nginx)

1. Plesk → **Websites & Domains** → **ledajans.com**
2. **Apache & nginx Settings** / **Apache ve nginx Ayarlari**
3. **Additional nginx directives** (domain / sunucu blogu — **httpd.conf degil**)
4. Once sadece su satiri yapistirin:

```nginx
rewrite ^/led-ekran-nasil-secilir-rehber/?$ /blog/led-ekran-nasil-secilir-rehber/ permanent;
```

5. **OK** / Apply — hata cikmazsa devam
6. W3TC → Empty all caches + LiteSpeed Purge
7. Gizli pencere: `https://ledajans.com/led-ekran-nasil-secilir-rehber/` → **301** olmali

---

## Adim B — 103 kural (test OK ise)

1. Ayni kutuya `scripts/plesk-nginx-blog-301-paste.conf` **tum** rewrite satirlarini ekleyin  
   (yorum satirlari opsiyonel; 103 `rewrite` satiri sart)
2. **OK** / Apply
3. Onbellek tekrar temizle

Dosya yolu: `Ledajans-SourceCode/scripts/plesk-nginx-blog-301-paste.conf`

---

## Adim C — W3TC 404 onbellegi (hala 404 ise)

FTP/Dosya Yoneticisi:

`httpdocs/wp-content/cache/page_enhanced/ledajans.com/led-ekran-nasil-secilir-rehber/`

klasorunu silin (varsa). Sonra W3TC Empty all caches.

---

## Adim D — Apache yedek (nginx yetmezse)

**Additional Apache directives** kutusuna `.htaccess` blog 301 blokundaki `RewriteRule` satirlarini yapistirin.

---

## Hata: nginx config test failed

- Kutudaki metni geri alin
- Sadece Adim A tek satir ile deneyin
- `location / { }` sarmalayici **kullanmayin** (cakisma)

---

## Kontrol

| URL | Beklenen |
|-----|----------|
| `/blog/led-ekran-nasil-secilir-rehber/` | 200 |
| `/led-ekran-nasil-secilir-rehber/` | 301 → blog |
