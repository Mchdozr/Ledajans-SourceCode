$ErrorActionPreference = "Stop"

$repoPath = "C:\Users\kacma\OneDrive\Masaüstü\Ledajans-SourceCode"
$logPath = Join-Path $repoPath "AGENT-HUB\git-pull-log.txt"

if (-not (Test-Path $repoPath)) {
    throw "Repo bulunamadi: $repoPath"
}

Set-Location $repoPath

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$timestamp] START git pull" | Out-File -FilePath $logPath -Append -Encoding utf8

git pull --ff-only origin master 2>&1 | Out-File -FilePath $logPath -Append -Encoding utf8

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$timestamp] END git pull" | Out-File -FilePath $logPath -Append -Encoding utf8
