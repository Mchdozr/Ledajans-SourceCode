# EN/DE i18n runbook

Canlı WordPress Uygulama Şifresi gerekir. Cloud secret `WP_USERNAME` GitHub kullanıcısına map edilmiş; `WP_SITE_URL` Plesk `:8880/admin`. Scriptler her zaman `https://ledajans.com` kullanır.

```bash
# .env (commit etme)
WP_SITE_URL=https://ledajans.com
WP_USERNAME=ledajans
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

python3 scripts/ledajans_i18n.py
python3 scripts/i18n-clone-translate.py --generate-chrome --no-mt
python3 scripts/restore-polylang-langs.py
python3 scripts/install-gsc-coverage-mu.py
# File Manager yedek: wp-content/mu-plugins/ledajans-gsc-coverage.php
python3 scripts/i18n-clone-translate.py --pilot --menus --templates --inject-chrome --no-mt
python3 scripts/qa-i18n-live.py
# onay sonrası
python3 scripts/i18n-clone-translate.py --batch --menus --inject-chrome
```

TR `Anasayfa/Hero.html` dokunulmaz. Eski boş EN/DE taslaklar yayına alınmaz.
