# hub-events.ps1 -- structured per-cycle TRACE for the 4-AI hub (OTel-GenAI flavored).
# ASCII-only source (PS 5.1 no-BOM safe). READ-ONLY w.r.t. the running hub.
#
# WHY (2026-07-11 audit, obs B1/B2/B3): the only execution record is the prose
# hub-daemon.log, which every tool reverse-engineers with regex. There is no durable
# per-cycle structure, so (a) hub-usage.ps1 is arithmetically BLIND to TIMEOUT cycles
# (they never emit an "exit(" line) -> a lane timing out every cycle reads as idle;
# (b) cycle latency is derivable from BEGIN/END but never derived; (c) a killed/no-op
# cycle is indistinguishable from a shipped one. This tool parses the daemon log into
# ONE JSON line per cycle at tools/trace/events.jsonl using OpenTelemetry GenAI
# semantic-convention keys, then reports per-lane cycles / outcome-breakdown (incl.
# TIMEOUT + incomplete) / latency p50-p95-max. It is the substrate the dashboard and a
# future budget/eval layer read from. The daemon can later append the same schema live;
# until then -Backfill reconstructs full history from the existing log.
#
# Usage (cwd = hub root):
#   powershell -ExecutionPolicy Bypass -File tools/hub-events.ps1                 # backfill + console stats (7d)
#   powershell -ExecutionPolicy Bypass -File tools/hub-events.ps1 -Days 2
#   powershell -ExecutionPolicy Bypass -File tools/hub-events.ps1 -Backfill       # rebuild events.jsonl only
#   powershell -ExecutionPolicy Bypass -File tools/hub-events.ps1 -Json
#   powershell -ExecutionPolicy Bypass -File tools/hub-events.ps1 -Html
param(
  [int]$Days = 7,
  [switch]$Backfill,   # rebuild events.jsonl and exit (no stats)
  [switch]$NoBackfill, # use existing events.jsonl as-is
  [switch]$Json,
  [switch]$Html
)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent
$dlog = Join-Path $PSScriptRoot 'hub-daemon.log'
$traceDir = Join-Path $PSScriptRoot 'trace'
$events = Join-Path $traceDir 'events.jsonl'

function Read-SharedLog([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return @() }
  for ($i = 0; $i -lt 4; $i++) {
    try {
      $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
      try { $sr = New-Object System.IO.StreamReader($fs, [System.Text.UTF8Encoding]::new($false)); $text = $sr.ReadToEnd(); $sr.Close() }
      finally { $fs.Close() }
      return @($text -split "`r?`n")
    } catch { Start-Sleep -Milliseconds 60 }
  }
  return @()
}

function Parse-Kst([string]$s) {
  $t = ($s -replace 'KST', '').Trim()
  try { return [datetime]::Parse($t) } catch { return $null }
}

function Emit-Event($tbl, $endTs, $outcome) {
  # build one OTel-GenAI-flavored event object from an open-cycle table
  $durMs = $null
  if ($tbl.tb -and $endTs) { $durMs = [int]((New-TimeSpan -Start $tbl.tb -End $endTs).TotalMilliseconds) }
  return [pscustomobject][ordered]@{
    'ts'                     = if ($tbl.tb) { $tbl.tb.ToString('s') } else { '' }
    'gen_ai.agent.name'      = $tbl.ai
    'gen_ai.operation.name'  = 'cycle'
    'cycle'                  = $tbl.cyc
    'gen_ai.request.model'   = $tbl.model
    'tier'                   = $tbl.tier
    'cycle.exit_code'        = $tbl.code
    'outcome'                = $outcome
    'latency_ms'             = $durMs
    'quota'                  = [bool]$tbl.quota
    'timeout'                = ($outcome -eq 'timeout')
  }
}

# ---------- BACKFILL: hub-daemon.log -> events.jsonl ----------
if (-not $NoBackfill) {
  $lines = Read-SharedLog $dlog
  $open = @{}      # ai -> open-cycle table
  $evList = New-Object System.Collections.ArrayList
  foreach ($ln in $lines) {
    # [ai] bracket is optional: TIMEOUT lines are logged as "[ts KST] cycle TIMEOUT(ai)..."
    # with NO [ai] prefix, so a required second bracket would silently drop every timeout.
    if ($ln -notmatch '^\[(?<ts>[^\]]+) KST\]\s*(?:\[(?<ai>[^\]]+)\]\s*)?(?<msg>.*)$') { continue }
    $ts = Parse-Kst $Matches['ts']; $ai = $Matches['ai']; $msg = $Matches['msg']
    # TIMEOUT first: it is logged with NO [ai] prefix, so $ai may be null here -- resolve the
    # lane from TIMEOUT(<ai>) instead of the (absent) bracket.
    if ($msg -match 'cycle\s+TIMEOUT\((\w+)\)') {
      $ta = $Matches[1]
      if ($ta -and $open.ContainsKey($ta)) { [void]$evList.Add((Emit-Event $open[$ta] $ts 'timeout')); $open.Remove($ta) }
      else { [void]$evList.Add((Emit-Event @{ ai = $ta; cyc = $null; tb = $ts; model = ''; tier = ''; code = $null; quota = $false } $ts 'timeout')) }
    }
    elseif (-not $ai) { continue }   # BEGIN/exit/END all carry the [ai] prefix; a bracket-less non-timeout line is not a cycle event
    elseif ($msg -match '^cycle\s+(\d+)\s+BEGIN') {
      if ($open.ContainsKey($ai)) { [void]$evList.Add((Emit-Event $open[$ai] $null 'incomplete')) }  # prior cycle never closed (daemon killed mid-cycle)
      $open[$ai] = @{ ai = $ai; cyc = [int]$Matches[1]; tb = $ts; model = ''; tier = ''; code = $null; quota = $false }
    }
    elseif ($msg -match 'cycle\s+exit\((?<a>\w+)(?:/(?<rest>[^)]*))?\)=(?<code>-?\d+)\s*(?<tag>\w+)?') {
      if ($open.ContainsKey($ai)) {
        $open[$ai].code = [int]$Matches['code']
        if ($Matches['rest'] -and $Matches['rest'] -match '^(?<tier>[^=]+)=(?<model>.+)$') { $open[$ai].tier = $Matches['tier']; $open[$ai].model = $Matches['model'] }
        if ($Matches['tag'] -match 'QUOTA') { $open[$ai].quota = $true }
      }
    }
    elseif ($msg -match '^cycle\s+(\d+)\s+END') {
      if ($open.ContainsKey($ai)) {
        $t = $open[$ai]
        $outcome = if ($t.quota) { 'quota' } elseif ($null -eq $t.code) { 'noop' } elseif ($t.code -eq 0) { 'ok' } else { 'err' }
        [void]$evList.Add((Emit-Event $t $ts $outcome)); $open.Remove($ai)
      }
    }
  }
  # any still-open cycles = in-flight now; leave them out (not yet closed)
  if (-not (Test-Path $traceDir)) { New-Item -ItemType Directory -Path $traceDir -Force | Out-Null }
  $sb = New-Object System.Text.StringBuilder
  foreach ($e in $evList) { [void]$sb.AppendLine(($e | ConvertTo-Json -Compress)) }
  [System.IO.File]::WriteAllText($events, $sb.ToString(), $utf8)
  if ($Backfill) { Write-Host ("[hub-events] backfilled " + $evList.Count + " cycle events -> " + $events) -ForegroundColor Green; return }
}

# ---------- STATS from events.jsonl ----------
if (-not (Test-Path $events)) { Write-Host "[hub-events] no events.jsonl (run with -Backfill first)" -ForegroundColor Yellow; return }
$all = @()
foreach ($ln in (Read-SharedLog $events)) { if ($ln.Trim()) { try { $all += ($ln | ConvertFrom-Json) } catch {} } }
$cut = (Get-Date).AddDays(-$Days)
$win = @($all | Where-Object { $_.ts -and ([datetime]::Parse($_.ts) -ge $cut) })

function Pctl([double[]]$vals, [double]$p) {
  if ($vals.Count -eq 0) { return $null }
  $s = @($vals | Sort-Object)
  $idx = [int][math]::Ceiling($p / 100.0 * $s.Count) - 1
  if ($idx -lt 0) { $idx = 0 }; if ($idx -ge $s.Count) { $idx = $s.Count - 1 }
  return [math]::Round($s[$idx] / 1000.0, 1)   # ms -> s
}

$ais = @('claude', 'codex', 'antigravity', 'grok')
$rows = @()
foreach ($ai in $ais) {
  $ev = @($win | Where-Object { $_.'gen_ai.agent.name' -eq $ai })
  $tot = $ev.Count
  $ok = @($ev | Where-Object { $_.outcome -eq 'ok' }).Count
  $err = @($ev | Where-Object { $_.outcome -eq 'err' }).Count
  $to = @($ev | Where-Object { $_.outcome -eq 'timeout' }).Count
  $q = @($ev | Where-Object { $_.outcome -eq 'quota' }).Count
  $inc = @($ev | Where-Object { $_.outcome -eq 'incomplete' }).Count
  $durs = @($ev | Where-Object { $_.latency_ms -ne $null -and $_.outcome -ne 'incomplete' } | ForEach-Object { [double]$_.latency_ms })
  $rows += [pscustomobject]@{
    AI = $ai; Cycles = $tot; OK = $ok; Err = $err; Timeout = $to; Quota = $q; Incomplete = $inc
    p50s = (Pctl $durs 50); p95s = (Pctl $durs 95); maxs = $(if ($durs.Count) { [math]::Round(($durs | Measure-Object -Maximum).Maximum / 1000.0, 1) } else { $null })
  }
}

if ($Json) {
  [pscustomobject]@{ generated = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); windowDays = $Days; totalEvents = $all.Count; lanes = $rows } | ConvertTo-Json -Depth 5
  return
}

# Console
Write-Host ""
Write-Host ("=" * 92) -ForegroundColor Cyan
Write-Host ("  AI HUB EVENTS -- per-cycle trace   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') KST   window=${Days}d   ($($all.Count) events total)") -ForegroundColor Cyan
Write-Host ("=" * 92) -ForegroundColor Cyan
Write-Host ("{0,-12}{1,-8}{2,-6}{3,-6}{4,-9}{5,-7}{6,-6}{7,-8}{8,-8}{9}" -f 'AI', 'cycles', 'OK', 'Err', 'TIMEOUT', 'Quota', 'Inc', 'p50 s', 'p95 s', 'max s') -ForegroundColor White
foreach ($r in $rows) {
  $col = if ($r.Timeout -gt 0 -or $r.Err -gt 0) { 'Red' } elseif ($r.Cycles -eq 0) { 'DarkGray' } else { 'Gray' }
  Write-Host ("{0,-12}{1,-8}{2,-6}{3,-6}{4,-9}{5,-7}{6,-6}{7,-8}{8,-8}{9}" -f `
      $r.AI, $r.Cycles, $r.OK, $r.Err, $r.Timeout, $r.Quota, $r.Incomplete, `
    $(if ($null -ne $r.p50s) { $r.p50s } else { '-' }), $(if ($null -ne $r.p95s) { $r.p95s } else { '-' }), $(if ($null -ne $r.maxs) { $r.maxs } else { '-' })) -ForegroundColor $col
}
Write-Host ("-" * 92) -ForegroundColor DarkGray
$toTotal = ($rows | Measure-Object -Property Timeout -Sum).Sum
if ($toTotal -gt 0) {
  Write-Host ("!! " + $toTotal + " TIMEOUT cycles in ${Days}d -- these are INVISIBLE to hub-usage.ps1 (no exit line). Check tools/live/<ai>.log for the wedged CLI.") -ForegroundColor Red
} else {
  Write-Host "no TIMEOUT cycles in window (all cycles completed with an exit code)" -ForegroundColor DarkGreen
}

if ($Html) {
  $genTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  $tr = ($rows | ForEach-Object {
      $c = if ($_.Timeout -gt 0 -or $_.Err -gt 0) { '#d98a8a' } elseif ($_.Cycles -eq 0) { '#7a7a88' } else { '#5bbf8a' }
      $f = { param($v) if ($null -ne $v) { $v } else { '-' } }
      "<tr><td><b>$($_.AI)</b></td><td>$($_.Cycles)</td><td style='color:#5bbf8a'>$($_.OK)</td><td style='color:#d98a8a'>$($_.Err)</td><td style='color:$c'>$($_.Timeout)</td><td style='color:#e0b24a'>$($_.Quota)</td><td class='mut'>$($_.Incomplete)</td><td>$(&$f $_.p50s)</td><td>$(&$f $_.p95s)</td><td>$(&$f $_.maxs)</td></tr>"
    }) -join "`n"
  $doc = @"
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Hub Events</title><style>
:root{--bg:#16161c;--line:#2c2c38;--tx:#e7e7ee;--mut:#a0a0b2}
body{margin:0;background:var(--bg);color:var(--tx);font-family:Pretendard,system-ui,sans-serif;padding:28px 18px}
.wrap{max-width:960px;margin:0 auto}h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:12.5px;margin-bottom:18px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left}
th{color:var(--mut);background:#20202a;font-weight:600}.mut{color:var(--mut)}
.note{color:var(--mut);font-size:12px;margin-top:14px;line-height:1.6}
</style></head><body><div class="wrap">
<h1>AI Hub Events &mdash; per-cycle trace</h1>
<div class="sub">$genTime KST &middot; window ${Days}d &middot; $($all.Count) events &middot; OTel-GenAI schema (events.jsonl)</div>
<table><tr><th>AI</th><th>cycles</th><th>OK</th><th>Err</th><th>TIMEOUT</th><th>Quota</th><th>Inc</th><th>p50 s</th><th>p95 s</th><th>max s</th></tr>
$tr
</table>
<div class="note">TIMEOUT cycles emit no exit line, so hub-usage.ps1 cannot see them &mdash; this trace can. Latency p50/p95/max derived from cycle BEGIN&rarr;END. Inc = incomplete (daemon killed mid-cycle). Source: tools/trace/events.jsonl, backfilled from hub-daemon.log; the daemon can later append the same schema live.</div>
</div></body></html>
"@
  $outDir = Join-Path $root 'Output'
  if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
  $outFile = Join-Path $outDir ("hub-events-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".html")
  [System.IO.File]::WriteAllText($outFile, $doc, $utf8)
  Write-Host ""
  Write-Host "  HTML -> $outFile" -ForegroundColor Green
  try { Start-Process $outFile } catch {}
}
