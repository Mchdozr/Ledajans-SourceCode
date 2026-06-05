# Rehber alt URL → kök URL (nginx yedek)

Sayfa WP'de **Üst sayfa: LED Ekran Rehberleri** (`/rehber/`) altındaysa canlı URL `/rehber/{slug}/` olur; repodaki linkler `/{slug}/` bekler → kök 404.

**Kalıcı çözüm (tercih):** WP → Sayfalar → ilgili sayfa → **Üst sayfa: Yok**  
veya: `python scripts/fix-rehber-flat-permalinks.py --apply`

**Hızlı yedek (Plesk nginx):** her slug için 301:

```nginx
rewrite ^/fuar-led-ekran/?$ /rehber/fuar-led-ekran/ permanent;
rewrite ^/havaalani-led-ekran/?$ /rehber/havaalani-led-ekran/ permanent;
rewrite ^/otel-led-ekran/?$ /rehber/otel-led-ekran/ permanent;
rewrite ^/billboard-led-ekran/?$ /rehber/billboard-led-ekran/ permanent;
rewrite ^/toplanti-odasi-led-ekran/?$ /rehber/toplanti-odasi-led-ekran/ permanent;
```

Kök URL istiyorsanız nginx'de hedefi `/rehber/...` değil, üst sayfayı kaldırın (yukarıdaki script).
