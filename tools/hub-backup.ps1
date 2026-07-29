<#
.SYNOPSIS
  Hub off-machine backup - push committed history to the private remote (comm-hub).
  Answers audit P1 'single-disk SPOF, no remote backup'. Called by the HubBackup scheduled task.
.NOTES
  Backs up COMMITTED history only (uncommitted working-tree changes must be committed by
  each agent first). Remote is the first line of SPOF defense. No destructive ops (push only,
  never force). Source kept ASCII: scheduled tasks may launch this under powershell.exe 5.1,
  which reads BOM-less UTF-8 as cp949 and mojibakes non-ASCII literals.
  2026-07-04: added fetch + divergence guard - a plain push used to swallow non-fast-forward
  rejections into the log for days (restore-migration incident: 17 behind / 3 ahead, no alarm).
#>
[CmdletBinding()]
param([string]$Hub = "E:\Coding Infra\AI Infra\Communication")
$ErrorActionPreference = "Continue"
function Now { Get-Date -Format "yyyy-MM-dd '/' HH:mm:ss" }
$log = Join-Path $Hub "tools\hub-backup.log"
Set-Location $Hub

# No remote (moved clone etc.) -> log and exit
$hasRemote = (git remote 2>$null) -contains 'origin'
if (-not $hasRemote) {
  "[$(Now) KST] HubBackup SKIP: origin remote not configured (git remote add origin <private-url>)" | Add-Content $log
  return
}

# Divergence guard: fetch first, then compare. Push only when the remote is a strict
# ancestor (fast-forward). On divergence, log LOUD and leave reconciliation to Claude
# (fetch + merge, never force) - see hub-watchdog check #8 which alarms on pile-up.
git fetch origin 2>&1 | Out-Null
$counts = (git rev-list --left-right --count origin/master...master 2>$null) -split '\s+'
$behind = 0; $ahead = 0
if ($counts.Count -ge 2) { $behind = [int]$counts[0]; $ahead = [int]$counts[1] }

if ($ahead -eq 0) {
  "[$(Now) KST] HubBackup OK: nothing to push (ahead=0, behind=$behind)" | Add-Content $log
  return
}
if ($behind -gt 0) {
  "[$(Now) KST] HubBackup DIVERGED: master is ahead=$ahead behind=$behind vs origin - push would be rejected non-FF. Claude must reconcile (git fetch + git merge origin/master, NEVER force), then push. NOT pushing." | Add-Content $log
  return
}

$push = (git push origin master 2>&1 | Out-String).Trim()
$localHead  = (git rev-parse --short HEAD 2>$null)
$remoteHead = ((git ls-remote origin master 2>$null) -split '\s')[0]
$synced = $remoteHead -and ($remoteHead -like "$((git rev-parse HEAD))*")
"[$(Now) KST] HubBackup push (local=$localHead, ahead was $ahead, synced=$synced): $push" | Add-Content $log
