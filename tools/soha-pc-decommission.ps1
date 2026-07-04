<#
.SYNOPSIS
  SOHA PC (old C:-drive hub machine) decommission script. Simon directive 2026-07-04:
  "비활성화 하고 legacy 접미사 + legacy 처리".
.DESCRIPTION
  RUN THIS ON THE SOHA PC (user Soha.Bae), NOT on the E: machine.
  The live hub machine is E: (DESKTOP-Q02Q4FG / 202502) as of 2026-07-04 - if the SOHA
  PC ever runs hub lanes / HubBackup again, both machines write the same comm-hub master
  and the history FORKS (this exact split-brain happened 07-04: 17 behind / 3 ahead).
  What this script does (all reversible - rename + disable only, NO deletion):
    1. Disables every Hub* / SimonK* scheduled task.
    2. Kills running hub-daemon / hub-watchdog processes.
    3. Renames "C:\Coding Infra" -> "C:\Coding Infra-Legacy-20260704" (and C:\2ndB alike)
       so nothing auto-resolves the old paths.
    4. Drops a LEGACY marker file explaining where the live hub lives.
  ASCII-only source (safe under powershell.exe 5.1 cp949 read).
#>
[CmdletBinding()]
param([switch]$DryRun)
$ErrorActionPreference = 'Continue'
function Say([string]$m){ Write-Host "[soha-decomm] $m" }

if ($env:COMPUTERNAME -eq 'DESKTOP-Q02Q4FG') {
  Say "ABORT: this is the LIVE E: hub machine, not the SOHA PC. Run this on the old C:-drive machine only."
  exit 1
}

# 1. disable scheduled tasks
$tasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like 'Hub*' -or $_.TaskName -like 'SimonK*' }
foreach ($t in $tasks) {
  Say "disable task: $($t.TaskName) (state=$($t.State))"
  if (-not $DryRun) { try { $t | Disable-ScheduledTask | Out-Null } catch { Say "  failed: $($_.Exception.Message)" } }
}

# 2. kill hub daemon/watchdog processes
Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'hub-daemon|hub-watchdog|orders-poll' } |
  ForEach-Object {
    Say "kill PID $($_.ProcessId): $($_.CommandLine.Substring(0,[Math]::Min(90,$_.CommandLine.Length)))"
    if (-not $DryRun) { try { Stop-Process -Id $_.ProcessId -Force } catch {} }
  }

# 3. legacy-rename the old roots (rename = reversible, nothing deleted)
foreach ($root in @('C:\Coding Infra','C:\2ndB')) {
  if (Test-Path $root) {
    $legacy = "$root-Legacy-20260704"
    Say "rename: $root -> $legacy"
    if (-not $DryRun) { try { Move-Item -LiteralPath $root -Destination $legacy -ErrorAction Stop } catch { Say "  failed (open handles? close editors/terminals and retry): $($_.Exception.Message)" } }
  } else { Say "not present: $root" }
}

# 4. marker
$marker = @"
LEGACY MACHINE - HUB DECOMMISSIONED 2026-07-04 (Simon directive)
The live AI hub + 2nd-B workspace moved to the E: machine (DESKTOP-Q02Q4FG / user 202502).
Do NOT re-enable Hub*/SimonK* scheduled tasks or run hub-daemon here - it would fork the
shared comm-hub master (split-brain guard: hub CONTROL.md broadcast 2026-07-04).
Everything from this machine was migrated via H:\backup_SimonK_260703 (now *-Legacy) and
merged into comm-hub master (commit ac22ae9e).
"@
if (-not $DryRun) { try { [System.IO.File]::WriteAllText('C:\HUB-LEGACY-README.txt', $marker) } catch {} }
Say "done. (DryRun=$DryRun)"
