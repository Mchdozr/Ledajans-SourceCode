$ErrorActionPreference = "Stop"

$taskName = "Ledajans-Weekday-GitPull-1715"
$command = @'
$repoPath = "C:\Users\kacma\OneDrive\Masa" + [char]0x00FC + "st" + [char]0x00FC + "\Ledajans-SourceCode"
if (-not (Test-Path $repoPath)) { exit 1 }
$logPath = Join-Path $repoPath "AGENT-HUB\git-pull-log.txt"
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$stamp] START git pull" | Out-File -FilePath $logPath -Append -Encoding utf8
git -C $repoPath pull --ff-only origin master 2>&1 | Out-File -FilePath $logPath -Append -Encoding utf8
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$stamp] END git pull" | Out-File -FilePath $logPath -Append -Encoding utf8
'@

$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $encodedCommand"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 17:15
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Write-Output "Task olusturuldu: $taskName"
