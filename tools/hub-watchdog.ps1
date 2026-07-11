# hub-watchdog.ps1 -- the hub watches ITSELF and feeds problems to Claude automatically.
# Born from Simon's ask: "passing errors to you every time is tedious -- make the hub self-feedback."
# Instead of the user pasting the monitor when something looks wrong, this detects the real
# problems and drops a note into agents/claude/inbox/ so Claude's normal poll surfaces them.
#
# Dedup: a state file (tools/.watchdog-state.json) remembers what was already reported, so the
# same standing issue is not re-filed every run -- it re-files only if it persists past a cooldown
# or newly (re)appears, and auto-clears the note-marker when the issue resolves.
#
# Run standalone or from the HubWatchdog scheduled task (10min):
#   powershell -ExecutionPolicy Bypass -File tools/hub-watchdog.ps1            # check + file new issues
#   powershell -ExecutionPolicy Bypass -File tools/hub-watchdog.ps1 -Quiet     # no console, just file
param([switch]$Quiet, [switch]$NoAutoRestart, [int]$StaleMin = 35, [int]$CooldownMin = 120)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent
$toolsDir = $PSScriptRoot
$dlog = Join-Path $toolsDir 'hub-daemon.log'
$stateFile = Join-Path $toolsDir '.watchdog-state.json'
$inbox = Join-Path $root 'agents\claude\inbox'
function Now { Get-Date -Format 'yyyy-MM-dd HH:mm:ss' }
function NowStamp { Get-Date -Format 'yyyyMMdd-HHmmss' }

function Read-SharedLog([string]$path, [int]$tail = 0) {
  if (-not (Test-Path -LiteralPath $path)) { return @() }
  for ($i = 0; $i -lt 4; $i++) {
    try {
      $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
      try { $sr = New-Object System.IO.StreamReader($fs, [System.Text.UTF8Encoding]::new($false)); $text = $sr.ReadToEnd(); $sr.Close() }
      finally { $fs.Close() }
      $ls = @($text -split "`r?`n"); if ($tail -gt 0 -and $ls.Count -gt $tail) { $ls = $ls[($ls.Count - $tail)..($ls.Count - 1)] }
      return @($ls)
    } catch { Start-Sleep -Milliseconds 60 }
  }
  return @()
}

# ---- gather facts ----
$log = Read-SharedLog $dlog
$tail = if ($log.Count -gt 200) { $log[($log.Count - 200)..($log.Count - 1)] } else { $log }
$daemonAIs = @('codex','antigravity')  # grok removed 2026-06-18: request-only per ROUTING §4 (auto-loop produced ~96 hub commits / 0 live merges in AI-value eval; near-zero marginal value). Launch grok manually only when a specific decision needs consumer/X signal.
$aliveAIs = @()
try {
  Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'hub-daemon\.ps1' } |
    ForEach-Object { if ($_.CommandLine -match '-Only\s+(\w+)') { $aliveAIs += $matches[1] } }
} catch {}
$aliveAIs = @($aliveAIs | Select-Object -Unique)

$issues = @()   # each: @{ key; title; detail; action }

# (1) RUN STATE paused unexpectedly
$ctrl = Join-Path $root 'CONTROL.md'
$cs = $null
if (Test-Path $ctrl) {
  $cs = (Get-Content $ctrl -Raw)
  if ($cs -match '(?im)^\s*state\s*[:=]\s*paused') {
    $issues += @{ key='control-paused'; title='Hub CONTROL is paused'; detail='CONTROL.md state=paused -- daemons will skip work cycles.'; action='If unintended, set CONTROL state=running. If intended (migration/maintenance), ignore.' }
  }
} else {
  # 2026-07-04: fail CLOSED like the daemon (missing CONTROL = paused, hub-daemon reads it
  # the same way). Previously $cs stayed undefined and the restart gate below evaluated
  # "running", respawning daemons that then idle-skip forever - restarter/worker disagreed.
  $issues += @{ key='control-missing'; title='CONTROL.md is MISSING'; detail='Run-state semaphore file not found; daemons treat this as paused (fail-closed) and the watchdog now does too.'; action='Restore CONTROL.md from git (git checkout -- CONTROL.md) and set the intended state.' }
}

# (1.5) AUTO-RESTART dead daemons (self-healing, 2026-06-16 Simon "놀고 있는 놈들 일하게").
# A dead daemon = idle workers for HOURS (root cause of the 9h-stale AG seat). When the hub is
# RUNNING, revive any missing -Only lane right here. The hub-daemon per-lane mutex makes this
# idempotent (an already-alive lane's relaunch just exits as a duplicate), so it is safe to run
# every watchdog tick. Paused/draining => do NOT restart (respect the deliberate stop). Disable
# entirely with -NoAutoRestart. Requires the watchdog to run from its SCHEDULED TASK (HubWatchdog,
# 10min) so it fires even when the daemon-driven call path is dead.
$restarted = @()
if (-not $NoAutoRestart) {
  # Fail-closed (2026-07-04): restart ONLY on a positive state=running match, mirroring
  # hub-daemon.ps1 (missing/corrupt CONTROL => treated as paused, no restart).
  $isRunning = [bool]($cs -and ($cs -match '(?im)^\s*state\s*[:=]\s*"?running'))
  if ($isRunning) {
    $daemonScript = Join-Path $toolsDir 'hub-daemon.ps1'
    foreach ($a in $daemonAIs) {
      if ($aliveAIs -notcontains $a) {
        try {
          Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$daemonScript`" -Only $a -IntervalSec 600 -MaxTasksPerCycle 2" -WindowStyle Hidden
          $restarted += $a
          $aliveAIs += $a   # mutex dedups; next tick confirms it stayed up
        } catch {}
      }
    }
  }
}

# (2) daemon process not running. Auto-restarted lanes get an informational note instead of an alarm.
foreach ($a in $daemonAIs) {
  if ($restarted -contains $a) {
    $issues += @{ key="daemon-restarted-$a"; title="Daemon '$a' was down -- auto-restarted"; detail="hub-watchdog found no '$a' daemon and relaunched it (hub state=running)."; action="No action needed. If '$a' keeps needing restarts, tail hub-daemon.log to find why it dies." }
  } elseif ($aliveAIs -notcontains $a) {
    $issues += @{ key="daemon-down-$a"; title="Daemon '$a' is not running"; detail="No hub-daemon.ps1 -Only $a process alive (auto-restart skipped: hub paused or -NoAutoRestart)."; action="If intended, ignore. Else set CONTROL state=running, or relaunch via HUB-STARTUP.html." }
  }
}

# (3) daemon log not fresh while daemons alive = hung
if (Test-Path $dlog) {
  $age = ((Get-Date) - (Get-Item $dlog).LastWriteTime).TotalMinutes
  if ($aliveAIs.Count -gt 0 -and $age -gt $StaleMin) {
    $issues += @{ key='daemon-log-stale'; title='Daemon log stale while daemons alive'; detail=("hub-daemon.log last write {0:n0}m ago but {1} daemon(s) alive -- likely hung on a CLI call." -f $age, $aliveAIs.Count); action='Inspect tail of hub-daemon.log; if a CLI is wedged, safe-restart the daemons (the Start-Job timeout should prevent this).' }
  }
}

# (4) per-AI: real failure vs EXPECTED quota-backoff (do NOT flag expected backoff)
foreach ($a in $daemonAIs) {
  $backoff = @($tail | Select-String -Pattern ($a + " SKIP \(quota backoff") | Select-Object -Last 1)
  $exits = @($tail | Select-String -Pattern ("exit\(" + $a + "(?:/[^)]*)?\)=(-?\d+)\s*(\w+)?") -AllMatches | ForEach-Object { $_.Matches } | Select-Object -Last 3)
  if ($backoff) { continue }  # quota backoff is expected, not a fault
  if ($exits.Count -ge 3) {
    $bad = @($exits | Where-Object { [int]$_.Groups[1].Value -ne 0 })
    if ($bad.Count -eq $exits.Count) {
      $tags = (($exits | ForEach-Object { $_.Groups[1].Value + $(if ($_.Groups[2].Value) { '/' + $_.Groups[2].Value } else { '' }) }) -join ', ')
      $issues += @{ key="ai-failing-$a"; title="'$a' failing every recent cycle"; detail="Last 3 $a exits all nonzero ($tags) and NOT in quota backoff."; action="Spawn $a once manually to read the real error (see tool_headless_ai_spawn), or check its model in models.json is callable." }
    }
  }
}

# (5) backlog: an AI has >=3 items addressed to claude unprocessed (heuristic: open requests to claude in that AI's outbox)
# (light heuristic -- board.ps1 owns the real count; here we just notice an unusually deep claude inbox)
$claudeInboxOpen = @(Get-ChildItem $inbox -Filter *.md -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch 'selffeedback' })
if ($claudeInboxOpen.Count -ge 12) {
  $issues += @{ key='claude-inbox-deep'; title="Claude inbox is deep ($($claudeInboxOpen.Count) items)"; detail='Many unprocessed items addressed to Claude.'; action='Run tools/board.ps1 -Me claude and clear/triage; archive resolved items.' }
}

# (6) REMOTE ORDERS channel unconsumed (2026-07-03 audit: 12-day outage went undetected).
# The channel's consumer is an interactive Claude /loop session (SPOF) that dies silently with
# the session. Detect: orders waiting (newCount>0) while the CONSUMER heartbeat (written only
# by orders-poll -Heartbeat, i.e. the director loop) is missing/old -> tell Claude+Simon.
try {
  $pollOut = powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $toolsDir 'orders-poll.ps1') -Json 2>$null
  $poll = $null; try { $poll = $pollOut | ConvertFrom-Json } catch {}
  if ($poll -and $poll.error) {
    $issues += @{ key='orders-channel-error'; title='Remote ORDERS channel broken'; detail="orders-poll error: $($poll.error)"; action='Check E:\2ndB clone + network; run tools/orders-poll.ps1 manually.' }
  } elseif ($poll) {
    $hb = Join-Path $toolsDir 'orders-poll-heartbeat.txt'
    $hbAgeMin = if (Test-Path $hb) { ((Get-Date) - (Get-Item $hb).LastWriteTime).TotalMinutes } else { [double]::MaxValue }
    # (6a) orders WAITING with a dead/absent consumer = the real-harm case (an idle queue with a
    # stale heartbeat is normal session-bound-consumer behavior, NOT an outage -- do not alert on it).
    if ([int]$poll.newCount -gt 0 -and $hbAgeMin -gt 30) {
      $hbTxt = if (Test-Path $hb) { "consumer heartbeat {0:n0}m old" -f $hbAgeMin } else { 'no consumer heartbeat file (no director /loop has ever polled with -Heartbeat)' }
      $issues += @{ key='orders-unconsumed'; title="Simon's remote order(s) waiting with NO consumer (O-$($poll.newIds -join ', O-'))"; detail="ORDERS.md has $($poll.newCount) unconsumed order(s); $hbTxt. The remote-order pipeline is effectively DOWN."; action='Start the Claude /loop director session (HUB-STARTUP.html remote-orders card) or handle the order directly, then have the loop poll with -Heartbeat.' }
    }
    # (6b, audit E2b) ABANDONED in-progress: an order was acked (picked up, in tools/orders-ack.json)
    # but never reached ## DONE while the consumer heartbeat went stale -> the director died mid-task
    # and the ack ledger now hides that order from newIds FOREVER (it never re-surfaces as NEW). This
    # requires a genuinely-acked order, so it is not the idle-death false alarm -- real work was dropped.
    $abandoned = @($poll.ackedIds | Where-Object { ($poll.openIds -contains $_) -and ($poll.doneIds -notcontains $_) })
    if ($abandoned.Count -gt 0 -and $hbAgeMin -gt 30) {
      $issues += @{ key='orders-abandoned'; title="Acked order(s) abandoned in-progress (O-$($abandoned -join ', O-'))"; detail="Picked up (ack ledger) but never moved to ## DONE, and the consumer heartbeat is $([int]$hbAgeMin)m stale -- the director died mid-task and the ack ledger now hides them from new-order detection, so they will NOT re-surface on their own."; action="Handle O-$($abandoned -join ', O-') directly, then move them to ## DONE or clear their ids from tools/orders-ack.json." }
    }
  }
} catch {}

# (7) hub HEAD off master (BRANCH-ALERT): commits are landing on a stray branch; HubBackup
# pushes master only, so off-master work is NOT backed up (2026-07-02 incident, 206 commits).
try {
  $curBranch = (git -C $root rev-parse --abbrev-ref HEAD 2>$null)
  if ($curBranch -and $curBranch -ne 'master') {
    $issues += @{ key='hub-head-off-master'; title="Hub HEAD is on '$curBranch' (must be master)"; detail='A CLI checked out a branch in the shared hub tree. Commits are missing master and the off-machine backup.'; action='git checkout master; git merge --ff-only <branch>; git branch -d <branch>. The daemon BRANCH-HEAL also repairs this when the tree is clean.' }
  }
} catch {}

# (8) PUSH PATH health (2026-07-04 restore audit): local commits must reach origin (comm-hub).
# Detect a dead/rotting push path: master far ahead of the origin/master ref (HubBackup dead,
# push rejected non-FF, or divergence) or the HubBackup scheduled task missing on this machine.
try {
  $ahead = 0
  $aheadRaw = git -C $root rev-list --count origin/master..master 2>$null
  if ($aheadRaw -match '^\d+$') { $ahead = [int]$aheadRaw }
  if ($ahead -ge 15) {
    $issues += @{ key='push-stale'; title="Hub master is $ahead commits ahead of origin"; detail='Local hub commits are not reaching the comm-hub remote (HubBackup dead, rejected push, or divergence). They pile up locally and are not backed up off-machine.'; action='Run tools/hub-backup.ps1 manually and read tools/hub-backup.log; if the push is rejected non-fast-forward, Claude must git fetch + merge origin/master (never force), then push.' }
  }
  $bkTask = $null
  try { $bkTask = Get-ScheduledTask -TaskName 'HubBackup' -ErrorAction SilentlyContinue } catch {}
  if (-not $bkTask) {
    $issues += @{ key='hubbackup-task-missing'; title='HubBackup scheduled task is missing on this machine'; detail='Nothing pushes hub master to origin automatically; daemon commits accumulate locally with no off-machine backup.'; action='Re-register the HubBackup task pointing at tools/hub-backup.ps1 (launch via pwsh; the script contains Korean literals that powershell.exe 5.1 mojibakes).' }
  }
} catch {}

# (9) grok is request-only (no standing lane, ROUTING Sec.4): an OPEN request addressed to grok
# has NO automated server - dispatch-oneshot's hidden spawn already died silently once (07-03).
# File a note so Claude spawns `hub-daemon.ps1 -Only grok -MaxCycles 1` or handles it directly.
# (Note only, no auto-spawn: this scan is not ref-aware, so an already-answered stale row must
# not trigger respawn ping-pong; the note's cooldown dedupe keeps it quiet.)
try {
  if ($aliveAIs -notcontains 'grok') {
    $grokOpen = 0
    Get-ChildItem (Join-Path $root 'agents') -Directory -ErrorAction SilentlyContinue | ForEach-Object {
      $ob = Join-Path $_.FullName 'outbox'
      if (Test-Path $ob) {
        Get-ChildItem $ob -Filter *.md -File -ErrorAction SilentlyContinue | ForEach-Object {
          $h = Get-Content $_.FullName -TotalCount 14 -ErrorAction SilentlyContinue
          if (($h -match '^to:\s*"?grok') -and ($h -match '^type:\s*"?request') -and ($h -match '^status:\s*"?open')) { $grokOpen++ }
        }
      }
    }
    if ($grokOpen -gt 0) {
      $issues += @{ key='grok-order-waiting'; title="$grokOpen open request(s) addressed to grok with no server"; detail='grok is request-only (excluded from default lanes); nothing serves its queue automatically.'; action='Spawn once: powershell -ExecutionPolicy Bypass -File tools/hub-daemon.ps1 -Only grok -MaxCycles 1 (its ref-aware counter + NO-OP rule make this safe), or answer/close the request as Claude.' }
    }
  }
} catch {}

# ---- dedup against state ----
$state = @{}
if (Test-Path $stateFile) { try { (Get-Content $stateFile -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $state[$_.Name] = $_.Value } } catch {} }
# DateTimeOffset: PS5.1's `-UFormat %s` is LOCAL-time epoch while pwsh's is UTC -- a 9h skew
# on this KST box corrupted the cooldown ledger depending on which host last wrote it.
$nowEpoch = [DateTimeOffset]::Now.ToUnixTimeSeconds()
$activeKeys = @($issues | ForEach-Object { $_.key })
$filed = @()
foreach ($iss in $issues) {
  $prev = $state[$iss.key]
  $cooldownOk = (-not $prev) -or (($nowEpoch - [int]$prev) -gt ($CooldownMin * 60))
  if ($cooldownOk) {
    # write a self-feedback note into Claude's inbox
    $stamp = NowStamp
    # 자기증식 방지: 같은 이슈 키의 이전 selffeedback 노트를 먼저 제거(키당 최대 1건 유지 → inbox 적체 방지)
    Get-ChildItem $inbox -Filter "*-selffeedback-$($iss.key).md" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    $file = Join-Path $inbox "$stamp-selffeedback-$($iss.key).md"
    $body = @"
---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: $stamp-selffeedback-$($iss.key)
created: $(Now) KST
---

# [self-feedback] $($iss.title)

[$(Now) KST] The hub detected this on its own (no user paste needed).

- **Issue**: $($iss.detail)
- **Suggested action**: $($iss.action)

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a ${CooldownMin}m cooldown if unresolved. Delete this note once handled.)
"@
    [System.IO.File]::WriteAllText($file, $body, (New-Object System.Text.UTF8Encoding $false))  # UTF-8 no-BOM (PS5.1 -Encoding utf8 adds BOM -> hub-health FAIL)
    $state[$iss.key] = $nowEpoch
    $filed += $iss.key
  }
}
# clear resolved keys from state so they can re-fire fresh next time
$resolved = @($state.Keys | Where-Object { $activeKeys -notcontains $_ })
foreach ($k in $resolved) { $state.Remove($k) }
[System.IO.File]::WriteAllText($stateFile, ($state | ConvertTo-Json), (New-Object System.Text.UTF8Encoding $false))  # UTF-8 no-BOM (#3 fix)

if (-not $Quiet) {
  Write-Host "[hub-watchdog $(Now) KST] issues=$($issues.Count)  filed=$($filed.Count)  resolved-cleared=$($resolved.Count)" -ForegroundColor $(if ($issues.Count) { 'Yellow' } else { 'Green' })
  foreach ($iss in $issues) { $mark = $(if ($filed -contains $iss.key) { 'FILED' } else { 'cooldown' }); Write-Host "  [$mark] $($iss.title)" }
}
