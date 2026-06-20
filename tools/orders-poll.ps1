# orders-poll.ps1 — Deterministic poll of Simon's remote orders (2nd-B ORDERS.md §33).
# Fetches origin/main, finds O-13+ order blocks in "## OPEN" that are NOT yet in "## DONE".
# Used by the PC Claude /loop as the receiving end of the remote-order pipeline.
#   pwsh tools/orders-poll.ps1            # human-readable
#   pwsh tools/orders-poll.ps1 -Json      # machine: {newCount, newIds, blocks}
param([switch]$Json, [string]$Repo = "E:\2ndB", [int]$MinId = 13)

$ErrorActionPreference = "Stop"
function Out-Result($obj) {
  if ($Json) { $obj | ConvertTo-Json -Depth 6 -Compress }
  else {
    if ($obj.newCount -eq 0) { Write-Output "NO NEW ORDERS (open O-ids: $($obj.openIds -join ', ' ); done: $($obj.doneIds -join ', '))" }
    else {
      Write-Output "NEW ORDERS: $($obj.newCount)  -> O-$($obj.newIds -join ', O-')"
      foreach ($b in $obj.blocks) { Write-Output "`n----- O-$($b.id) -----`n$($b.text)" }
    }
  }
}

try { git -C $Repo fetch origin --quiet 2>$null } catch {}
$content = (git -C $Repo show origin/main:ORDERS.md 2>$null) -join "`n"
if (-not $content) { Out-Result @{ error="ORDERS.md unreadable"; newCount=0; newIds=@(); openIds=@(); doneIds=@(); blocks=@() }; return }

# split sections
$openIdx = $content.IndexOf("`n## OPEN")
$doneIdx = $content.IndexOf("`n## DONE")
if ($openIdx -lt 0) { Out-Result @{ error="no ## OPEN"; newCount=0; newIds=@(); openIds=@(); doneIds=@(); blocks=@() }; return }
$openSec = if ($doneIdx -gt $openIdx) { $content.Substring($openIdx, $doneIdx-$openIdx) } else { $content.Substring($openIdx) }
$doneSec = if ($doneIdx -ge 0) { $content.Substring($doneIdx) } else { "" }

# collect O-ids
function Get-Ids($text) {
  [regex]::Matches($text, '\bO-(\d+)\b') | ForEach-Object { [int]$_.Groups[1].Value } | Sort-Object -Unique
}
$openIds = @(Get-Ids $openSec)
$doneIds = @(Get-Ids $doneSec)
$newIds  = @($openIds | Where-Object { $_ -ge $MinId -and $doneIds -notcontains $_ })

# extract each new order's block (from its "### [O-n" header to the next "### [" or end)
$blocks = @()
foreach ($id in $newIds) {
  $m = [regex]::Match($openSec, "(?s)###\s*\[\s*O-$id\b.*?(?=`n###\s*\[|\z)")
  if ($m.Success) { $blocks += @{ id=$id; text=$m.Value.Trim() } }
}

Out-Result @{ newCount=$newIds.Count; newIds=$newIds; openIds=$openIds; doneIds=$doneIds; blocks=$blocks }
