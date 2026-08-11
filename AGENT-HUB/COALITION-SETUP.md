# Koalisyon Kurulum — Tek Seferlik

Secret'ları repoya commit etmeyin.

## 1. WordPress Application Password

```env
WP_SITE_URL=https://ledajans.com
WP_USERNAME=your-wp-username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

WP Admin → Kullanıcılar → Profil → Uygulama Şifreleri.

## 2. MCP (opsiyonel)

Apify SERP için `.cursor/mcp.json` (gitignored):

```json
{
  "mcpServers": {
    "apify": {
      "url": "https://mcp.apify.com",
      "headers": { "Authorization": "Bearer apify_api_XXXX" }
    }
  }
}
```

WP MCP eklentisi zorunlu değil; REST + `.env` yeter.

## 3. Mod

`STATE.md` → `apply-with-gates` (T1/T2 otomatik; T3 BLOCKER).

## 4. Zamanlama

```bash
# Cloud / Linux: cron veya Cursor Cloud Agent 09:30 / 13:00 / 17:00 TR
python3 scripts/run-coalition-cycle.py --phase discover
python3 scripts/coalition-apply.py --dry-run
python3 scripts/coalition-apply.py

# Windows:
powershell -ExecutionPolicy Bypass -File scripts/register-coalition-task.ps1
```

## Doğrulama

```bash
python3 scripts/check-wp-env.py
python3 scripts/run-coalition-cycle.py --phase discover
python3 deploy-to-wordpress.py --dry-run
```
