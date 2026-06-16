#requires -Version 5
<#
.SYNOPSIS
  Repoint machine-specific references after the coding root has moved
  (e.g. C:\Coding -> "C:\Coding Infra"). These do NOT travel with git, so a
  drive/folder move silently breaks the session bootstrap and scheduled tasks:
    1. User env vars : SIMON_STACK_DIR, SIMONK_PROJECT_DIR, SIMON_WIKI_DIR
    2. SimonK-* Scheduled Tasks whose -File target moved with the root

.DESCRIPTION
  The "current root" is derived from THIS script's own location:
    <root>\Harrness Eng\SimonK-stack\scripts\heal-coding-paths.ps1
  so it always heals toward wherever the repo now lives. Idempotent: a no-op
  once everything already points at the current root. install.sh calls it
  automatically on Windows; you can also run it by hand after a move.

  ASCII-only output. No admin required (only the current user's env + tasks).

.PARAMETER DryRun
  Report what WOULD change without modifying anything.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\heal-coding-paths.ps1
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\heal-coding-paths.ps1 -DryRun
#>
[CmdletBinding()]
param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
function Say($m){ Write-Host "[heal] $m" }
function NormPath($p){ if(-not $p){ return '' } ($p -replace '/','\').TrimEnd('\') }

# --- Derive the current coding root from this script's own location ---
$stackRoot  = Split-Path $PSScriptRoot -Parent   # ...\Harrness Eng\SimonK-stack
$harrness   = Split-Path $stackRoot   -Parent    # ...\Harrness Eng
$codingRoot = Split-Path $harrness    -Parent    # <root>  e.g. C:\Coding Infra
Say "coding root : $codingRoot"
Say "stack repo  : $stackRoot"
if($DryRun){ Say 'DRY RUN - nothing will be modified' }

$changes = 0

# ---- 1. User environment variables ----
$envWanted = [ordered]@{
  'SIMON_STACK_DIR'    = $stackRoot
  'SIMONK_PROJECT_DIR' = $codingRoot
  'SIMON_WIKI_DIR'     = (Join-Path $codingRoot 'obsidian\SimonKWiki')
}
foreach($name in $envWanted.Keys){
  $want = $envWanted[$name]
  $have = [Environment]::GetEnvironmentVariable($name,'User')
  if((NormPath $have) -eq (NormPath $want)){ Say "env $name OK"; continue }
  if(-not (Test-Path $want)){ Say "env $name -> target missing, SKIP ($want)"; continue }
  Say "env $name : '$have' -> '$want'"
  if(-not $DryRun){
    [Environment]::SetEnvironmentVariable($name,$want,'User')
    [Environment]::SetEnvironmentVariable($name,$want,'Process')   # so the current session sees it too
  }
  $changes++
}

# ---- 2. SimonK-* scheduled tasks ----
# Known tasks -> the .ps1 (relative to the coding root) they should run, routed
# through the windowless VBS launcher so the periodic runs never flash a console.
$vbs = Join-Path $codingRoot 'tools\run-hidden.vbs'
$taskMap = [ordered]@{
  'SimonK-MemoryGuard'      = 'tools\memory-guard.ps1'
  'SimonK-Wiki-Lint-Weekly' = 'obsidian\SimonKWiki\.simonk-cron\run-wiki-lint.ps1'
}
foreach($tn in $taskMap.Keys){
  $task = Get-ScheduledTask -TaskName $tn -ErrorAction SilentlyContinue
  if(-not $task){ continue }
  $ps1 = Join-Path $codingRoot $taskMap[$tn]
  if(-not (Test-Path $ps1)){ Say "task $tn -> target missing, SKIP ($ps1)"; continue }

  if(Test-Path $vbs){
    $wantExe = 'wscript.exe'
    $wantArg = '"{0}" "{1}"' -f $vbs, $ps1
  } else {
    $wantExe = 'powershell.exe'
    $wantArg = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $ps1
  }

  $cur = $task.Actions[0]
  if((NormPath $cur.Execute) -eq (NormPath $wantExe) -and ("$($cur.Arguments)").Trim() -eq $wantArg){
    Say "task $tn OK"; continue
  }
  Say "task $tn : -> $wantExe $wantArg"
  if(-not $DryRun){
    Set-ScheduledTask -TaskName $tn -Action (New-ScheduledTaskAction -Execute $wantExe -Argument $wantArg) | Out-Null
  }
  $changes++
}

# ---- 3. Warn about any OTHER SimonK task pointing at a now-missing file ----
Get-ScheduledTask | Where-Object { $_.TaskName -like 'SimonK*' -and -not $taskMap.Contains($_.TaskName) } | ForEach-Object {
  $a = ($_.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join ' '
  foreach($m in [regex]::Matches($a, '[A-Za-z]:\\[^"]*\.ps1')){
    if(-not (Test-Path $m.Value)){ Say "WARN task $($_.TaskName) references missing $($m.Value) (not auto-healed)" }
  }
}

Say ("done - {0} change(s){1}" -f $changes, $(if($DryRun){' (dry run)'}else{''}))
exit 0
