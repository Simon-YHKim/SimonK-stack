# hub-insight.ps1 -- VALUE / NOVELTY / DEGENERATION instrument for the 4-AI hub.
# ASCII-only source (PS 5.1 no-BOM safe). READ-ONLY: reads git log + outbox only.
#
# WHY: monitor.ps1 / hub-usage.ps1 measure LIVENESS and ACTIVITY (cycles, commits,
# OK/Err). They cannot tell "busy" from "productive": a lane that commits the SAME
# semantic work every cycle looks green + high-commit while producing zero net value
# (observed 2026-07-11: codex landed ~40 near-identical "records branch refresh"
# commits). This tool measures PROGRESS/NOVELTY: it normalizes each commit subject to
# a topic signature (drop the conventional-commit type/scope prefix, lower-case, strip
# digits/hashes/punctuation, reduce to a SORTED unique-word set so "report records
# branch refresh" == "refresh records branch report"), then per lane reports:
#   commits, distinct topics, novelty% (distinct/total), wasted (repeats),
#   top repeated topic + count, and "since-new" = age of the last commit that
#   introduced a topic not seen before it. A lane whose top topic repeats >=
#   -DegenerateThreshold times inside the window is flagged DEGENERATE.
#
# Usage (cwd = hub root):
#   powershell -ExecutionPolicy Bypass -File tools/hub-insight.ps1            # console, last 7d
#   powershell -ExecutionPolicy Bypass -File tools/hub-insight.ps1 -Days 3
#   powershell -ExecutionPolicy Bypass -File tools/hub-insight.ps1 -Json      # machine output
#   powershell -ExecutionPolicy Bypass -File tools/hub-insight.ps1 -Html      # + Output/ HTML, opens it
param(
  [int]$Days = 7,
  [int]$DegenerateThreshold = 5,
  [switch]$Json,
  [switch]$Html
)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent

$emails = [ordered]@{
  claude='claude@2nd-b.ai'; codex='codex@2nd-b.ai'; antigravity='antigravity@2nd-b.ai'; grok='grok@2nd-b.ai'
}
$emailToAI = @{}
foreach ($k in $emails.Keys) { $emailToAI[$emails[$k]] = $k }

# Words that carry no topic signal -- dropped before building the signature so that
# process-noise verbs do not make two different reports look distinct (or the same).
$stop = @{}
foreach ($w in @('the','a','an','of','for','to','in','on','and','or','re','and',
                 'report','reports','update','updates','refresh','refreshed','status',
                 'verify','verified','verification','cycle','branch','chore','docs','test')) { $stop[$w] = $true }

function Get-Signature([string]$subject) {
  # 1) drop conventional-commit "type(scope): " prefix
  $s = $subject -replace '^(feat|fix|chore|docs|test|refactor|style|perf|ci|build|revert|merge)(\([^)]*\))?!?:\s*', ''
  # 2) lower + strip hashes/digits/punctuation
  $s = $s.ToLowerInvariant()
  $s = $s -replace '[0-9a-f]{7,40}', ' '       # sha-like
  $s = $s -replace '[0-9]+', ' '               # any number
  $s = $s -replace '[^a-z ]', ' '              # keep letters + space
  # 3) reduce to sorted unique non-stopword tokens
  $words = @($s -split '\s+' | Where-Object { $_ -and -not $stop.ContainsKey($_) -and $_.Length -ge 2 } | Sort-Object -Unique)
  if ($words.Count -eq 0) { return '(process-noise)' }
  return ($words -join ' ')
}

# git log window: hash | committer-ISO | author-email | subject
$since = "$Days days ago"
$raw = @(git -C $root log --since="$since" --pretty=format:'%H|%cI|%ae|%s' 2>$null)

$byAI = @{}
foreach ($k in $emails.Keys) { $byAI[$k] = New-Object System.Collections.ArrayList }
$hubSig = @{}   # signature -> count (hub-wide)

foreach ($line in $raw) {
  if (-not $line) { continue }
  $p = $line.Split('|', 4)
  if ($p.Count -lt 4) { continue }
  $iso = $p[1]; $email = $p[2].ToLowerInvariant(); $subj = $p[3]
  $ai = $emailToAI[$email]
  if (-not $ai) { $ai = 'other' }
  $sig = Get-Signature $subj
  if (-not $hubSig.ContainsKey($sig)) { $hubSig[$sig] = 0 }
  $hubSig[$sig]++
  if ($byAI.ContainsKey($ai)) {
    [void]$byAI[$ai].Add([pscustomobject]@{ Iso=$iso; Subj=$subj; Sig=$sig })
  }
}

$now = Get-Date
$rows = @()
foreach ($ai in $emails.Keys) {
  $items = @($byAI[$ai])
  $total = $items.Count
  if ($total -eq 0) {
    $rows += [pscustomobject]@{ AI=$ai; Commits=0; Topics=0; NoveltyPct=100; Wasted=0; TopTopic='-'; TopCount=0; SinceNewH=$null; Degenerate=$false; TopSubjectSample='' }
    continue
  }
  # commits arrive newest-first from git log; reverse to oldest-first for first-seen walk
  $chrono = @($items)
  [array]::Reverse($chrono)
  $seen = @{}
  $lastNewIso = $null
  $sigCount = @{}
  $sampleForSig = @{}
  foreach ($it in $chrono) {
    if (-not $seen.ContainsKey($it.Sig)) { $seen[$it.Sig] = $true; $lastNewIso = $it.Iso }
    if (-not $sigCount.ContainsKey($it.Sig)) { $sigCount[$it.Sig] = 0; $sampleForSig[$it.Sig] = $it.Subj }
    $sigCount[$it.Sig]++
  }
  $distinct = $seen.Count
  $novelty = [math]::Round(100.0 * $distinct / $total, 0)
  $wasted = $total - $distinct
  $top = $sigCount.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1
  $topTopic = $top.Key; $topCount = $top.Value
  $sinceNewH = $null
  if ($lastNewIso) { try { $sinceNewH = [math]::Round(($now - [datetime]::Parse($lastNewIso)).TotalHours, 1) } catch {} }
  $degen = ($topCount -ge $DegenerateThreshold -and $topTopic -ne '(process-noise)')
  $rows += [pscustomobject]@{
    AI=$ai; Commits=$total; Topics=$distinct; NoveltyPct=$novelty; Wasted=$wasted
    TopTopic=$topTopic; TopCount=$topCount; SinceNewH=$sinceNewH; Degenerate=$degen
    TopSubjectSample=$sampleForSig[$topTopic]
  }
}

# hub-wide top churn signatures
$hubTop = @($hubSig.GetEnumerator() | Where-Object { $_.Key -ne '(process-noise)' } | Sort-Object Value -Descending | Select-Object -First 8)

if ($Json) {
  [pscustomobject]@{
    generated = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    windowDays = $Days
    degenerateThreshold = $DegenerateThreshold
    lanes = $rows
    hubTopChurn = @($hubTop | ForEach-Object { [pscustomobject]@{ topic=$_.Key; count=$_.Value } })
  } | ConvertTo-Json -Depth 5
  return
}

# ---- Console ----
Write-Host ""
Write-Host ("=" * 96) -ForegroundColor Cyan
Write-Host ("  AI HUB INSIGHT -- value/novelty   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') KST   window=${Days}d  degen>=$DegenerateThreshold") -ForegroundColor Cyan
Write-Host ("=" * 96) -ForegroundColor Cyan
Write-Host ("{0,-12}{1,-8}{2,-8}{3,-9}{4,-8}{5,-9}{6}" -f 'AI','commits','topics','novelty','wasted','sinceNew','top repeated topic') -ForegroundColor White
foreach ($r in $rows) {
  $col = if ($r.Degenerate) { 'Red' } elseif ($r.Commits -eq 0) { 'DarkGray' } elseif ($r.NoveltyPct -lt 50) { 'Yellow' } else { 'Gray' }
  $sn = if ($null -ne $r.SinceNewH) { ("{0}h" -f $r.SinceNewH) } else { '-' }
  $topShow = if ($r.TopCount -ge 2) { ("x{0} {1}" -f $r.TopCount, $r.TopTopic) } else { '-' }
  if ($topShow.Length -gt 40) { $topShow = $topShow.Substring(0,39) + '~' }
  Write-Host ("{0,-12}{1,-8}{2,-8}{3,-9}{4,-8}{5,-9}{6}" -f $r.AI,$r.Commits,$r.Topics,("$($r.NoveltyPct)%"),$r.Wasted,$sn,$topShow) -ForegroundColor $col
}
Write-Host ("-" * 96) -ForegroundColor DarkGray
$degenLanes = @($rows | Where-Object { $_.Degenerate })
if ($degenLanes.Count -gt 0) {
  foreach ($d in $degenLanes) {
    Write-Host ("!! DEGENERATE LOOP -- {0}: same topic x{1} in {2}d (novelty {3}%, {4} wasted commits). Sample: {5}" -f `
      $d.AI, $d.TopCount, $Days, $d.NoveltyPct, $d.Wasted, $d.TopSubjectSample) -ForegroundColor Red
  }
  Write-Host "   -> the lane is re-doing the same work each cycle. Close/quarantine the driving order or add a novelty gate." -ForegroundColor Yellow
} else {
  Write-Host "value: healthy (no lane repeating one topic past the degenerate threshold)" -ForegroundColor DarkGreen
}
Write-Host ("-" * 96) -ForegroundColor DarkGray
Write-Host "hub-wide top churn topics:" -ForegroundColor DarkCyan
foreach ($h in $hubTop) {
  $c = if ($h.Value -ge $DegenerateThreshold) { 'Red' } elseif ($h.Value -ge 3) { 'Yellow' } else { 'Gray' }
  Write-Host ("  x{0,-4} {1}" -f $h.Value, $h.Key) -ForegroundColor $c
}

if ($Html) {
  $genTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  $laneRows = ($rows | ForEach-Object {
    $stateCol = if ($_.Degenerate) { '#d98a8a' } elseif ($_.Commits -eq 0) { '#7a7a88' } elseif ($_.NoveltyPct -lt 50) { '#e0b24a' } else { '#5bbf8a' }
    $sn = if ($null -ne $_.SinceNewH) { ("{0}h" -f $_.SinceNewH) } else { '-' }
    $flag = if ($_.Degenerate) { " <span class='badge'>DEGENERATE</span>" } else { '' }
    $topShow = if ($_.TopCount -ge 2) { ("x{0} {1}" -f $_.TopCount, $_.TopTopic) } else { '-' }
    "<tr><td><b>$($_.AI)</b>$flag</td><td>$($_.Commits)</td><td>$($_.Topics)</td><td style='color:$stateCol'>$($_.NoveltyPct)%</td><td>$($_.Wasted)</td><td class='mut'>$sn</td><td class='mono'>$topShow</td></tr>"
  }) -join "`n"
  # topic signatures are reduced to [a-z ] only, so no HTML-escaping is needed here.
  $churnRows = ($hubTop | ForEach-Object {
    $c = if ($_.Value -ge $DegenerateThreshold) { '#d98a8a' } elseif ($_.Value -ge 3) { '#e0b24a' } else { '#a0a0b2' }
    "<tr><td style='color:$c'>x$($_.Value)</td><td class='mono'>$($_.Key)</td></tr>"
  }) -join "`n"
  $doc = @"
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Hub Insight</title><style>
:root{--bg:#16161c;--card:#1d1d25;--line:#2c2c38;--tx:#e7e7ee;--mut:#a0a0b2}
body{margin:0;background:var(--bg);color:var(--tx);font-family:Pretendard,system-ui,sans-serif;padding:28px 18px}
.wrap{max-width:1040px;margin:0 auto}h1{font-size:20px;margin:0 0 2px}h2{font-size:14px;color:var(--mut);margin:26px 0 8px}
.sub{color:var(--mut);font-size:12.5px;margin-bottom:18px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left}
th{color:var(--mut);background:#20202a;font-weight:600}.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px}.mut{color:var(--mut)}
.badge{background:#5a2530;color:#f0b6b6;font-size:10px;padding:1px 6px;border-radius:8px;margin-left:6px;vertical-align:middle}
.note{color:var(--mut);font-size:12px;margin-top:14px;line-height:1.6}
</style></head><body><div class="wrap">
<h1>AI Hub Insight &mdash; value / novelty</h1>
<div class="sub">$genTime KST &middot; window ${Days}d &middot; degenerate threshold &ge; $DegenerateThreshold repeats. Measures PROGRESS, not activity.</div>
<table><tr><th>AI</th><th>commits</th><th>topics</th><th>novelty</th><th>wasted</th><th>since-new</th><th>top repeated topic</th></tr>
$laneRows
</table>
<h2>hub-wide top churn topics</h2>
<table><tr><th>count</th><th>topic signature</th></tr>
$churnRows
</table>
<div class="note">novelty% = distinct topics / commits. wasted = repeated commits (total - distinct). since-new = hours since the last commit that introduced a NEW topic (a lane stuck on one topic grows this without bound). A lane flagged DEGENERATE is re-doing the same semantic work each cycle &mdash; close the driving order or add a novelty gate to the daemon. Topic signature = subject with type prefix + digits removed, reduced to a sorted unique-word set.</div>
</div></body></html>
"@
  $outDir = Join-Path $root 'Output'
  if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
  $outFile = Join-Path $outDir ("hub-insight-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".html")
  [System.IO.File]::WriteAllText($outFile, $doc, $utf8)
  Write-Host ""
  Write-Host "  HTML -> $outFile" -ForegroundColor Green
  try { Start-Process $outFile } catch {}
}
