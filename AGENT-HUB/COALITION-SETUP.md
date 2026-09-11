# Koalisyon Kurulum — Tek Seferlik

Otonom uygulama (`apply-with-gates`) için aşağıdaki adımları tamamlayın. Secret'ları repoya commit etmeyin.

## 1. WordPress Application Password

1. WP Admin → Kullanıcılar → Profilim → Uygulama Şifreleri → Yeni şifre
2. Repo kökünde `.env` oluşturun (`.gitignore`'da olmalı):

```env
WP_SITE_URL=https://ledajans.com
WP_USERNAME=your-wp-username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

Alternatif: Windows ortam değişkenleri `WP_SITE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`.

## 2. MCP (Cursor)

```powershell
copy .cursor\mcp.json.example .cursor\mcp.json
```

`.cursor/mcp.json` içinde (commit etmeyin):

- `LEDAJANS_WP_MCP_TOKEN` — WordPress MCP eklenti token
- `APIFY_TOKEN` — SERP scrape (opsiyonel)

Cursor → Settings → MCP → sunucuları doğrula.

## 3. Çalışma modu

[`STATE.md`](STATE.md) → `apply-with-gates` aktif. T1/T2 otomatik; T3 (robots/canonical/noindex) BLOCKER.

## 4. Zamanlama

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register-coalition-task.ps1
```

Görevler: 09:30 keşif, 13:00 uygulama, 17:00 kapanış (hafta içi).

## Doğrulama

```powershell
python scripts\run-coalition-cycle.py --phase discover
python deploy-to-wordpress.py --dry-run
```
