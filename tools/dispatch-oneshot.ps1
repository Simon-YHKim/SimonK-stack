# dispatch-oneshot.ps1 -- Urgent-order helper: file a request, commit it, run the target
# lane ONCE (one-shot), and wait for the response file. Born from the 2026-07-03 4ai
# roundtrip test: one-shot grok answered in 87s while codex waited 6m14s for its cadence.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools/dispatch-oneshot.ps1 -To codex -Slug ui-check -BodyFile C:\path\body.md
#   powershell -ExecutionPolicy Bypass -File tools/dispatch-oneshot.ps1 -To grok -Slug live-signal -BodyFile body.md -TimeoutMin 10
#
# BodyFile = md fragment placed under '## Ask' (Korean OK; read as UTF-8 no-BOM).
# If the standing lane daemon is running (mutex held) we do NOT double-spawn -- the
# standing daemon picks the order up on its next cycle instead.
# ASCII-only source (PS 5.1 no-BOM safe).
param(
  [Parameter(Mandatory=$true)][ValidateSet('codex','grok','antigravity')][string]$To,
  [Parameter(Mandatory=$true)][string]$Slug,
  [Parameter(Mandatory=$true)][string]$BodyFile,
  [int]$TimeoutMin = 15,
  [string]$Priority = 'high'
)
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if (-not (Test-Path -LiteralPath $BodyFile)) { Write-Host "[dispatch] BodyFile not found: $BodyFile" -ForegroundColor Red; exit 1 }
$body = [System.IO.File]::ReadAllText($BodyFile, $utf8)
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$createdTs = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$id = "$ts-claude-to-$To-$Slug"
$rel = "agents/claude/outbox/$ts-to-$To-$Slug.md"

$md = @"
---
id: $id
from: claude
to: $To
type: request
ref: ""
project: hub
priority: $Priority
status: open
created: $createdTs KST
---

## Context
dispatch-oneshot urgent order (bypasses the 10-min cadence).

## Ask
$body

## Acceptance
- Response md in your outbox with the FULL 9-key frontmatter contract (ref: $id).
- Identity commit via tools/commit.ps1 -As $To (no orphan files).
"@
[System.IO.File]::WriteAllText((Join-Path $root $rel), $md, $utf8)

& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'commit.ps1') -As claude -Message "feat(comm): oneshot dispatch to $To - $Slug" -Files $rel
if ($LASTEXITCODE -ne 0) { Write-Host "[dispatch] commit failed - aborting (order file left in working tree)" -ForegroundColor Red; exit 1 }
Write-Host "[dispatch] order committed: $rel" -ForegroundColor Green
$t0 = Get-Date

# One-shot spawn unless the standing lane daemon holds the mutex.
# 2026-07-04: ALSO probe the 'default' lane mutex - a daemon launched without -Only
# holds Global\hubdaemon_default while cycling every default-lane seat; probing only
# hubdaemon_$To would double-spawn a second concurrent worker into the shared tree
# (the index.lock race the sequential design exists to avoid).
try {
  $free = $false
  $m = New-Object System.Threading.Mutex($false, "Global\hubdaemon_$To")
  try { $free = $m.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $free = $true }
  if ($free) {
    [void]$m.ReleaseMutex()
    $defaultLanes = @('codex')   # keep in sync with hub-daemon.ps1 default AI set
    if ($defaultLanes -contains $To) {
      $md = New-Object System.Threading.Mutex($false, "Global\hubdaemon_default")
      $dfree = $false
      try { $dfree = $md.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $dfree = $true }
      if ($dfree) { [void]$md.ReleaseMutex() } else { $free = $false }
      $md.Dispose()
    }
  }
  if ($free) {
    Start-Process powershell -ArgumentList '-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'hub-daemon.ps1'),'-Only',$To,'-MaxCycles','1' -WindowStyle Hidden
    Write-Host "[dispatch] one-shot lane spawned (-Only $To -MaxCycles 1)" -ForegroundColor Green
  } else {
    Write-Host "[dispatch] standing $To daemon is running - it picks the order up on its next cycle (<=10min); not double-spawning" -ForegroundColor Yellow
  }
  $m.Dispose()
} catch { Write-Host "[dispatch] mutex check failed: $($_.Exception.Message) - not spawning; the standing daemon (or watchdog) will handle it" -ForegroundColor Yellow }

# Wait for a response that references our id (slug as fallback).
$deadline = (Get-Date).AddMinutes($TimeoutMin)
$obx = Join-Path $root "agents\$To\outbox"
while ((Get-Date) -lt $deadline) {
  $hit = Get-ChildItem $obx -Filter *.md -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt $t0 } |
    Where-Object { try { $c = [System.IO.File]::ReadAllText($_.FullName, $utf8); ($c -match [regex]::Escape($id)) -or ($c -match [regex]::Escape($Slug)) } catch { $false } } |
    Select-Object -First 1
  if ($hit) {
    $secs = [int]((Get-Date) - $t0).TotalSeconds
    Write-Host "[dispatch] RESPONSE in ${secs}s: agents/$To/outbox/$($hit.Name)" -ForegroundColor Green
    exit 0
  }
  Start-Sleep -Seconds 20
}
Write-Host "[dispatch] TIMEOUT after ${TimeoutMin}min - no response yet. Check tools/live/$To.log and tools/hub-daemon.log" -ForegroundColor Yellow
exit 2
