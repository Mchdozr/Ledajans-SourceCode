# Üç KW cluster canlı apply — 2026-08-20

**Karar: GO** (içerik + REST publish). **301: NO-GO** (Rank Math REST 404, 0/16).
**Onay:** kullanıcı açık onay — `scripts/deploy-uc-kw-cluster.py --apply`
**GOB ana menü:** eklenmedi.

## Dry-run (apply öncesi)

| Kontrol | Sonuç |
|---------|--------|
| auth | 200 |
| widget MAP | 18/18 |
| miss | 0 |
| NO-GO widget | yok |

## Canlı apply

Komut: `$env:PYTHONIOENCODING='utf-8'; python scripts/deploy-uc-kw-cluster.py --apply`  
Exit: **0**

### Widget POST (18/18 success=true, HTTP 200)

| Page ID | Slug | Widget | Dosya |
|---------|------|--------|--------|
| 6004 | /ic-mekan-led-ekran/ | 7f03109 | hero-banner.html |
| 6004 | /ic-mekan-led-ekran/ | d1061de | ic-mekan-led-ekran-text.html |
| 6004 | /ic-mekan-led-ekran/ | 2b6c17d | urun-ozellikleri.html |
| 6004 | /ic-mekan-led-ekran/ | 848614d | sss.html |
| 6012 | /dis-mekan-led-ekran/ | 3f7d957 | hero-banner.html |
| 6012 | /dis-mekan-led-ekran/ | 7b76b791 | dis-mekan-led-ekran-text.html |
| 6012 | /dis-mekan-led-ekran/ | 677eee5 | urun-ozellikleri.html |
| 6012 | /dis-mekan-led-ekran/ | de132a7 | ofc-serisi-outdoor.html |
| 6012 | /dis-mekan-led-ekran/ | 538c2a3 | sss.html |
| 1248 | / (anasayfa) | 48f4925 | widget-3.html |
| 1248 | / | 8f08265 | widget-4-Ic-Mekan.html |
| 1248 | / | 3618c5f | widget-5-Dis-Mekan.html |
| 1248 | / | 39bcdae | widget-6-Urunlerimiz-Slider.html |
| 1248 | / | 0118cbd | widget-7-projeler.html |
| 5557 | /led-ekran/ | 25a1bb2 | led-ekran.html |
| 6026 | /ic-mekan-rgb-panel/ | 8f766f3 | ic-mekan-icin-rgb-panel-text.html |
| 6026 | /ic-mekan-rgb-panel/ | 992082e | tablo-ic-mekan-rgb-gob-led-paneller.html |
| 786 | /program-indir/ | 25682f9 | hero-banner.html |

### REST publish

| Slug | HTTP | ID | Not |
|------|------|----|-----|
| gob-led-ekran | 201 | 8094 | yeni sayfa, publish |
| gob-vs-cob-smd | 201 | 8095 | yeni sayfa, publish |
| gob-led-nedir | 200 | 7512 | draft → publish |
| cob-led-ne-zaman | 200 | 7503 | draft → publish |
| gob-led-ekran-ne-zaman-tercih-edilir | 201 | 8098 | yeni post (blog) |

### RankMath P1 meta (`set-rankmath-p1-meta.py --apply`)

GOB slug’ları canlıda vardı → apply çalıştı. **5/5 OK.**

| Slug | ID |
|------|-----|
| magaza-vitrin-led-ekran | 7446 |
| istanbul-led-ekran | 7513 |
| gob-led-ekran | 8094 |
| gob-led-nedir | 7512 |
| gob-vs-cob-smd | 8095 |

### 301 (Rank Math REST + canlı HEAD)

Endpoint `POST /wp-json/rankmath/v1/redirections` → **404**. `rankmath 301 ok=0/16` (bu apply turunda yazılmadı).

Canlıda zaten doğru 301: `/case/ic-mekan-led-ekran/`, `/case/dis-mekan-led-ekran/`, `/case/rental-ekran/`.

Yanlış hedef (blog’a gidiyor, para sayfaya değil): `/dis-mekan-led-ekranlar/` → `/blog/dis-mekan-led-ekranlar/`; `/led-ekran-2/` → `/blog/led-ekran-2/`; `/led-2/` → `/blog/led-2/`.

Hâlâ 404 (CSV hedefi para/SKU): `/case/kontrol-kartlari/`, `/case/ic-mekan-rgb-panel/`, `/urunler/ic-mekan-led-ekran/`, `/urunler/dis-mekan-led-ekran/`, `/sozluk/gob-led-nedir/`, `/led-ekran-9/`, 4 GOB SKU kısa slug.

Manuel kalan: Rank Math UI import (`AGENT-HUB/cluster-301-rankmath.csv`) **veya** Plesk nginx (`scripts/plesk-nginx-cluster-301-paste.conf`).

## Canlı HTTP doğrulama (HEAD no-follow + GET follow)

| URL | HEAD | GET | İçerik |
|-----|------|-----|--------|
| https://ledajans.com/ic-mekan-led-ekran/ | 200 | 200 | IP31 var, İç Mekan LED Ekran var, Fansız SMPS var |
| https://ledajans.com/dis-mekan-led-ekran/ | 200 | 200 | Dış Mekan LED Ekran var, IP65 var |
| https://ledajans.com/gob-led-ekran/ | 200 | 200 | GOB LED var |
| https://ledajans.com/gob-led-nedir/ | 200 | 200 | 404 değil |
| https://ledajans.com/gob-vs-cob-smd/ | 200 | 200 | — |
| https://ledajans.com/blog/gob-led-ekran-ne-zaman-tercih-edilir/ | 200 | 200 | — |
| https://ledajans.com/cob-led-ne-zaman/ | 200 | 200 | (ekstra, REST publish) |

## Hatalar

- Widget/REST: yok
- Rank Math 301 REST: 16/16 skip (404) — yönlendirmeler canlıya yazılmadı
- LiteSpeed purge: apply script `ledajans/v1/purge` çağırdı

## Rollback

- Elementor widget: WP/Elementor revision veya önceki HTML ile `POST /wp-json/ledajans/v1/hero-widget` (page_id + widget_id)
- REST sayfalar: WP revision — 8094, 8095, 7512, 7503, 8098
- Yeni GOB sayfaları tamamen geri almak için trash: 8094, 8095, 8098; 7512 ve 7503 draft’a çek
- Rank Math meta: P1 script öncesi değer veya Rank Math UI
- 301: uygulanmadı, rollback gerekmez

## Sonraki (manuel)

1. Rank Math / nginx 301 (16 kural)
2. GSC URL Inspection: kanonik iç/dış + yeni GOB URL’ler
3. GOB menüye ekleme **yapılmadı** (istek)
