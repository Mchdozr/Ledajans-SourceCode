# Rental Ekran URL Taşıma — Güvenli 301

## Sorun

Google'da `rental ekran` aramasında eski URL görünüyor:

- Eski: `https://ledajans.com/case/rental-ekran/`
- Hedef: `https://ledajans.com/rental-ekran/`

Canlı kontrol:

- `/rental-ekran/` → `200`, canonical kendisi
- `/case/rental-ekran/` → `404`

Bu durumda sıralamadaki eski URL boşa düşüyor. En güvenli çözüm eski URL'yi **tek adımlı 301** ile hedef sayfaya taşımaktır.

## Plesk nginx kuralı

Plesk → **Websites & Domains** → `ledajans.com` → **Apache & nginx Settings** → **Additional nginx directives**

En üste şu satırı ekleyin:

```nginx
rewrite ^/case/rental-ekran/?$ /rental-ekran/ permanent;
```

Sonra:

1. Apply / OK
2. W3TC / cache eklentisi: Empty all caches
3. Kontrol:

```powershell
python scripts/inspect-rental-canonical.py
```

Beklenen:

```text
https://ledajans.com/case/rental-ekran/ -> 301 -> https://ledajans.com/rental-ekran/
https://ledajans.com/rental-ekran/ -> 200
```

## SEO notu

- `noindex` veya canonical tek başına yeterli değil; eski URL 404 olduğu için sinyal aktarmaz.
- 301 sonrası Google eski sonucu zamanla `/rental-ekran/` olarak değiştirir.
- Sıralama dalgalanması olabilir ama 404'te bırakmaktan daha güvenlidir.
- 301'i en az 12 ay, tercihen kalıcı tutun.
