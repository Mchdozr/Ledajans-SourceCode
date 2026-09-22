# Haftalık Blog Otomasyonu (Pazartesi 09:00 — 2 yazı)

## Amaç
Her Pazartesi **09:00** (Europe/Istanbul) **2** SEO blog yazısı üret, görsel ekle, WordPress’e **publish** et, git’e push et.

Yapı örneği: https://ledajans.com/huidu-c08l-controller/  
Ajan: `.cursor/agents/haftalik-blog-yayin.md` (+ `blog-ajan.md`)

## Kaynaklar
| Dosya | Rol |
|-------|-----|
| `.cursor/agents/haftalik-blog-yayin.md` | 2 yazı / görsel / canlı publish |
| `Blog/keyword-queue.json` | Konu kuyruğu |
| `Blog/yayinlanan-basliklar.md` | Başlık/slug/odak tekrarı yok |
| `Blog/_ornek-huidu-c08l-controller.html` | C08L iskelet |
| `Blog/huidu-wf1-wf2-wf4-led-kontrol-karti.html` | CSS |
| `scripts/select-weekly-blog-topics.py` | 2 unique pending |
| `scripts/publish-blog-post.py` | WP REST + Rank Math |

## Cursor Cloud Automation prompt

```
Repo: Ledajans-SourceCode (master)
Oku: .cursor/agents/haftalik-blog-yayin.md
Çalıştır: python scripts/select-weekly-blog-topics.py
Seçilen 2 topic için C08L yapısında HTML + görsel üret.
Dry-run sonra python scripts/publish-blog-post.py Blog/<slug>.html --publish
Queue + yayinlanan-basliklar güncelle, commit, push.
Onay sorma. Aynı slug/başlık/odak yasak.
```

Cron: `0 9 * * 1` — Europe/Istanbul  
Secret: `WP_USERNAME`, `WP_APP_PASSWORD`, `WP_SITE_URL=https://ledajans.com`

## Manuel
```
python scripts/select-weekly-blog-topics.py
python scripts/publish-blog-post.py Blog/<slug>.html --dry-run
python scripts/publish-blog-post.py Blog/<slug>.html --publish
```
