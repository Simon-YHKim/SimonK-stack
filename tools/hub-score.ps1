# hub-score.ps1 -- measured-loop scoreboard for the hub (audit H3, + F1 runaway sensor).
# ASCII-only source. READ-ONLY (appends only to a gitignored score ledger).
#
# WHY: PROTOCOL 12.1a "measured loop" (baseline -> one change -> re-measure -> keep only on
# gain/no-regression) was doctrine-only for the hub, executed by hand. This makes it EXECUTABLE:
# it composes the read-only collectors (hub-events cycles/err/timeout/p95, hub-insight novelty/
# degenerate/wasted) + git (ahead-of-origin backup health, commit volume) + CONTROL.state into
# ONE score record, appends it to Output/scores.jsonl, and DIFFS against the previous record to
# flag REGRESSIONS (more timeouts/errors, a new degenerate lane, novelty drop, backup falling
# behind). It also carries a cycles/day RUNAWAY sensor (audit F1) -- a dormant volume tripwire that
# would surface an abnormal spawn spike (the closest flat-rate-subscription proxy for cost governance;
# no metered path exists today, so this warns rather than auto-pausing).
#
#   powershell -ExecutionPolicy Bypass -File tools/hub-score.ps1              # measure + diff vs last, console
#   powershell -ExecutionPolicy Bypass -File tools/hub-score.ps1 -Days 3
#   powershell -ExecutionPolicy Bypass -File tools/hub-score.ps1 -Json
#   powershell -ExecutionPolicy Bypass -File tools/hub-score.ps1 -RunawayCyclesPerDay 400
param([int]$Days = 7, [int]$RunawayCyclesPerDay = 500, [switch]$Json)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent
$ledger = Join-Path $root 'Output\scores.jsonl'

function Invoke-Json([string]$script, [hashtable]$params) {
  try { $out = (& (Join-Path $PSScriptRoot $script) @params) | Out-String; if ($out.Trim()) { return ($out | ConvertFrom-Json) } } catch {}
  return $null
}
function Read-Lines([string]$p) { if (-not (Test-Path $p)) { return @() }; return @(Get-Content $p -Encoding UTF8 | Where-Object { $_ -and $_.Trim() }) }

# ---- collect metrics ----
$ev = Invoke-Json 'hub-events.ps1'  @{ Json = $true; Days = $Days }
$ins = Invoke-Json 'hub-insight.ps1' @{ Json = $true; Days = $Days }

$cyclesTotal = 0; $errTotal = 0; $timeoutTotal = 0
if ($ev) { foreach ($l in $ev.lanes) { $cyclesTotal += [int]$l.Cycles; $errTotal += [int]$l.Err; $timeoutTotal += [int]$l.Timeout } }
$degenerateLanes = 0; $wastedTotal = 0; $minNovelty = 100
if ($ins) { foreach ($l in $ins.lanes) { if ([bool]$l.Degenerate) { $degenerateLanes++ }; $wastedTotal += [int]$l.Wasted; if ($l.Commits -gt 0 -and [int]$l.NoveltyPct -lt $minNovelty) { $minNovelty = [int]$l.NoveltyPct } } }

$controlState = '?'
$cf = Join-Path $root 'CONTROL.md'
if (Test-Path $cf) { foreach ($l in (Get-Content $cf -Encoding UTF8 -TotalCount 8)) { if ($l -match '^state:\s*"?(\w+)') { $controlState = $Matches[1] } } }

$ahead = 0
try { $a = git -C $root rev-list --count origin/master..master 2>$null; if ($a -match '^\d+$') { $ahead = [int]$a } } catch {}
$commits24h = 0
try { $c = git -C $root rev-list --count --since='24 hours ago' HEAD 2>$null; if ($c -match '^\d+$') { $commits24h = [int]$c } } catch {}
$cyclesPerDay = if ($Days -gt 0) { [math]::Round($cyclesTotal / $Days, 0) } else { $cyclesTotal }

$rec = [ordered]@{
  ts = (Get-Date -Format 's'); windowDays = $Days; controlState = $controlState
  cyclesTotal = $cyclesTotal; errTotal = $errTotal; timeoutTotal = $timeoutTotal
  degenerateLanes = $degenerateLanes; minNoveltyPct = $minNovelty; wastedTotal = $wastedTotal
  aheadOfOrigin = $ahead; commits24h = $commits24h; cyclesPerDay = $cyclesPerDay
}

# ---- diff vs previous record ----
$prev = $null
$hist = Read-Lines $ledger
if ($hist.Count -gt 0) { try { $prev = $hist[-1] | ConvertFrom-Json } catch {} }

$regressions = @()
$improvements = @()
if ($prev) {
  if ($rec.timeoutTotal   -gt $prev.timeoutTotal)   { $regressions  += "timeouts $($prev.timeoutTotal)->$($rec.timeoutTotal)" } elseif ($rec.timeoutTotal -lt $prev.timeoutTotal) { $improvements += "timeouts $($prev.timeoutTotal)->$($rec.timeoutTotal)" }
  if ($rec.errTotal       -gt $prev.errTotal)       { $regressions  += "errors $($prev.errTotal)->$($rec.errTotal)" } elseif ($rec.errTotal -lt $prev.errTotal) { $improvements += "errors $($prev.errTotal)->$($rec.errTotal)" }
  if ($rec.degenerateLanes -gt $prev.degenerateLanes){ $regressions  += "degenerate lanes $($prev.degenerateLanes)->$($rec.degenerateLanes)" } elseif ($rec.degenerateLanes -lt $prev.degenerateLanes) { $improvements += "degenerate lanes $($prev.degenerateLanes)->$($rec.degenerateLanes)" }
  if ($rec.minNoveltyPct  -lt $prev.minNoveltyPct)  { $regressions  += "min novelty $($prev.minNoveltyPct)%->$($rec.minNoveltyPct)%" } elseif ($rec.minNoveltyPct -gt $prev.minNoveltyPct) { $improvements += "min novelty $($prev.minNoveltyPct)%->$($rec.minNoveltyPct)%" }
  if ($rec.aheadOfOrigin  -gt 15 -and $rec.aheadOfOrigin -gt $prev.aheadOfOrigin) { $regressions += "ahead-of-origin $($rec.aheadOfOrigin) (backup falling behind)" }
}

# ---- F1 runaway sensor ----
$runaway = ($cyclesPerDay -gt $RunawayCyclesPerDay)

# ---- append ledger ----
try {
  $outDir = Join-Path $root 'Output'; if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
  [System.IO.File]::AppendAllText($ledger, (($rec | ConvertTo-Json -Compress) + "`n"), $utf8)
} catch {}

if ($Json) {
  [pscustomobject]@{ record = $rec; regressions = @($regressions); improvements = @($improvements); runaway = $runaway } | ConvertTo-Json -Depth 5
  return
}

# ---- console ----
Write-Host ""
Write-Host ("=" * 84) -ForegroundColor Cyan
Write-Host ("  AI HUB SCORE   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') KST   window=${Days}d   (measured loop, PROTOCOL 12.1a)") -ForegroundColor Cyan
Write-Host ("=" * 84) -ForegroundColor Cyan
Write-Host ("  run-state       : {0}" -f $controlState)
Write-Host ("  cycles/err/to   : {0} / {1} / {2}" -f $rec.cyclesTotal, $rec.errTotal, $rec.timeoutTotal) -ForegroundColor $(if ($rec.timeoutTotal -gt 0 -or $rec.errTotal -gt 0) { 'Yellow' } else { 'Gray' })
Write-Host ("  degenerate lanes: {0}   min novelty: {1}%   wasted commits: {2}" -f $rec.degenerateLanes, $rec.minNoveltyPct, $rec.wastedTotal) -ForegroundColor $(if ($rec.degenerateLanes -gt 0) { 'Red' } else { 'Gray' })
Write-Host ("  backup (ahead)  : {0}   commits/24h: {1}   cycles/day: {2}" -f $rec.aheadOfOrigin, $rec.commits24h, $rec.cyclesPerDay) -ForegroundColor $(if ($rec.aheadOfOrigin -gt 15) { 'Yellow' } else { 'Gray' })
Write-Host ("-" * 84) -ForegroundColor DarkGray
if (-not $prev) {
  Write-Host "  first score recorded -- no previous baseline to diff (re-run after a change to measure)." -ForegroundColor DarkGray
} else {
  if ($regressions.Count -gt 0) { Write-Host ("  !! REGRESSIONS vs last: " + ($regressions -join ' , ')) -ForegroundColor Red }
  if ($improvements.Count -gt 0) { Write-Host ("  ++ improvements vs last: " + ($improvements -join ' , ')) -ForegroundColor Green }
  if ($regressions.Count -eq 0 -and $improvements.Count -eq 0) { Write-Host "  no change vs last score." -ForegroundColor DarkGray }
}
if ($runaway) { Write-Host ("  !! RUNAWAY sensor (F1): cycles/day $cyclesPerDay > $RunawayCyclesPerDay -- abnormal spawn volume; investigate before it burns pool/cost.") -ForegroundColor Red }
Write-Host ("  ledger: $ledger  ($($hist.Count + 1) records)") -ForegroundColor DarkGray
