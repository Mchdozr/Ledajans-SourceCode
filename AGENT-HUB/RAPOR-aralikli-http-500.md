# Risk-Guardian: Aralıklı HTTP 500 — ledajans.com

**Tarih:** 2026-08-13  
**Kapsam:** Report-only (canlı WP yazımı / deploy yok)  
**Risk seviyesi:** P1 (kesikli erişim; soft-404/500 maskeleme riski ile P0’a yaklaşabilir)  
**Karar:** Block canlı kod değişikliği | Allow hosting panel teşhisi + log inceleme

## Probe (salt okuma, 2026-08-13)

| URL | HTTP | TTFB | Not |
|-----|------|------|-----|
| `/` | 200 | ~1.76s | `Server: nginx`, `X-Powered-By: PHP/7.4.33, PleskLin` |
| `/?nocache=` | 200 | ~1.79s | HTML ~432 KiB |
| `/wp-json/` | 200 | ~1.38s | Cache-Control çakışmalı (`max-age=300` + `max-age=0`) |

Anlık 500 yakalanmadı; “1–2 yenilemede açılıyor” deseni sunucu kaynak / FPM / WAF ile uyumlu.

## Repo bağlamı

- **Stack notu:** nginx + PHP 7.4 (Plesk); LiteSpeed HTML cache yok (`REPORTS/2026-08-03-lcp-5step-loop.md`).
- **TTFB tavanı:** 0.5–1.6s bandı; kod tarafı LCP tavanı hosting/cache (`REPORTS/2026-08-03-mobile-perf-loop.md`).
- **mu-plugin:** `wordpress-mobil-hiz-patch.php` → canlı `mu-plugins/ledajans-perf-patch.php`; `ob_start` ile tam sayfa buffer (logo + GTM). Büyük HTML’de bellek baskısı mümkün; aralıklı 500’ün birincil nedeni olma ihtimali orta.
- **WAF:** REST Basic Auth → nginx 403 geçmişi (`scripts/WP-REST-403-FIX.md`, ModSecurity/Wordfence).
- **Maskeleme:** `/500` ve olmayan URL’ler ana sayfaya 301 — gerçek 5xx izlenmesi zor (`REPORTS/2026-05-06-tech-seo-agent.md`).
- **STATE:** apply-with-gates; T3/robots/canonical → BLOCKER; deploy öncesi dry-run + Telegram onayı.

## En olası 3 kök neden

1. **PHP-FPM worker tükenmesi / bellek (Plesk, PHP 7.4)** — eşzamanlı istek + ~430 KiB HTML + eklenti yığını → `pm.max_children` / `memory_limit` aşımı; sonraki istek boş worker bulunca açılır.
2. **ModSecurity / Wordfence / nginx WAF aralıklı engeli** — belirli UA, sorgu veya bot deseni; yenilemede farklı imza → 200.
3. **Önbellek yok / soğuk PHP + OPcache baskısı** — HTML cache fiilen yok (`max-age=0` çakışması); her istek PHP; spike’ta 500/timeout.

Diğer adaylar (düşük–orta): DB bağlantı limiti, mu-plugin `ob_start` + büyük sayfa, eklenti fatal (Elementor/Rank Math/güvenlik), disk dolu / inode.

## Aksiyon listesi (hosting — kod deploy yok)

1. **Plesk → Loglar → hata günlüğü** (domain + PHP-FPM): 500 anında `Allowed memory size`, `max_children`, `segfault`, `ModSecurity` satırlarını kopyala.
2. **Plesk → PHP ayarları:** `memory_limit` (en az 256M, tercihen 512M), `max_execution_time`, PHP sürümü notu (7.4 EOL).
3. **PHP-FPM:** `pm.status` / Domains → PHP settings → FPM pool: `max_children`, `start_servers`; “server reached pm.max_children” uyarısı var mı bak.
4. **Aynı anda İzleme:** CPU, RAM, MySQL bağlantı sayısı; 500 ile örtüşüyor mu.
5. **Wordfence / güvenlik eklentisi:** Live Traffic / Blocking — 5xx veya blocked istek; geçici Learning Mode veya kural gevşetme (kalıcı değil).
6. **ModSecurity (Plesk WAF):** domain için son hit’ler; şüphede geçici Off → tekrar üret → On (kök neden testi).
7. **Önbellek:** LiteSpeed Cache / WP Rocket / nginx FastCGI microcache durumu; Cache-Control çakışmasını hosting’e ilet (kod deploy değil).
8. **Eklenti izolasyonu:** staging veya bakım penceresinde güvenlik + cache dışı eklentileri tek tek kapatıp 500 sıklığını ölç (önce Wordfence/benzeri).
9. **mu-plugin geçici mitigation:** yalnızca onaylı bakımda `ledajans-perf-patch.php` yeniden adlandırıp 15 dk izle; düzelirse buffer/bellek hipotezi güçlenir — **repo’dan canlı yazma / `install-mobile-perf-plugin.py` çalıştırma**.
10. **wp-content/debug.log:** `WP_DEBUG_LOG` kısa süreli aç (display_errors kapalı); fatal sınıfı yakala, sonra kapat.
11. **Soft-404/500 maskesini kaldırma:** özel 500 sayfası + gerçek status — ayrı T3/onay işi; teşhis için şart.
12. **Kapı hatırlatması:** canlı içerik/patch için yalnızca `python3 deploy-to-wordpress.py --dry-run` → kullanıcı onayı → sonra canlı; robots/canonical/noindex yasak; secret commit yok.

## Güvenli alternatif (repo)

- Bu dosya + panel logları yeterli; kod patch veya WP REST yazımı önerme.
- Dry-run / Telegram `/onay` olmadan `coalition-apply` / `write-files` / canlı widget deploy **Block**.

## Handoff

- Hosting sahibi: maddeler 1–7  
- wordpress-deploy: beklet (onay yok)  
- performance: TTFB/cache notları doğrulandı; 500 kökü hosting  
- tech-seo: 5xx → ana sayfa 301 maskesi ayrı backlog  
