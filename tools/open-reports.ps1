# open-reports.ps1 -- surface the hub AIs' HTML reports (PROTOCOL section 16).
# WHY: each AI writes a self-contained HTML report to agents/<ai>/outbox/preview/, but in
# DAEMON (headless) mode the in-AI `start ""` auto-open cannot pop a browser, so the reports
# pile up unseen. This opens the most recent ones for the user on demand.
#
# Usage (VS Code terminal):
#   powershell -ExecutionPolicy Bypass -File "tools/open-reports.ps1"            # open 6 latest
#   powershell -ExecutionPolicy Bypass -File "tools/open-reports.ps1" -Count 10  # open 10 latest
#   powershell -ExecutionPolicy Bypass -File "tools/open-reports.ps1" -SinceHours 3
#   powershell -ExecutionPolicy Bypass -File "tools/open-reports.ps1" -Only codex
#   powershell -ExecutionPolicy Bypass -File "tools/open-reports.ps1" -List      # list only, don't open
param(
  [int]$Count = 6,
  [double]$SinceHours = 0,          # 0 = ignore age, use -Count; >0 = open everything newer than N hours
  [string]$Only = '',               # claude|codex|antigravity|grok ; '' = all
  [switch]$List,                    # list only, do not open
  [switch]$IncludeOutput            # also include Communication/Output/*.html
)
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent

$ais = if ($Only) { @($Only) } else { @('claude','codex','antigravity','grok') }
$items = @()
foreach ($a in $ais) {
  $pv = Join-Path $root "agents\$a\outbox\preview"
  if (Test-Path $pv) {
    Get-ChildItem (Join-Path $pv '*.html') -ErrorAction SilentlyContinue | ForEach-Object {
      $items += [pscustomobject]@{ AI = $a; Time = $_.LastWriteTime; Name = $_.Name; Path = $_.FullName }
    }
  }
}
if ($IncludeOutput) {
  $out = Join-Path $root 'Output'
  if (Test-Path $out) {
    Get-ChildItem (Join-Path $out '*.html') -ErrorAction SilentlyContinue | ForEach-Object {
      $items += [pscustomobject]@{ AI = 'output'; Time = $_.LastWriteTime; Name = $_.Name; Path = $_.FullName }
    }
  }
}

$items = @($items | Sort-Object Time -Descending)
if ($SinceHours -gt 0) {
  $cut = (Get-Date).AddHours(-$SinceHours)
  $pick = @($items | Where-Object { $_.Time -ge $cut })
} else {
  $pick = @($items | Select-Object -First $Count)
}

$bar = ('=' * 72)
Write-Host $bar -ForegroundColor Cyan
Write-Host ("  HUB REPORTS  ({0} total, opening {1})  @ {2} KST" -f $items.Count, $pick.Count, (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) -ForegroundColor Cyan
Write-Host $bar -ForegroundColor Cyan
if ($pick.Count -eq 0) { Write-Host "  (no HTML reports found - is the hub running? are AIs on PROTOCOL section 16?)" -ForegroundColor Yellow; return }

foreach ($it in $pick) {
  Write-Host ("  {0:MM-dd HH:mm}  [{1,-11}]  {2}" -f $it.Time, $it.AI, $it.Name)
  if (-not $List) { try { Start-Process $it.Path } catch { Write-Host ("    ! open failed: " + $_.Exception.Message) -ForegroundColor Red } }
}
Write-Host $bar -ForegroundColor Cyan
if ($List) { Write-Host "  (-List: not opened. Re-run without -List to open in browser.)" -ForegroundColor DarkGray }
else { Write-Host ("  opened {0} report(s) in your default browser." -f $pick.Count) -ForegroundColor Green }
