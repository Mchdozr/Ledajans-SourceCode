# Haftalık Blog Otomasyonu (Pazartesi 09:00)

## Amaç
Her Pazartesi saat **09:00** (Türkiye) bir SEO blog yazısı üret, WordPress’e **publish** et, git’e push et. Odak programı: **led ekran** 1. sırada.

## Kaynaklar
| Dosya | Rol |
|-------|-----|
| `.cursor/agents/blog-ajan.md` | Ajan talimatı |
| `Blog/keyword-queue.json` | Konu kuyruğu + published_slugs |
| `Blog/huidu-wf1-wf2-wf4-led-kontrol-karti.html` | CSS/HTML referans |
| `scripts/publish-blog-post.py` | WP REST publish + Rank Math |

## Agent talimatı (Cursor Automation prompt özeti)
1. Repo checkout: `Mchdozr/Ledajans-SourceCode` (master veya tanımlı branch)
2. `.cursor/agents/blog-ajan.md` + `Blog/keyword-queue.json` oku
3. Sıradaki `pending` topic’i seç; HTML üret (`Blog/<slug>.html`)
4. `python scripts/publish-blog-post.py Blog/<slug>.html --dry-run` sonra `--publish`
5. Queue güncelle, commit, push
6. Özet yaz: slug, link, KW

## Ortam
Cloud Agent’ta `.env` veya secret: `WP_USERNAME`, `WP_APP_PASSWORD`, `WP_SITE_URL=https://ledajans.com`

## Cron
`0 9 * * 1` — her Pazartesi 09:00 (kullanıcı yerel saati / editör timezone)
