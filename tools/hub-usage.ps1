# hub-usage.ps1 -- per-AI usage / activity monitor for the 4-AI hub.
# The hub AIs run on subscription CLIs (codex/grok/gemini) + interactive Claude, so there is NO
# per-token billing to read -- "usage" here = ACTIVITY: cycles run, success/error/quota breakdown,
# commits landed, reports delivered, model in use, last-active, and current backoff state.
# (If a CLI ever exposes token counts in the daemon log, the parser picks them up under Tokens.)
#
#   powershell -ExecutionPolicy Bypass -File tools/hub-usage.ps1            # console table
#   powershell -ExecutionPolicy Bypass -File tools/hub-usage.ps1 -Html      # + write Output/ HTML and open it
#   powershell -ExecutionPolicy Bypass -File tools/hub-usage.ps1 -Json      # machine output
param([switch]$Html, [switch]$Json)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent
$toolsDir = $PSScriptRoot
$dlog = Join-Path $toolsDir 'hub-daemon.log'

# Shared read (daemon may be appending) -- same pattern as monitor/feed/hub-health.
function Read-SharedLog([string]$path, [int]$tail = 0) {
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

$emails = @{ claude='claude@2nd-b.ai'; codex='codex@2nd-b.ai'; antigravity='antigravity@2nd-b.ai'; grok='grok@2nd-b.ai' }
$models = @{}
try {
  $mj = Get-Content (Join-Path $toolsDir 'models.json') -Raw | ConvertFrom-Json
  foreach ($a in $emails.Keys) { if ($mj.$a) { $models[$a] = "$($mj.$a.model) ($($mj.$a.effort))" } }
} catch {}

$log = Read-SharedLog $dlog
$ais = @('claude','codex','antigravity','grok')
$rows = @()
foreach ($a in $ais) {
  # cycles + exit-code breakdown from the shared daemon log (claude has no daemon)
  $exits = @($log | Select-String -Pattern ("exit\(" + $a + "(?:/[^)]*)?\)=(-?\d+)\s*(\w+)?") -AllMatches | ForEach-Object { $_.Matches })
  $cycles = $exits.Count
  $ok = 0; $err = 0; $quota = 0
  foreach ($m in $exits) {
    $code = [int]$m.Groups[1].Value; $tag = $m.Groups[2].Value
    if ($code -eq 0) { $ok++ } elseif ($tag -match 'QUOTA') { $quota++ } else { $err++ }
  }
  # current backoff state
  $backoff = @($log | Select-String -Pattern ($a + " SKIP \(quota backoff, (\d+) cycles") | Select-Object -Last 1)
  $state = if ($backoff) { "quota-backoff ($($backoff.Matches[0].Groups[1].Value) left)" } elseif ($a -eq 'claude') { 'interactive' } else { 'active' }
  # commits landed (this AI's identity) in the hub repo
  $commits = 0
  try { $commits = @(git -C $root log --author="$($emails[$a])" --oneline 2>$null).Count } catch {}
  # reports delivered = outbox md count
  $reports = @(Get-ChildItem (Join-Path $root "agents\$a\outbox") -Filter *.md -ErrorAction SilentlyContinue).Count
  # last active = most recent commit by this author
  $last = ''
  try { $last = (git -C $root log --author="$($emails[$a])" -1 --format='%ad' --date=format:'%m-%d %H:%M' 2>$null) } catch {}
  # tokens if ever logged (subscription CLIs do not expose; placeholder)
  $tok = @($log | Select-String -Pattern ($a + ".*?(\d+)\s*tokens") | Select-Object -Last 1)
  $tokens = if ($tok) { $tok.Matches[0].Groups[1].Value } else { 'n/a (sub CLI)' }
  $rows += [pscustomobject]@{
    AI = $a; Model = ($models[$a]); Cycles = $cycles; OK = $ok; Err = $err; Quota = $quota
    Commits = $commits; Reports = $reports; LastActive = $last; State = $state; Tokens = $tokens
  }
}

if ($Json) { $rows | ConvertTo-Json -Depth 4; return }

# Console
Write-Host ""
Write-Host ("=" * 92)
Write-Host "  AI HUB USAGE   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') KST   (activity, not per-token billing -- sub CLIs)" -ForegroundColor Cyan
Write-Host ("=" * 92)
$rows | Format-Table -AutoSize @{L='AI';E={$_.AI}}, @{L='Model';E={$_.Model}}, @{L='Cyc';E={$_.Cycles}}, @{L='OK';E={$_.OK}}, @{L='Err';E={$_.Err}}, @{L='Quota';E={$_.Quota}}, @{L='Commits';E={$_.Commits}}, @{L='Reports';E={$_.Reports}}, @{L='LastActive';E={$_.LastActive}}, @{L='State';E={$_.State}} | Out-String | Write-Host
Write-Host "  Tokens: subscription CLIs (codex/grok/gemini) + interactive Claude are not per-token metered, so token usage is not exposed. Cycles/Commits/Reports are the real activity signal." -ForegroundColor DarkGray

if ($Html) {
  $genTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  $trs = ($rows | ForEach-Object {
    $st = $_.State; $stColor = if ($st -match 'backoff') { '#e0b24a' } elseif ($st -eq 'interactive') { '#8b8bf0' } else { '#5bbf8a' }
    $errCell = if ($_.Err -gt 0) { "<td style='color:#c98b8b'>$($_.Err)</td>" } else { "<td>$($_.Err)</td>" }
    "<tr><td><b>$($_.AI)</b></td><td class='mono'>$($_.Model)</td><td>$($_.Cycles)</td><td style='color:#5bbf8a'>$($_.OK)</td>$errCell<td style='color:#e0b24a'>$($_.Quota)</td><td>$($_.Commits)</td><td>$($_.Reports)</td><td class='mut'>$($_.LastActive)</td><td style='color:$stColor'>$($_.State)</td></tr>"
  }) -join "`n"
  $doc = @"
<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Hub Usage</title><style>
:root{--bg:#16161c;--card:#1d1d25;--line:#2c2c38;--tx:#e7e7ee;--mut:#a0a0b2}
body{margin:0;background:var(--bg);color:var(--tx);font-family:Pretendard,system-ui,sans-serif;padding:28px 18px}
.wrap{max-width:1000px;margin:0 auto}h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:12.5px;margin-bottom:18px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left}
th{color:var(--mut);background:#20202a;font-weight:600}.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px}.mut{color:var(--mut)}
.note{color:var(--mut);font-size:12px;margin-top:14px;line-height:1.6}
</style></head><body><div class="wrap">
<h1>AI Hub Usage</h1><div class="sub">$genTime KST · 활동 기준(구독 CLI라 per-token 과금 없음)</div>
<table><tr><th>AI</th><th>Model (effort)</th><th>Cycles</th><th>OK</th><th>Err</th><th>Quota</th><th>Commits</th><th>Reports</th><th>Last active</th><th>State</th></tr>
$trs
</table>
<div class="note">Cycles = 데몬 사이클 완료 수(exit). OK/Err/Quota = 사이클 결과. Commits = 허브 git에 각 AI 정체성으로 랜딩한 커밋. Reports = outbox 산출물 수. Claude는 데몬 없는 인터랙티브.<br>
Tokens 미표시: codex/grok/gemini는 구독 CLI + Claude 인터랙티브라 per-token 미과금·미노출. 활동량은 Cycles/Commits/Reports로 본다. (Anthropic 6/15 헤드리스만 metered.)</div>
</div></body></html>
"@
  $outDir = Join-Path $root 'Output'
  $outFile = Join-Path $outDir ("hub-usage-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".html")
  Set-Content -LiteralPath $outFile -Value $doc -Encoding utf8
  Write-Host "  HTML -> $outFile" -ForegroundColor Green
  try { Start-Process $outFile } catch {}
}
