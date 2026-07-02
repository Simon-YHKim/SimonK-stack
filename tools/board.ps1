# board.ps1 -- Communication Hub status helper (read-only)
# Usage: powershell tools/board.ps1 [-Me claude|codex|antigravity|grok]
# Scans every agents/*/outbox message's frontmatter (to/status/type/ref)
# and shows -Me's inbox = open requests addressed to -Me with no response yet.
# Also shows run-state (CONTROL.md), auth blockers, open consensus, recent HTML reports.

param([string]$Me = "")

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

function Get-Utf8Content {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [int]$TotalCount = 0
  )

  if ($TotalCount -gt 0) {
    return Get-Content -LiteralPath $Path -Encoding UTF8 -TotalCount $TotalCount
  }
  return Get-Content -LiteralPath $Path -Encoding UTF8
}

function Get-MatchedValue {
  param(
    [Parameter(Mandatory=$true)]$Lines,
    [Parameter(Mandatory=$true)][string]$Pattern
  )

  $match = $Lines | Select-String -Pattern $Pattern | Select-Object -First 1
  if ($match) { return $match.Matches[0].Groups[1].Value }
  return ""
}

$root = Split-Path $PSScriptRoot -Parent
$agents = @("claude","codex","antigravity","grok")

Write-Host "=== AI Infra Communication Hub ===`n" -ForegroundColor Cyan

# --- run-state (CONTROL.md) ---
$control = Join-Path $root "CONTROL.md"
if (Test-Path $control) {
  $controlHead = Get-Utf8Content $control -TotalCount 12
  $cstate = Get-MatchedValue $controlHead '^state:\s*(.*)$'
  $creason = Get-MatchedValue $controlHead '^pause_reason:\s*"?(.*?)"?$'
  $color = if ($cstate -eq "running") { "Green" } elseif ($cstate -eq "paused") { "Red" } else { "Yellow" }
  Write-Host ("RUN STATE: {0}" -f $cstate.ToUpper()) -ForegroundColor $color
  if ($creason) { Write-Host ("  reason: {0}" -f $creason) -ForegroundColor DarkGray }
  Write-Host ""
}

# --- scan all outbox messages ---
$msgs = @()
foreach ($a in $agents) {
  $obx = Join-Path $root "agents\$a\outbox"
  if (Test-Path $obx) {
    Get-ChildItem $obx -Filter *.md -File | Where-Object { $_.Name -ne "README.md" } | ForEach-Object {
      $head = Get-Utf8Content $_.FullName -TotalCount 15
      $fm = @{}
      foreach ($line in $head) {
        if ($line -match '^(id|from|to|type|ref|status|priority|project|created|date):\s*"?(.*?)"?\s*$') { $fm[$matches[1]] = $matches[2] }
      }
      # created date: prefer 'created'/'date' frontmatter, else parse YYYYMMDD-HHMMSS prefix from filename
      $createdRaw = if ($fm.created) { $fm.created } elseif ($fm.date) { $fm.date } else { "" }
      $createdDt = $null
      if ($createdRaw -match '(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?') {
        $sec = if ($matches[6]) { $matches[6] } else { "00" }
        try { $createdDt = [datetime]("{0}-{1}-{2} {3}:{4}:{5}" -f $matches[1],$matches[2],$matches[3],$matches[4],$matches[5],$sec) } catch { $createdDt = $null }
      } elseif ($_.Name -match '^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})') {
        try { $createdDt = [datetime]("{0}-{1}-{2} {3}:{4}:{5}" -f $matches[1],$matches[2],$matches[3],$matches[4],$matches[5],$matches[6]) } catch { $createdDt = $null }
      }
      $msgs += [pscustomobject]@{ File=$_.Name; From=$fm.from; To=$fm.to; Type=$fm.type; Status=$fm.status; Ref=$fm.ref; Id=$fm.id; Priority=$fm.priority; Created=$createdDt }
    }
  }
}

Write-Host ("Total messages: {0}" -f $msgs.Count) -ForegroundColor Yellow

$answered = $msgs | Where-Object { $_.Type -eq "response" -and $_.Ref } | Select-Object -ExpandProperty Ref

# statuses that mean a message is closed / no longer needs action
$closedStatus = @("done","resolved","closed","ingested","merged","merged_observed","superseded","completed","done_with_concerns")

function Get-AgeString {
  param($Created)
  if (-not $Created) { return "?" }
  $span = (Get-Date) - $Created
  if ($span.TotalDays -ge 1) { return ("{0}d" -f [int]$span.TotalDays) }
  if ($span.TotalHours -ge 1) { return ("{0}h" -f [int]$span.TotalHours) }
  return ("{0}m" -f [int]$span.TotalMinutes)
}

# --- auth / external blockers ---
# Only OPEN, unanswered blockers: resolved ones (status done/closed/...) displayed forever
# as "Simon action needed" trained readers to ignore the section (2026-07-03 audit fix).
$blockers = $msgs | Where-Object { $_.Type -eq "blocker" -and ($closedStatus -notcontains $_.Status) -and ($answered -notcontains $_.Id) }
if ($blockers) {
  Write-Host "`n[AUTH / EXTERNAL BLOCKERS] (Simon action needed)" -ForegroundColor Magenta
  $blockers | Format-Table From,Status,File -AutoSize
}

# --- open consensus votes ---
$consReq = $msgs | Where-Object { $_.Type -eq "consensus_request" -and ($answered -notcontains $_.Id) }
$consVote = $msgs | Where-Object { $_.Type -eq "consensus_vote" }
if ($consReq) {
  Write-Host "`n[CONSENSUS OPEN] (voting in progress)" -ForegroundColor Cyan
  foreach ($r in $consReq) {
    $votes = ($consVote | Where-Object { $_.Ref -eq $r.Id }).From -join ", "
    Write-Host ("  {0}  votes: {1}" -f $r.File, ($(if ($votes) { $votes } else { "(none)" })))
  }
}

# --- wiki lessons pending ingest (Claude is the librarian; PROTOCOL.md s607) ---
if ($Me -eq "claude") {
  $actionableTypes = @("wiki_lesson","action_request","work_request")
  $pending = $msgs | Where-Object {
    ($_.To -eq "claude" -or $_.To -eq "all") -and
    ($actionableTypes -contains $_.Type) -and
    ($closedStatus -notcontains $_.Status) -and
    ($answered -notcontains $_.Id)
  } | Sort-Object Created
  if ($pending) {
    Write-Host "`n[WIKI LESSONS PENDING INGEST] (to:claude, not yet ingested/closed)" -ForegroundColor Yellow
    $pending |
      Select-Object @{N='Age';E={Get-AgeString $_.Created}},
                    @{N='Created';E={ if ($_.Created) { $_.Created.ToString('MM-dd HH:mm') } else { '?' } }},
                    From, Type, Status, File |
      Format-Table -AutoSize
  }
}

# --- inbox for -Me ---
if ($Me) {
  Write-Host ("`n=== inbox for {0} (open, unanswered requests) ===" -f $Me) -ForegroundColor Green
  $inbox = $msgs | Where-Object { ($_.To -eq $Me -or $_.To -eq "all") -and $_.Type -eq "request" -and $_.Status -eq "open" -and ($answered -notcontains $_.Id) } | Sort-Object Created
  if ($inbox) {
    $inbox |
      Select-Object @{N='Age';E={Get-AgeString $_.Created}},
                    @{N='Created';E={ if ($_.Created) { $_.Created.ToString('MM-dd HH:mm') } else { '?' } }},
                    From, Priority, Type, File |
      Format-Table -AutoSize
  } else { Write-Host "(empty)" }

  # --- physical inbox files (watchdog selffeedback / daemon reroute notes) ---
  # hub-watchdog + hub-daemon drop files into agents/<me>/inbox/ (not outbox), so the
  # outbox-only scan above never surfaced them (2026-07-03 audit: notes invisible for weeks).
  $inboxDir = Join-Path $root "agents\$Me\inbox"
  if (Test-Path $inboxDir) {
    $inboxFiles = Get-ChildItem $inboxDir -Filter *.md -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($inboxFiles) {
      Write-Host "`n[INBOX FILES] (agents/$Me/inbox - watchdog/daemon drops; delete or act, they self-replace)" -ForegroundColor Yellow
      $inboxFiles | Select-Object -First 10 | ForEach-Object { Write-Host ("  {0}  {1}" -f $_.LastWriteTime.ToString('MM-dd HH:mm'), $_.Name) }
      if ($inboxFiles.Count -gt 10) { Write-Host ("  ... and {0} more" -f ($inboxFiles.Count - 10)) }
    }
  }
}

# --- recent HTML reports (browser previews) ---
$previews = Get-ChildItem (Join-Path $root "agents") -Recurse -Filter *.html -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -match 'outbox\\preview' } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 5
if ($previews) {
  Write-Host "`n[RECENT HTML REPORTS]" -ForegroundColor DarkCyan
  $previews | ForEach-Object { Write-Host ("  {0}  {1}" -f $_.LastWriteTime.ToString('MM-dd HH:mm'), $_.Name) }
}
