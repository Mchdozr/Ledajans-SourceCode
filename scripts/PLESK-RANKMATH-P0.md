# P0 RankMath — canliya alma

## Sorun
WP REST, `rank_math_*` alanlarini sayfalarda kayitli degilse **sessizce yok sayar** (HTTP 200 ama meta yazilmaz).

## Cozum A — mu-plugin guncelle (onerilen)

1. Plesk Dosya Yoneticisi: `wp-content/mu-plugins/ledajans-perf-patch.php`
2. Repodaki `wordpress-mobil-hiz-patch.php` iceriginin **tamamini** yapistirin (sonunda Rank Math REST blogu var).
3. Lokal:
   ```powershell
   python scripts/set-rankmath-p0-meta.py --apply
   python scripts/verify-rankmath-p0-meta.py
   ```

## Cozum B — WP-CLI (SSH)

```bash
cd /var/www/vhosts/ledajans.com/httpdocs
bash scripts/set-rankmath-p0-wpcli.sh
```

## Cozum C — Rank Math kutusu (manuel)

`AGENT-HUB/RANKMATH-P0-APPLY-2026-06-05.md` tablosundan 4 sayfaya yapistirin.
