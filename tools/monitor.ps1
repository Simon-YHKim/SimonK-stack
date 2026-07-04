# monitor.ps1 -- Live AI Hub dashboard for the user's VS Code terminal (read-only).
# Shows CONTROL run-state, each AI's STATUS (state / freshness / WORKING-now / live procs /
# pending-for-Claude), daemon liveness, emulator status, inbox & blocker counts, open
# consensus, recent hub commits. Auto-refreshes so Simon can watch the 4-AI loops live.
# ASCII-only source (PS 5.1 no-BOM safe).
#
# Usage (VS Code terminal, cwd = hub root):
#   powershell -ExecutionPolicy Bypass -File "tools/monitor.ps1"          # live, 5s refresh
#   powershell -ExecutionPolicy Bypass -File "tools/monitor.ps1" -Interval 3
#   powershell -ExecutionPolicy Bypass -File "tools/monitor.ps1" -Once    # single render
param([int]$Interval = 5, [switch]$Once)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$root   = Split-Path $PSScriptRoot -Parent
$agents = @("claude","codex","antigravity","grok")
# Per-AI commit identity (commit.ps1). Git-author time is an AUTOMATIC freshness signal that
# does not depend on STATUS.md discipline -- Claude works via commits/BOARD, not a daemon that
# rewrites its own STATUS each cycle, so STATUS alone made the orchestrator look idle for hours.
$agentEmail = @{ claude='claude@2nd-b.ai'; codex='codex@2nd-b.ai'; antigravity='antigravity@2nd-b.ai'; grok='grok@2nd-b.ai' }
# CLI process names that represent a live "agent" for each AI (best-effort; codex spawns node
# children, gemini is the AG seat). Used for the "procs" column = how many are running now.
$agentProc  = @{ claude=@('claude'); codex=@('Codex','codex'); antigravity=@('gemini'); grok=@('grok') }
# Pending-for-Claude alarm: when an AI has >= this many unprocessed outputs awaiting Claude,
# the merge-gate is falling behind (Simon's rule: 3+ piled up => Claude likely not processing).
$PENDING_ALARM = 3

# Read a log the daemon may be appending to RIGHT NOW. Plain Get-Content crashes with
# "file in use by another process" during the daemon's append window; open with
# FileShare.ReadWrite + retry so the monitor never dies on that race (was: blank daemon
# line + cyc=0 for every AI because the dlog read threw).
function Read-SharedLog([string]$path, [int]$tail = 0) {
  if(-not (Test-Path -LiteralPath $path)){ return @() }
  for($i=0; $i -lt 4; $i++){
    try {
      $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
      try { $sr = New-Object System.IO.StreamReader($fs, [System.Text.UTF8Encoding]::new($false)); $text = $sr.ReadToEnd(); $sr.Close() }
      finally { $fs.Close() }
      $lines = @($text -split "`r?`n")
      if($tail -gt 0 -and $lines.Count -gt $tail){ $lines = $lines[($lines.Count-$tail)..($lines.Count-1)] }
      return @($lines)
    } catch { Start-Sleep -Milliseconds 60 }
  }
  return @()
}

function Get-Front([string[]]$lines,[string]$key){
  $pat = "^" + $key + ':\s*"?(.*?)"?\s*$'
  $m = $lines | Select-String -Pattern $pat | Select-Object -First 1
  if($m){ return $m.Matches[0].Groups[1].Value }
  return ""
}
function Get-Age([string]$stamp){
  $s = ($stamp -replace 'KST','' -replace '/','' -replace '\s+',' ').Trim()
  try {
    $t = [datetime]::Parse($s)
    $d = (Get-Date) - $t
    if($d.TotalMinutes -lt 1){ return ("{0:n0}s ago" -f $d.TotalSeconds) }
    if($d.TotalHours   -lt 1){ return ("{0:n0}m ago" -f $d.TotalMinutes) }
    if($d.TotalDays    -lt 1){ return ("{0:n0}h ago" -f $d.TotalHours) }
    return ("{0:n0}d ago" -f $d.TotalDays)
  } catch { return "?" }
}
function Get-GitLastByAuthor([string]$rootDir,[string]$email){
  if(-not $email){ return $null }
  $iso = git -C $rootDir log -1 --author="$email" --format='%cI' 2>$null
  if($iso){ try { return [datetime]::Parse($iso) } catch { return $null } }
  return $null
}
function Get-ProcCount([string[]]$names){
  $n = 0
  foreach($nm in ($names | Select-Object -Unique)){
    try { $n += @(Get-Process -Name $nm -ErrorAction SilentlyContinue).Count } catch {}
  }
  return $n
}

function Render {
  $now = Get-Date -Format 'yyyy-MM-dd / HH:mm:ss'
  $bar = ("=" * 78)
  Write-Host $bar -ForegroundColor Cyan
  Write-Host ("  AI HUB MONITOR     {0} KST     refresh {1}s  (Ctrl+C to stop)" -f $now,$Interval) -ForegroundColor Cyan
  Write-Host $bar -ForegroundColor Cyan

  $control = Join-Path $root "CONTROL.md"
  $controlState = ""
  if(Test-Path $control){
    $ch = Get-Content $control -Encoding UTF8 -TotalCount 12
    $st = Get-Front $ch 'state'
    $controlState = $st
    $rs = Get-Front $ch 'pause_reason'
    $col = if($st -eq 'running'){'Green'}elseif($st -eq 'paused'){'Red'}else{'Yellow'}
    Write-Host ("RUN STATE: {0}" -f $st.ToUpper()) -ForegroundColor $col
    if($rs){ Write-Host ("  reason: {0}" -f $rs.Substring(0,[Math]::Min(68,$rs.Length))) -ForegroundColor DarkGray }
  }

  # ---- Daemon liveness: which hub-daemon.ps1 loops are alive + the shared log heartbeat ----
  $dproc = @()
  try {
    $dproc = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -match 'hub-daemon\.ps1' })
  } catch {}
  $dAIs = @()
  foreach($dp in $dproc){ if($dp.CommandLine -match '-Only\s+(\w+)'){ $dAIs += $matches[1] } }
  $dAIs = @($dAIs | Select-Object -Unique)
  $dlog = Join-Path $root "tools\hub-daemon.log"
  $dlogLines = @()
  if(Test-Path $dlog){ $dlogLines = Read-SharedLog $dlog 120 }
  # ---- Per-AI cycle counts (how many loops each AI has run) ----
  # Daemon AIs (codex/antigravity/grok): count completed cycles = "exit(<ai>)=" in the FULL
  # shared daemon log (lifetime, survives restarts). Claude has no daemon, so a Claude
  # orchestration cycle = a BOARD r-round (unique r<N> tokens across Claude hub commit subjects).
  $dlogFull = @()
  if(Test-Path $dlog){ $dlogFull = Read-SharedLog $dlog 0 }
  $cycles = @{}
  foreach($a in $agents){
    if($a -eq 'claude'){
      $rs = @(git -C $root log --author="$($agentEmail['claude'])" --format='%s' 2>$null |
              Select-String -Pattern '\br\d+\b' -AllMatches |
              ForEach-Object { $_.Matches } | ForEach-Object { $_.Value } | Select-Object -Unique)
      $cycles['claude'] = $rs.Count
    } else {
      $cycles[$a] = @($dlogFull | Select-String -Pattern ("exit\(" + $a + "(?:/|\))")).Count
    }
  }
  if($dlogLines.Count -gt 0){
    # Last REAL line: the split keeps a trailing empty element after the final newline,
    # so [-1] was always "" and the timestamp regex never matched (DAEMON row never green).
    $dlast = @($dlogLines | Where-Object { $_ -match '^\[' }) | Select-Object -Last 1
    if(-not $dlast){ $dlast = "" }
    $dts = ""; if($dlast -match '^\[([^\]]+) KST\]'){ $dts = $matches[1] }
    $dage = if($dts){ Get-Age $dts } else { "?" }
    $dmsg = ($dlast -replace '^\[[^\]]*\]\s*','').Trim()
    # P0: green requires BOTH a fresh log AND a LIVE daemon process. A fresh log with no live
    # PID is the "stale-log illusion" (daemon died, log just looks recent) -> not green.
    $dcol = if(($dage -match 's ago|m ago') -and ($dproc.Count -gt 0)){'Green'}elseif($dproc.Count -gt 0){'Yellow'}else{'Red'}
    $daemonTag = if($dAIs.Count -gt 0){ ("loops: " + ($dAIs -join ' ') + " (" + $dAIs.Count + ")") } else { "loops: NONE (no live PID)" }
    Write-Host ("DAEMON  {0,-10}{1,-40}{2}" -f $dage,($dmsg.Substring(0,[Math]::Min(38,$dmsg.Length))),$daemonTag) -ForegroundColor $dcol
  } else {
    Write-Host "DAEMON  (no hub-daemon.log -- launch tools/hub-daemon.ps1)" -ForegroundColor DarkGray
  }

  # ---- Emulator / device line (Q3 visibility) ----
  $emuProc = 0; $adbProc = 0
  try { $emuProc = @(Get-Process -Name 'qemu-system-x86_64','emulator' -ErrorAction SilentlyContinue).Count } catch {}
  try { $adbProc = @(Get-Process -Name 'adb' -ErrorAction SilentlyContinue).Count } catch {}
  $appdir = "E:\2ndB"
  $headStr = ""
  if(Test-Path $appdir){
    $ahead = git -C $appdir rev-parse --short HEAD 2>$null
    $asub  = git -C $appdir log -1 --format='%s' 2>$null
    if($ahead){ $headStr = ("2nd-B " + $ahead + "  " + $(if($asub){$asub.Substring(0,[Math]::Min(34,$asub.Length))}else{""})) }
  }
  if($emuProc -gt 0){
    Write-Host ("EMULATOR running (qemu" + $(if($adbProc -gt 0){"+adb"}else{" no-adb"}) + ")   |  " + $headStr) -ForegroundColor Green
  } else {
    Write-Host ("EMULATOR down (no qemu)   |  " + $headStr) -ForegroundColor DarkGray
  }
  Write-Host ("-" * 78) -ForegroundColor DarkGray

  # ---- Pre-scan all outbox messages once (used for pending/inbox/blockers) ----
  $msgs = @()
  foreach($a in $agents){
    $obx = Join-Path $root ("agents\" + $a + "\outbox")
    if(Test-Path $obx){
      Get-ChildItem $obx -Filter *.md -File -ErrorAction SilentlyContinue | ForEach-Object {
        $h = Get-Content $_.FullName -Encoding UTF8 -TotalCount 15
        $fm = @{}
        foreach($l in $h){ if($l -match '^(from|to|type|ref|status|id|priority):\s*"?(.*?)"?\s*$'){ $fm[$matches[1]] = $matches[2] } }
        $subj = $_.BaseName -replace '^\d{8}-\d{6}-(to-[a-z]+-)?',''
        $msgs += [pscustomobject]@{ From=$fm.from; To=$fm.to; Type=$fm.type; Status=$fm.status; Ref=$fm.ref; Id=$fm.id; Pri=$fm.priority; Subj=$subj }
      }
    }
  }
  $answered = $msgs | Where-Object { $_.Ref } | Select-Object -ExpandProperty Ref
  # Pending-for-Claude per AI = hub commits by that AI SINCE Claude's last hub commit. Simon's
  # rule: 3+ commits piled up means Claude (merge-gate) likely is not processing. This self-
  # clears the instant Claude commits (merge+feedback), so a rising count = a real stall signal,
  # not lifetime backlog (an outbox-status count over-counted because old reports stay open).
  $claudeLastIso = git -C $root log -1 --author="claude@2nd-b.ai" --format='%cI' 2>$null
  $claudeLast = $null
  if($claudeLastIso){ try { $claudeLast = [datetime]::Parse($claudeLastIso) } catch {} }
  $pending = @{}
  foreach($a in $agents){
    if($a -eq 'claude'){ $pending[$a] = 0; continue }
    $cnt = if($claudeLast){
      git -C $root rev-list --count --author="$($agentEmail[$a])" --since="$($claudeLast.ToString('yyyy-MM-dd HH:mm:ss'))" HEAD 2>$null
    } else {
      git -C $root rev-list --count --author="$($agentEmail[$a])" HEAD 2>$null
    }
    $pending[$a] = [int](@($cnt)[0])
  }

  # ---- Per-AI rows: state | fresh | WORKING-now | procs | pend>CL | activity ----
  Write-Host ("{0,-11}{1,-9}{2,-9}{3,-9}{4,-6}{5,-6}{6,-8}{7}" -f "AI","state","fresh","now","procs","cyc","pend>CL","last activity") -ForegroundColor White
  $alarms = @()
  foreach($a in $agents){
    $sf = Join-Path $root ("agents\" + $a + "\STATUS.md")
    $state = "-"; $age = "-"; $act = ""; $rawState = ""; $stale = $false
    if(Test-Path $sf){
      $lines = Get-Content $sf -Encoding UTF8
      $head = $lines | Select-Object -First 8
      $rawState = Get-Front $head 'state'
      $state = $rawState; if(-not $state){ $state = "-" }
      if($state.Length -gt 8){ $state = $state.Substring(0,8) }
      $upd = Get-Front $head 'updated'
      $best = (Get-Item $sf).LastWriteTime
      if($upd){ try { $ut=[datetime]::Parse((($upd -replace 'KST','' -replace '/','' -replace '\s+',' ').Trim())); if($ut -gt $best){ $best=$ut } } catch {} }
      $gl = Get-GitLastByAuthor $root $agentEmail[$a]
      if($gl -and $gl -gt $best){ $best = $gl }
      # P0: daemon-driven AIs publish a real transcript to tools/live/<ai>.log each cycle. Its
      # mtime is an HONEST freshness signal that replaces the removed fake STATUS heartbeat --
      # without it, removing the heartbeat would make daemon AIs look stale.
      if($a -ne 'claude'){
        $ll = Join-Path $root ("tools\live\" + $a + ".log")
        if(Test-Path -LiteralPath $ll){ $lt = (Get-Item -LiteralPath $ll).LastWriteTime; if($lt -gt $best){ $best = $lt } }
      }
      $d = (Get-Date) - $best
      if($d.TotalSeconds -lt 0){ $d = [TimeSpan]::Zero }
      if($d.TotalMinutes -lt 1){ $age = ("{0:n0}s ago" -f $d.TotalSeconds) }
      elseif($d.TotalHours -lt 1){ $age = ("{0:n0}m ago" -f $d.TotalMinutes) }
      elseif($d.TotalDays -lt 1){ $age = ("{0:n0}h ago" -f $d.TotalHours) }
      else { $age = ("{0:n0}d ago" -f $d.TotalDays) }
      $stale = ($d.TotalDays -gt 1)
      $idx = -1
      for($i=0;$i -lt $lines.Count;$i++){ if($lines[$i] -match '^\[\d{4}-\d{2}-\d{2}'){ $idx = $i; break } }
      if($idx -ge 0){
        $act = ($lines[$idx] -replace '^\[[^\]]*\]\s*','').Trim()
        if(-not $act -and ($idx+1) -lt $lines.Count){ $act = $lines[$idx+1].Trim() }
      }
    }
    # WORKING-now: in the shared daemon log, is this AI's last "-> $a poll" more recent than its
    # last "exit($a)="? If so a CLI run is in flight right now; else it's idle between cycles.
    $nowState = "-"
    if($a -ne 'claude'){
      # WORKING/idle only mean something if this AI's daemon is actually ALIVE. Otherwise a
      # daemon killed mid-cycle leaves a dangling "-> poll" with no "exit(" and would falsely
      # read WORKING forever -- so a dead daemon is always no-daemon regardless of the log tail.
      if($dAIs -contains $a){
        $lastPoll = -1; $lastExit = -1; $lastExitCode = 0; $lastTimeout = -1
        for($i=0;$i -lt $dlogLines.Count;$i++){
          if($dlogLines[$i] -match ("->\s+" + $a + "\s+poll")){ $lastPoll = $i }
          if($dlogLines[$i] -match ("exit\(" + $a + "(?:/[^)]*)?\)=(-?\d+)")){ $lastExit = $i; $lastExitCode = [int]$matches[1] }
          if($dlogLines[$i] -match ("TIMEOUT\(" + $a + "\)")){ $lastTimeout = $i }
        }
        # A non-zero last exit (bad model id, untrusted folder, CLI error) means the daemon is
        # spinning but the AI is PRODUCING NOTHING -- show ERR so a fresh-looking-but-broken AI
        # is not mistaken for healthy, and a stale one is explained ("fresh growing by hours").
        if($lastPoll -ge 0 -and $lastPoll -gt $lastExit -and $lastPoll -gt $lastTimeout){ $nowState = "WORKING" }
        elseif($lastTimeout -gt $lastExit){ $nowState = "TIMEOUT" }
        elseif($lastExitCode -ne 0){ $nowState = "ERR" }
        else { $nowState = "idle" }
      } else {
        $nowState = "no-daemon"
      }
    } else {
      $nowState = "loop"
    }
    $procN = Get-ProcCount $agentProc[$a]
    $cycN = [int]$cycles[$a]
    $pendN = $pending[$a]
    $pendStr = "$pendN"
    if($pendN -ge $PENDING_ALARM){ $pendStr = "$pendN!!"; $alarms += "$a $pendN" }

    $runlike = ($rawState -match '^\s*running')
    if($runlike -and ($controlState -eq 'paused')){ $state = "stale-run?" }
    elseif($runlike -and $stale){ $state = "STALE" }
    if($act.Length -gt 30){ $act = $act.Substring(0,29) + "~" }
    $live = ($age -match 's ago|m ago') -and -not $stale
    $rowcol =
      if($pendN -ge $PENDING_ALARM){'Red'}
      elseif($nowState -eq 'WORKING'){'Green'}
      elseif($nowState -eq 'ERR' -or $nowState -eq 'TIMEOUT'){'Red'}
      elseif($state -eq 'stale-run?' -or $state -eq 'STALE' -or $nowState -eq 'no-daemon'){'Yellow'}
      elseif($state -eq 'paused' -or $rawState -match '^\s*paused'){'DarkGray'}
      elseif($live){'Gray'}
      else{'Gray'}
    Write-Host ("{0,-11}{1,-9}{2,-9}{3,-9}{4,-6}{5,-6}{6,-8}{7}" -f $a,$state,$age,$nowState,$procN,$cycN,$pendStr,$act) -ForegroundColor $rowcol
  }
  Write-Host ("-" * 78) -ForegroundColor DarkGray

  # ---- Backlog alarm line (Simon: 3+ unprocessed per AI => Claude behind) ----
  if($alarms.Count -gt 0){
    Write-Host ("!! BACKLOG ALARM -- Claude behind on: " + ($alarms -join ' , ') + "  (>= $PENDING_ALARM unprocessed; merge/ack now)") -ForegroundColor Red
  } else {
    Write-Host "backlog: clear (no AI >= $PENDING_ALARM unprocessed for Claude)" -ForegroundColor DarkGreen
  }

  # ---- Inbox / blockers / open requests ----
  $inboxStr = ($agents | ForEach-Object {
    $me = $_
    $n = ($msgs | Where-Object { ($_.To -eq $me -or $_.To -eq 'all') -and $_.Type -eq 'request' -and $_.Status -eq 'open' -and ($answered -notcontains $_.Id) }).Count
    ("{0}:{1}" -f $me.Substring(0,[Math]::Min(2,$me.Length)), $n)
  }) -join "  "
  $openBlockers = @($msgs | Where-Object { $_.Type -eq 'blocker' -and ($_.Status -notmatch 'closed|resolved|done') -and ($answered -notcontains $_.Id) })
  $blk  = $openBlockers.Count
  $cons = ($msgs | Where-Object { $_.Type -eq 'consensus_request' -and ($answered -notcontains $_.Id) }).Count
  Write-Host ("inbox  {0}    blockers:{1}    consensus open:{2}" -f $inboxStr,$blk,$cons) -ForegroundColor $(if($blk -gt 0){'Magenta'}else{'Gray'})
  $open = $msgs | Where-Object { $_.Type -eq 'request' -and $_.Status -eq 'open' -and ($answered -notcontains $_.Id) } | Select-Object -First 6
  foreach($o in $open){
    $os = if($o.Subj){ $o.Subj } else { "" }
    Write-Host ("   -> {0,-11}[{1,-4}] {2}" -f $o.To,$o.Pri,$os.Substring(0,[Math]::Min(46,$os.Length))) -ForegroundColor DarkCyan
  }
  $blocks = $openBlockers | Select-Object -First 4
  foreach($b in $blocks){
    $bs = if($b.Subj){ $b.Subj } else { "" }
    Write-Host ("   !! blocker <- {0}: {1}" -f $b.From,$bs.Substring(0,[Math]::Min(44,$bs.Length))) -ForegroundColor Magenta
  }
  Write-Host ("-" * 78) -ForegroundColor DarkGray

  Write-Host "recent hub commits:" -ForegroundColor DarkCyan
  $log = git -C $root log -8 --format='%cd|%an|%s' --date=format:'%m-%d %H:%M' 2>$null
  if($log){
    $log | ForEach-Object {
      $p = $_.Split('|',3)
      Write-Host ("  {0}  {1,-12} {2}" -f $p[0],$p[1],$p[2].Substring(0,[Math]::Min(48,$p[2].Length))) -ForegroundColor Gray
    }
  } else { Write-Host "  (no git log)" -ForegroundColor DarkGray }

  $prev = Get-ChildItem (Join-Path $root "agents") -Recurse -Filter *.html -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match 'outbox\\preview' } | Sort-Object LastWriteTime -Descending | Select-Object -First 3
  if($prev){
    Write-Host "`nrecent HTML reports:" -ForegroundColor DarkCyan
    $prev | ForEach-Object { Write-Host ("  {0}  {1}" -f $_.LastWriteTime.ToString('MM-dd HH:mm'),$_.Name) -ForegroundColor Gray }
  }
}

if($Once){ Render; return }
try {
  while($true){ Clear-Host; Render; Start-Sleep -Seconds $Interval }
} catch [System.Management.Automation.PipelineStoppedException] { }
finally { Write-Host "`n[monitor stopped]" -ForegroundColor DarkGray }
