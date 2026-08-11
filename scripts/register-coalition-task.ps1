$ErrorActionPreference = "Stop"

$repoPath = "C:\Users\kacma\Desktop\Ledajans-SourceCode"
if (-not (Test-Path $repoPath)) {
    $repoPath = Join-Path $env:USERPROFILE "Desktop\Ledajans-SourceCode"
}
if (-not (Test-Path $repoPath)) {
    Write-Error "Repo bulunamadi: $repoPath"
}

$logPath = Join-Path $repoPath "AGENT-HUB\coalition-task-log.txt"
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    $python = (Get-Command python3 -ErrorAction SilentlyContinue).Source
}
if (-not $python) {
    Write-Error "Python bulunamadi"
}

function New-CoalitionTask {
    param(
        [string]$Name,
        [string]$At,
        [string]$Phase
    )

    $command = @"
`$repoPath = '$repoPath'
`$logPath = '$logPath'
`$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
"[`$stamp] START $Name ($Phase)" | Out-File -FilePath `$logPath -Append -Encoding utf8
& '$python' "`$repoPath\scripts\run-coalition-cycle.py" --phase $Phase 2>&1 | Out-File -FilePath `$logPath -Append -Encoding utf8
"[`$stamp] END $Name" | Out-File -FilePath `$logPath -Append -Encoding utf8
"@

    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $encodedCommand"
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $At
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

    if (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false
    }
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
    Write-Output "Task olusturuldu: $Name @ $At"
}

New-CoalitionTask -Name "Ledajans-Coalition-Discover-0930" -At "09:30" -Phase "discover"
New-CoalitionTask -Name "Ledajans-Coalition-Apply-1300" -At "13:00" -Phase "apply-prep"
New-CoalitionTask -Name "Ledajans-Coalition-Close-1700" -At "17:00" -Phase "close"

# Telegram komut poll — 5 dakikada bir (onay/red/emir)
$pollName = "Ledajans-Telegram-Poll-5min"
$pollCmd = @"
`$repoPath = '$repoPath'
`$logPath = '$logPath'
`$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
"[`$stamp] START telegram poll" | Out-File -FilePath `$logPath -Append -Encoding utf8
& '$python' "`$repoPath\scripts\telegram_bot_poll.py" 2>&1 | Out-File -FilePath `$logPath -Append -Encoding utf8
"@
$pollEncoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($pollCmd))
$pollAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $pollEncoded"
$pollTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ([TimeSpan]::MaxValue)
$pollPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$pollSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
if (Get-ScheduledTask -TaskName $pollName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $pollName -Confirm:$false
}
Register-ScheduledTask -TaskName $pollName -Action $pollAction -Trigger $pollTrigger -Principal $pollPrincipal -Settings $pollSettings | Out-Null
Write-Output "Task olusturuldu: $pollName (5 dk)"

Write-Output "Koalisyon gorevleri kayitli. Log: $logPath"
