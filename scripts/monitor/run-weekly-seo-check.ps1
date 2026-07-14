# Haftalık SEO sıra koruma kontrolü — smoke + para sayfa audit
# Kullanım: powershell -File scripts/run-weekly-seo-check.ps1

$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root

Write-Host "`n=== 1) SEO Smoke Test ===" -ForegroundColor Cyan
powershell -File scripts/seo-smoke-test.ps1
$smokeExit = $LASTEXITCODE

Write-Host "`n=== 2) Para Sayfa Audit ===" -ForegroundColor Cyan
python AGENT-HUB/audit-money-pages.py
$auditExit = $LASTEXITCODE

Write-Host "`n=== 3) İç Link Audit ===" -ForegroundColor Cyan
python AGENT-HUB/audit-internal-links.py

Pop-Location
if ($smokeExit -ne 0) { exit $smokeExit }
exit 0
