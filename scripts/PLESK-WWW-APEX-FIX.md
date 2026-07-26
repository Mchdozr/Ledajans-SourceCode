# www.ledajans.com → https://ledajans.com (acil DNS + SSL)

## Teşhis (2026-07-26)

| Kontrol | Sonuç |
|--------|--------|
| `ledajans.com` A | `194.36.84.221` — çalışıyor |
| `www.ledajans.com` A/CNAME | **yok** (`NXDOMAIN`) — tarayıcı açılmaz |
| SSL SAN | yalnızca `DNS:ledajans.com` — `www` yok |
| Sunucu (Host: www → IP) | **zaten 301** → `https://ledajans.com/` |
| NS | `ns1.natrohost.com` / `ns2.natrohost.com` |

Kanonik host: **apex** (`https://ledajans.com`). `www` yalnızca 301 ile apex’e gitmeli.

Repodan DNS/SSL paneline yazılamaz; aşağıdaki adımlar Natro / Plesk’te uygulanır.

---

## Adım 1 — DNS: `www` kaydı ekle (zorunlu)

### Tercih A — Plesk DNS (hosting Natro Plesk ise)

1. Plesk → **Websites & Domains** → **ledajans.com**
2. **DNS Settings** / **DNS Ayarları**
3. Kayıt ekle:

| Type | Host / Name | Value |
|------|-------------|--------|
| **A** | `www` | `194.36.84.221` |

veya

| Type | Host / Name | Value |
|------|-------------|--------|
| **CNAME** | `www` | `ledajans.com.` |

4. **Apply** / **Update**

### Tercih B — Natro müşteri paneli

1. [Natro Müşteri Paneli](https://www.natro.com/) → giriş
2. **Alan Adı Yönetimi** → `ledajans.com` → **DNS Kayıt Yönetimi**
3. Aynı A veya CNAME kaydını ekle, kaydet

Doğrulama (birkaç dakika sonra):

```bash
dig +short www.ledajans.com A
# beklenen: 194.36.84.221  (CNAME kullanıldıysa önce CNAME, sonra A)
```

---

## Adım 2 — Plesk: www alias + Let’s Encrypt (zorunlu)

DNS yayıldıktan hemen sonra:

1. Plesk → **ledajans.com** → **Hosting Settings**
2. **Preferred domain**: `ledajans.com` (www’siz) — www → apex yönlendirme açık olsun
3. Domain alias / www dahil olduğundan emin ol (`www.ledajans.com` siteye bağlı)
4. **SSL/TLS Certificates** → **Let’s Encrypt**
5. **www.ledajans.com** kutusunu işaretle → **Get / Renew**
6. Sertifikada SAN listesinde hem `ledajans.com` hem `www.ledajans.com` olmalı

---

## Adım 3 — Nginx yedek (gerekirse)

Sunucu zaten 301 veriyor. Preferred domain kapalıysa veya 301 kaybolursa:

**Apache & nginx Settings** → **Additional nginx directives** — `scripts/plesk-nginx-www-to-apex.conf` içeriğini ekle → Apply.

WP yedek: `wordpress-mobil-hiz-patch.php` içinde `www` → apex 301 var (mu-plugin / tema sonuna ekliyse).

---

## Adım 4 — Doğrulama

```bash
python3 scripts/check-www-host.py
```

Beklenen:

- DNS: `www` → `194.36.84.221` (veya CNAME zinciri)
- `http://www.ledajans.com/` → **301** → `https://ledajans.com/...`
- `https://www.ledajans.com/` → **301** → `https://ledajans.com/...` (tek hop, sertifika geçerli)
- Apex `https://ledajans.com/` → **200**

GSC: hem `https://ledajans.com` hem `https://www.ledajans.com` property varsa apex’i birincil bırakın; www trafiği 301 ile birleşir.
