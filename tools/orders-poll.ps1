# orders-poll.ps1 — Deterministic poll of Simon's remote orders (2nd-B ORDERS.md §33).
# Fetches origin/main, finds O-13+ order blocks in "## OPEN" that are NOT yet in "## DONE"
# and NOT acked in tools/orders-ack.json (picked-up-in-progress ledger).
# Used by the PC Claude /loop as the receiving end of the remote-order pipeline.
#   pwsh tools/orders-poll.ps1                 # human-readable
#   pwsh tools/orders-poll.ps1 -Json           # machine: {newCount, newIds, blocks, error, fetchWarn}
#   pwsh tools/orders-poll.ps1 -Ack 31         # record O-31 as picked up (suppress from new until DONE)
# DEDUP CAVEAT (2026-07-03 audit): doneIds matches any \bO-N\b mention in ## DONE prose --
# a passing mention ("next: O-32") would silently consume O-32. Real fix = ORDERS.md hygiene:
# DONE entries should carry explicit "### [O-N" headers. The -Ack ledger fixes the reverse
# failure (an in-progress order like O-31 reappearing as NEW every poll forever).
param([switch]$Json, [string]$Repo = "C:\2ndB", [int]$MinId = 13, [int[]]$Ack = @(), [switch]$Heartbeat)

$ErrorActionPreference = "Stop"
$ackFile = Join-Path $PSScriptRoot 'orders-ack.json'
$utf8 = [System.Text.UTF8Encoding]::new($false)

# -Ack mode: record picked-up order ids and exit.
if ($Ack.Count -gt 0) {
  $cur = @()
  if (Test-Path $ackFile) { try { $cur = @((Get-Content $ackFile -Raw | ConvertFrom-Json)) } catch { $cur = @() } }
  $merged = @($cur + $Ack | ForEach-Object { [int]$_ } | Sort-Object -Unique)
  [System.IO.File]::WriteAllText($ackFile, ($merged | ConvertTo-Json -Compress), $utf8)
  Write-Output "ACKED: O-$($Ack -join ', O-') (ledger: $($merged -join ','))"
  return
}

function Out-Result($obj) {
  if ($Json) { $obj | ConvertTo-Json -Depth 6 -Compress }
  else {
    if ($obj.error) { Write-Output "ORDERS POLL ERROR: $($obj.error)"; exit 1 }
    if ($obj.fetchWarn) { Write-Output "WARN: git fetch failed - reading a possibly STALE origin/main snapshot" }
    if ($obj.newCount -eq 0) { Write-Output "NO NEW ORDERS (open O-ids: $($obj.openIds -join ', ' ); done: $($obj.doneIds -join ', '); acked: $($obj.ackedIds -join ', '))" }
    else {
      Write-Output "NEW ORDERS: $($obj.newCount)  -> O-$($obj.newIds -join ', O-')"
      foreach ($b in $obj.blocks) { Write-Output "`n----- O-$($b.id) -----`n$($b.text)" }
    }
  }
}

$fetchWarn = $false
try { git -C $Repo fetch origin --quiet 2>$null; if ($LASTEXITCODE -ne 0) { $fetchWarn = $true } } catch { $fetchWarn = $true }
$content = (git -C $Repo show origin/main:ORDERS.md 2>$null) -join "`n"
if (-not $content) { Out-Result @{ error="ORDERS.md unreadable (git show origin/main:ORDERS.md empty - clone missing? fetch dead?)"; fetchWarn=$fetchWarn; newCount=0; newIds=@(); openIds=@(); doneIds=@(); ackedIds=@(); blocks=@() }; return }

# split sections
$openIdx = $content.IndexOf("`n## OPEN")
$doneIdx = $content.IndexOf("`n## DONE")
if ($openIdx -lt 0) { Out-Result @{ error="no ## OPEN section in ORDERS.md"; fetchWarn=$fetchWarn; newCount=0; newIds=@(); openIds=@(); doneIds=@(); ackedIds=@(); blocks=@() }; return }
$openSec = if ($doneIdx -gt $openIdx) { $content.Substring($openIdx, $doneIdx-$openIdx) } else { $content.Substring($openIdx) }
$doneSec = if ($doneIdx -ge 0) { $content.Substring($doneIdx) } else { "" }

# collect O-ids
function Get-Ids($text) {
  [regex]::Matches($text, '\bO-(\d+)\b') | ForEach-Object { [int]$_.Groups[1].Value } | Sort-Object -Unique
}
$openIds = @(Get-Ids $openSec)
$doneIds = @(Get-Ids $doneSec)
$ackedIds = @()
if (Test-Path $ackFile) { try { $ackedIds = @((Get-Content $ackFile -Raw | ConvertFrom-Json) | ForEach-Object { [int]$_ }) } catch { $ackedIds = @() } }
$newIds  = @($openIds | Where-Object { $_ -ge $MinId -and $doneIds -notcontains $_ -and $ackedIds -notcontains $_ })

# extract each new order's block (from its "### [O-n" header to the next "### [" or end)
$blocks = @()
foreach ($id in $newIds) {
  $m = [regex]::Match($openSec, "(?s)###\s*\[\s*O-$id\b.*?(?=`n###\s*\[|\z)")
  if ($m.Success) { $blocks += @{ id=$id; text=$m.Value.Trim() } }
}

# CONSUMER heartbeat: written ONLY with -Heartbeat (the /loop director passes it).
# Monitoring polls (hub-watchdog) must NOT pass it, or the liveness signal is circular.
if ($Heartbeat) {
  try { [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'orders-poll-heartbeat.txt'), (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " KST newCount=$($newIds.Count)", $utf8) } catch {}
}

Out-Result @{ newCount=$newIds.Count; newIds=$newIds; openIds=$openIds; doneIds=$doneIds; ackedIds=$ackedIds; blocks=$blocks; fetchWarn=$fetchWarn }
