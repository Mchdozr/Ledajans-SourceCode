# LEDAJANS teknik SEO smoke test — günlük veya deploy öncesi çalıştırın.
# Kullanım: powershell -File scripts/seo-smoke-test.ps1

$ErrorActionPreference = "Continue"
$failed = 0

function Test-Url {
    param([string]$Url, [int[]]$ExpectStatus = @(200), [string]$Label)
    $label = if ($Label) { $Label } else { $Url }
    try {
        $r = curl.exe -sS -o NUL -w "%{http_code}" -L --max-redirs 5 $Url
        $code = [int]$r
        if ($ExpectStatus -contains $code) {
            Write-Host "[OK] $label -> HTTP $code" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $label -> HTTP $code (beklenen: $($ExpectStatus -join ','))" -ForegroundColor Red
            $script:failed++
        }
    } catch {
        Write-Host "[FAIL] $label -> $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
    }
}

function Test-Redirect {
    param([string]$Url, [string]$ExpectFinal)
    $out = curl.exe -sS -I -L --max-redirs 5 -w "FINAL:%{url_effective}" $Url 2>&1 | Out-String
    if ($out -match "FINAL:(.+)$") {
        $final = $Matches[1].Trim()
        if ($final -eq $ExpectFinal) {
            Write-Host "[OK] $Url -> $final" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $Url -> $final (beklenen: $ExpectFinal)" -ForegroundColor Red
            $script:failed++
        }
    }
}

Write-Host "`n=== LEDAJANS SEO Smoke Test ===" -ForegroundColor Cyan
Write-Host (Get-Date -Format "yyyy-MM-dd HH:mm:ss") "`n"

Test-Url "https://ledajans.com/robots.txt"
Test-Url "https://ledajans.com/sitemap.xml"
Test-Url "https://ledajans.com/sitemap_index.xml"

Test-Redirect "https://www.ledajans.com/" "https://ledajans.com/"
Test-Redirect "http://ledajans.com/" "https://ledajans.com/"

$moneyPages = @(
    "/",
    "/led-ekran/",
    "/ic-mekan-led-ekran/",
    "/dis-mekan-led-ekran/",
    "/rental-ekran/",
    "/cob-ekran/",
    "/projeler/"
)
foreach ($path in $moneyPages) {
    Test-Url "https://ledajans.com$path"
}

Test-Redirect "https://ledajans.com/dis-mekan-led-ekran" "https://ledajans.com/dis-mekan-led-ekran/"

Write-Host "`n=== Deploy dry-run ===" -ForegroundColor Cyan
Push-Location (Split-Path $PSScriptRoot -Parent)
python deploy-to-wordpress.py --dry-run
if ($LASTEXITCODE -ne 0) { $failed++ }
Pop-Location

Write-Host "`n=== Sonuç ===" -ForegroundColor Cyan
if ($failed -eq 0) {
    Write-Host "Tüm kontroller geçti." -ForegroundColor Green
    exit 0
} else {
    Write-Host "$failed kontrol başarısız." -ForegroundColor Red
    exit 1
}
