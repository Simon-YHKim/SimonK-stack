# hub-dashboard.ps1 -- single glanceable HTML view of the 4-AI hub (2026-07-11 audit B5).
# ASCII-only source (PS 5.1 no-BOM safe). READ-ONLY: composes the read-only collectors
# hub-events.ps1 (-Json: cycles/TIMEOUT/latency p95) + hub-insight.ps1 (-Json: value/novelty/
# churn/DEGENERATE) + CONTROL.state + recent git log into ONE dark-theme page written to Output/.
# WHY: live-state (monitor), trace (hub-events), and value (hub-insight) were three separate
# console tools; a hub run for mobile/remote operation needs one URL that answers "is it healthy,
# who's working, what's stuck, is any lane degenerate". Touches no daemon/commit hot path.
#
#   powershell -ExecutionPolicy Bypass -File tools/hub-dashboard.ps1            # write + open (7d)
#   powershell -ExecutionPolicy Bypass -File tools/hub-dashboard.ps1 -Days 2 -NoOpen
param([int]$Days = 7, [switch]$NoOpen)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent

function Invoke-Json([string]$script, [hashtable]$params) {
  # hashtable splat binds by NAME (array splat would pass -Json positionally into -Days).
  try {
    $out = (& (Join-Path $PSScriptRoot $script) @params) | Out-String
    if ($out.Trim()) { return ($out | ConvertFrom-Json) }
  } catch { }
  return $null
}

$ev = Invoke-Json 'hub-events.ps1'  @{ Json = $true; Days = $Days }
$ins = Invoke-Json 'hub-insight.ps1' @{ Json = $true; Days = $Days }

# CONTROL run-state
$controlState = '?'; $controlReason = ''
$cf = Join-Path $root 'CONTROL.md'
if (Test-Path $cf) {
  $ch = Get-Content $cf -Encoding UTF8 -TotalCount 12
  foreach ($l in $ch) {
    if ($l -match '^state:\s*"?(.*?)"?\s*$') { $controlState = $Matches[1] }
    if ($l -match '^resume_reason:\s*"?(.*?)"?\s*$') { $controlReason = $Matches[1] }
  }
}

$ais = @('claude', 'codex', 'antigravity', 'grok')
function LaneEv($ai) { if ($ev) { return @($ev.lanes | Where-Object { $_.AI -eq $ai })[0] } return $null }
function LaneIn($ai) { if ($ins) { return @($ins.lanes | Where-Object { $_.AI -eq $ai })[0] } return $null }

$rows = @()
foreach ($ai in $ais) {
  $e = LaneEv $ai; $i = LaneIn $ai
  $rows += [pscustomobject]@{
    AI = $ai
    Cycles = if ($e) { $e.Cycles } else { 0 }
    OK = if ($e) { $e.OK } else { 0 }
    Err = if ($e) { $e.Err } else { 0 }
    Timeout = if ($e) { $e.Timeout } else { 0 }
    P95 = if ($e -and $null -ne $e.p95s) { $e.p95s } else { $null }
    Novelty = if ($i) { $i.NoveltyPct } else { $null }
    Wasted = if ($i) { $i.Wasted } else { 0 }
    Degenerate = if ($i) { [bool]$i.Degenerate } else { $false }
    TopRepeat = if ($i -and $i.TopCount -ge 2) { ("x{0} {1}" -f $i.TopCount, $i.TopTopic) } else { '-' }
  }
}

# alarms
$degen = @($rows | Where-Object { $_.Degenerate })
$toTotal = ($rows | Measure-Object -Property Timeout -Sum).Sum
$errTotal = ($rows | Measure-Object -Property Err -Sum).Sum

# recent commits
$commits = @()
try { $commits = @(git -C $root log -10 --format='%cd|%an|%s' --date=format:'%m-%d %H:%M' 2>$null) } catch {}

$genTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$stateColor = if ($controlState -eq 'running') { '#5bbf8a' } elseif ($controlState -eq 'paused') { '#e06a6a' } else { '#e0b24a' }

$alarmHtml = ''
if ($degen.Count -gt 0) { $alarmHtml += "<div class='alarm bad'>&#9888; DEGENERATE LOOP: " + (($degen | ForEach-Object { $_.AI + " (" + $_.TopRepeat + ")" }) -join ', ') + " &mdash; lane re-doing the same work; the commit-path A1 gate clamps it after 3 repeats.</div>" }
if ($toTotal -gt 0) { $alarmHtml += "<div class='alarm warn'>&#9888; $toTotal TIMEOUT cycle(s) in ${Days}d (invisible to hub-usage.ps1) &mdash; check tools/live/&lt;ai&gt;.log.</div>" }
if ($errTotal -gt 0) { $alarmHtml += "<div class='alarm warn'>$errTotal error cycle(s) in ${Days}d.</div>" }
if (-not $alarmHtml) { $alarmHtml = "<div class='alarm ok'>&#10003; no degenerate loop, no timeouts &mdash; lanes healthy.</div>" }

$laneRows = ($rows | ForEach-Object {
    $nc = if ($null -eq $_.Novelty) { '#7a7a88' } elseif ($_.Degenerate) { '#e06a6a' } elseif ($_.Novelty -lt 50) { '#e0b24a' } else { '#5bbf8a' }
    $flag = if ($_.Degenerate) { " <span class='badge'>DEGEN</span>" } else { '' }
    $nov = if ($null -ne $_.Novelty) { "$($_.Novelty)%" } else { '-' }
    $p95 = if ($null -ne $_.P95) { "$($_.P95)s" } else { '-' }
    $toc = if ($_.Timeout -gt 0) { "<td style='color:#e06a6a'>$($_.Timeout)</td>" } else { "<td>$($_.Timeout)</td>" }
    "<tr><td><b>$($_.AI)</b>$flag</td><td>$($_.Cycles)</td><td style='color:#5bbf8a'>$($_.OK)</td><td style='color:#d98a8a'>$($_.Err)</td>$toc<td>$p95</td><td style='color:$nc'>$nov</td><td>$($_.Wasted)</td><td class='mono mut'>$($_.TopRepeat)</td></tr>"
  }) -join "`n"

$churnRows = ''
if ($ins -and $ins.hubTopChurn) {
  $churnRows = (@($ins.hubTopChurn) | Select-Object -First 6 | ForEach-Object {
      $c = if ($_.count -ge 5) { '#e06a6a' } elseif ($_.count -ge 3) { '#e0b24a' } else { '#a0a0b2' }
      "<tr><td style='color:$c'>x$($_.count)</td><td class='mono'>$($_.topic)</td></tr>"
    }) -join "`n"
}

$commitRows = ($commits | ForEach-Object {
    $p = $_.Split('|', 3)
    if ($p.Count -ge 3) { "<tr><td class='mut'>$($p[0])</td><td>$($p[1])</td><td class='mono'>$([System.Net.WebUtility]::HtmlEncode($p[2]))</td></tr>" }
  }) -join "`n"

$doc = @"
<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Hub Dashboard</title><style>
:root{--bg:#15151b;--card:#1d1d25;--line:#2c2c38;--tx:#e7e7ee;--mut:#a0a0b2}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font-family:Pretendard,system-ui,sans-serif;padding:24px 16px}
.wrap{max-width:940px;margin:0 auto}h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:12.5px;margin-bottom:16px}
h2{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;margin:24px 0 8px}
.state{display:inline-block;font-weight:800;font-size:15px}
.alarm{border-radius:9px;padding:9px 13px;font-size:12.8px;margin:6px 0}
.alarm.bad{background:#3a1e22;color:#f0b6b6}.alarm.warn{background:#3a331e;color:#f0d6a0}.alarm.ok{background:#1e3a2b;color:#a6e6c4}
table{width:100%;border-collapse:collapse;font-size:12.7px}th,td{border:1px solid var(--line);padding:7px 9px;text-align:left}
th{color:var(--mut);background:#20202a;font-weight:600}.mono{font-family:ui-monospace,Consolas,monospace;font-size:11.5px}.mut{color:var(--mut)}
.badge{background:#5a2530;color:#f0b6b6;font-size:9.5px;padding:1px 6px;border-radius:8px;margin-left:5px}
.note{color:var(--mut);font-size:11.5px;margin-top:12px;line-height:1.6}
</style></head><body><div class="wrap">
<h1>AI Hub Dashboard</h1>
<div class="sub">$genTime KST &middot; window ${Days}d &middot; run-state: <span class="state" style="color:$stateColor">$($controlState.ToUpper())</span></div>
$alarmHtml
<h2>lanes &mdash; value &times; reliability</h2>
<table><tr><th>AI</th><th>cycles</th><th>OK</th><th>Err</th><th>TIMEOUT</th><th>p95</th><th>novelty</th><th>wasted</th><th>top repeated</th></tr>
$laneRows
</table>
<h2>hub-wide top churn topics</h2>
<table><tr><th>count</th><th>topic signature</th></tr>
$churnRows
</table>
<h2>recent hub commits</h2>
<table><tr><th>when</th><th>author</th><th>subject</th></tr>
$commitRows
</table>
<div class="note">Composes read-only collectors: hub-events.ps1 (cycles/TIMEOUT/latency p95 from tools/trace/events.jsonl) + hub-insight.ps1 (novelty% = distinct topics / commits; wasted = repeated commits; DEGEN = same topic past threshold) + CONTROL.state. novelty and TIMEOUT are the two signals monitor.ps1 / hub-usage.ps1 could not show. A DEGEN lane is structurally clamped by the commit.ps1 A1 anti-degeneration gate.</div>
</div></body></html>
"@

$outDir = Join-Path $root 'Output'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$outFile = Join-Path $outDir ("hub-dashboard-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".html")
[System.IO.File]::WriteAllText($outFile, $doc, $utf8)
Write-Host "[hub-dashboard] -> $outFile" -ForegroundColor Green
if (-not $NoOpen) { try { Start-Process $outFile } catch {} }
