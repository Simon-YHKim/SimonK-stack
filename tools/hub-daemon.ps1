# hub-daemon.ps1 -- Autonomous 4-AI hub driver (PROTOCOL section 12/19/35.4).
# Makes Codex/Grok (and optionally Antigravity) keep investigating on their own:
# each cycle it asks every AI to read its inbox + do the next task in its lane + commit.
# Freshness is REAL, not faked: each AI's tools/live/<ai>.log (real transcript+mtime) and its
# git author time drive the monitor. The daemon runs cycles only while CONTROL.state==running
# (section 13), and each CLI call is bounded by -PerAITimeoutSec so one hung CLI can't stall
# the whole sequential loop. Claude stays the merge gate; AIs never push 2nd-B (branch/outbox only).
#
# Why sequential: the hub is a LOCAL-ONLY shared git tree. One git writer at a
# time avoids .git index.lock races (commit.ps1 has no lock-retry). No fetch/pull
# needed -- every AI shares the same working directory.
#
# Launch (background, this session):
#   powershell -ExecutionPolicy Bypass -File tools/hub-daemon.ps1
#   powershell -ExecutionPolicy Bypass -File tools/hub-daemon.ps1 -IntervalSec 300 -IncludeAG
#   powershell -ExecutionPolicy Bypass -File tools/hub-daemon.ps1 -MaxCycles 1   # single test cycle
# Stop: kill the background task (TaskStop) or Ctrl+C in its terminal.
param(
  [int]$IntervalSec = 600,         # default 10min (Simon: all loops 10min)
  [int]$MaxCycles = 0,             # 0 = run forever
  [int]$MaxTasksPerCycle = 1,      # anti-idle: drain up to N OPEN orders per cycle before sleeping
  [int]$PerAITimeoutSec = 1200,    # hard ceiling per CLI call; a hung CLI is killed + skipped (P0: hung CLI stalled the whole sequential loop forever)
  [switch]$IncludeAG,              # add antigravity (agy seat) to the default codex,grok loop
  [string[]]$Only = @()            # run ONLY these AIs (e.g. -Only antigravity for a separate slow AG loop)
)
$ErrorActionPreference = 'Continue'
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8
$root = Split-Path $PSScriptRoot -Parent
$daemonLog = Join-Path $root "tools\hub-daemon.log"

function Now { Get-Date -Format 'yyyy-MM-dd HH:mm:ss' }
function Log([string]$m){
  # Lane label: two lane daemons (-Only codex / -Only antigravity) interleave in ONE log
  # with independent cycle counters -- unlabeled lines made forensics guesswork.
  $line = "[$(Now) KST] [$(if($script:laneKey){$script:laneKey}else{'?'})] $m"
  Write-Host $line
  # Shared append: open with FileShare.ReadWrite so monitor/feed/hub-health can read the
  # log WHILE we write it. Add-Content's default sharing locked readers out mid-append,
  # which is what crashed the dashboards ("file in use by another process"). Retry a few
  # times in case another daemon instance is appending the same instant.
  # Cross-process append mutex (2026-07-04): TWO lane daemons appending the same instant
  # tore lines (orphan fragments like "axCycles=0"/"EGIN" observed 07-04 15:41) because
  # FileMode::Append is seek-to-end-at-open, not atomic O_APPEND. A torn "cycle exit" line
  # can hide a failure sample from the watchdog's exit-code scan. Serialize appends.
  $lm = $null
  try { $lm = New-Object System.Threading.Mutex($false, "Global\hubdaemonlog"); [void]$lm.WaitOne(3000) } catch {}
  for($i=0;$i -lt 4;$i++){
    try {
      $fs = [System.IO.File]::Open($daemonLog, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
      try { $sw = New-Object System.IO.StreamWriter($fs, $utf8); $sw.WriteLine($line); $sw.Flush(); $sw.Close() }
      finally { $fs.Close() }
      break
    } catch { Start-Sleep -Milliseconds 50 }
  }
  if($lm){ try { $lm.ReleaseMutex() } catch {}; try { $lm.Dispose() } catch {} }
}

# Kill every descendant process of THIS daemon (used on per-AI timeout). Stop-Job only
# kills the job runspace; the native CLI child (codex/node/grok) kept running past the
# timeout, kept working, and could later commit outside the one-writer-at-a-time
# sequencing. Sequential design means all current descendants ARE the hung job tree.
function Kill-JobChildren {
  try {
    $all = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Select-Object ProcessId, ParentProcessId
    $kill = New-Object System.Collections.Generic.List[int]
    $queue = New-Object System.Collections.Generic.Queue[int]
    $queue.Enqueue($PID)
    while($queue.Count){
      $p = $queue.Dequeue()
      foreach($c in ($all | Where-Object { $_.ParentProcessId -eq $p })){ $kill.Add([int]$c.ProcessId); $queue.Enqueue([int]$c.ProcessId) }
    }
    foreach($k in $kill){ try { Stop-Process -Id $k -Force -ErrorAction SilentlyContinue } catch {} }
    if($kill.Count){ Log "TIMEOUT kill: terminated $($kill.Count) orphaned child process(es) of the hung job" }
  } catch {}
}

# ---- O-15 #1: single-instance guard per lane (-Only) -- prevents duplicate daemons.
# The 03:22+03:23 double-launch ran 2 daemons per AI -> cycle dup + git race. A named
# mutex per lane: if another daemon for this lane already holds it, this one exits.
$laneKey = if ($Only.Count) { ($Only | Sort-Object) -join '+' } else { 'default' }
try {
  $script:daemonMutex = New-Object System.Threading.Mutex($false, "Global\hubdaemon_$laneKey")
  $owns = $false
  try { $owns = $script:daemonMutex.WaitOne(0) }
  catch [System.Threading.AbandonedMutexException] { $owns = $true }  # prior daemon died -> we own it now
  if (-not $owns) {
    Log "DUP-GUARD: a hub-daemon for lane '$laneKey' is already running. Exiting duplicate (PID $PID)."
    exit 0
  }
} catch { Log "DUP-GUARD: mutex check failed ($($_.Exception.Message)); continuing." }

# ---- Best-model config (source of truth = tools/models.json, refreshed daily). ----
# Each AI must always run the highest-benchmark model + max reasoning effort.
# Falls back to safe inline defaults if the file is missing/unparseable, so the
# daemon never dies just because models.json is absent.
$modelsFile = Join-Path $PSScriptRoot "models.json"
$Models = $null
if(Test-Path $modelsFile){ try { $Models = Get-Content $modelsFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $Models = $null } }
# audit F2: models.json is cached ONCE here at START. Capture its mtime so each cycle can warn if
# an applied refresh (e.g. an effort downgrade to relieve a premium pool) changed it on disk -- the
# running lane keeps the OLD model/effort silently until a restart otherwise.
$modelsMtime = if(Test-Path $modelsFile){ (Get-Item $modelsFile).LastWriteTime } else { $null }
function Get-ModelCfg([string]$ai,[string]$key,[string]$default){
  try { $v = $Models.$ai.$key; if($v){ return [string]$v } } catch {}
  return $default
}
# Resolve an AI's (model, effort) for a tier: 'primary' = highest-benchmark model+effort;
# 'fallback' = the cheaper model the AI switches to on usage/quota exhaustion (models.json
# fallback_model/fallback_effort). Has=$false when a fallback tier was asked for but no
# fallback_model is defined -> caller then just backs off (no model to switch to).
function Get-AIModelTier([string]$ai,[string]$tier){
  $defModel = switch($ai){ 'codex' {'gpt-5.5'} 'grok' {'grok-build'} 'antigravity' {'gemini-3.1-pro-preview'} default {''} }
  $defEff   = switch($ai){ 'codex' {'medium'} 'grok' {'high'} 'antigravity' {'high'} default {'high'} }
  if($tier -eq 'fallback'){
    $fm = Get-ModelCfg $ai 'fallback_model' ''
    if(-not $fm){ return [pscustomobject]@{ Model=''; Effort=''; Has=$false } }
    return [pscustomobject]@{ Model=$fm; Effort=(Get-ModelCfg $ai 'fallback_effort' $defEff); Has=$true }
  }
  return [pscustomobject]@{ Model=(Get-ModelCfg $ai 'model' $defModel); Effort=(Get-ModelCfg $ai 'effort' $defEff); Has=$true }
}

# NOTE (P0 fix 2026-06-14): the old Set-Heartbeat rewrote each AI's STATUS.md to
# force `state: running` + a fresh `updated:` stamp every cycle. That FAKED freshness
# (STATUS looked fresh even when the CLI did nothing), VIOLATED single-writer (the daemon
# wrote another AI's file), and MASKED a paused hub (forced running over a paused state).
# Removed. Real freshness now comes from honest signals the monitor already reads:
#   - tools/live/<ai>.log  (real transcript + real mtime, written by Invoke-AI below)
#   - git last-commit-by-author  (Get-GitLastByAuthor in monitor.ps1)
# and the daemon only runs cycles while CONTROL.state == running (gate in the loop).

# Default lane = codex only (2026-07-03): grok is REQUEST-ONLY per ROUTING section 4 --
# a looped grok over-produced ~291 unconsumed advisories (06-17 incident). Run grok via
# -Only grok (or pass it explicitly) only while a directed request is queued for it.
if($Only.Count -gt 0){ $AIs = $Only } else { $AIs = @('codex'); if($IncludeAG){ $AIs += 'antigravity' } }

# Quota backoff state: when an AI's CLI returns a 429/quota-exhausted error (e.g. the gemini
# AG seat hits TerminalQuotaError with an 8h reset), stop hammering it every cycle. Each
# consecutive quota failure doubles the cycles skipped (cap 48 ~= 8h at 10min); a clean run
# resets it. Without this the AG daemon burned a spawn every 10min for 8h producing nothing.
$quotaSkip    = @{}   # ai -> cycles still to skip
$quotaStrikes = @{}   # ai -> consecutive quota failures
# Persistent NON-quota failure backoff: a misconfigured AI (bad model id, untrusted-folder
# refusal, missing/erroring CLI) exits non-zero EVERY cycle and would otherwise spin silently
# for hours producing nothing (the "fresh growing by hours" symptom). Back off + log LOUD.
$failSkip     = @{}   # ai -> cycles still to skip after repeated hard failures
$failStrikes  = @{}   # ai -> consecutive non-quota, non-zero exits
foreach($a in $AIs){ $quotaSkip[$a] = 0; $quotaStrikes[$a] = 0; $failSkip[$a] = 0; $failStrikes[$a] = 0 }
# Model-switch-on-quota state: each AI runs its PRIMARY (best) model until that model reports
# usage/quota exhaustion; the daemon then switches it to fallback_model (models.json) for
# $PrimaryReprobeAfter cycles before re-probing primary (the quota may have reset). This keeps
# an AI producing on a cheaper model instead of idling through a multi-hour quota window.
$activeTier  = @{}   # ai -> 'primary' | 'fallback'
$tierReprobe = @{}   # ai -> cycles left on fallback before re-trying primary
foreach($a in $AIs){ $activeTier[$a] = 'primary'; $tierReprobe[$a] = 0 }
$PrimaryReprobeAfter = 6   # ~1h at the default 10min interval

# Count OPEN request orders addressed to this AI (lightweight frontmatter scan). Used to decide
# whether a drain (extra task this cycle) is warranted -- no open orders => no busywork.
# REF-AWARE (2026-07-03 4ai roundtrip test): an already-ANSWERED request is not open work.
# Single-writer means the recipient cannot flip the sender's `status:` field, so the raw
# status-only count kept re-triggering drain on answered orders (codex re-poll observed live,
# and the June stale-89 pile was the chronic form). A request counts as open only if NO
# response message references its id (or filename) in `ref:`.
function Count-OpenOrders([string]$ai){
  $answered = New-Object 'System.Collections.Generic.HashSet[string]'
  $opens = @()
  Get-ChildItem (Join-Path $root "agents") -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $obx = Join-Path $_.FullName "outbox"
    if(Test-Path $obx){
      Get-ChildItem $obx -Filter *.md -File -ErrorAction SilentlyContinue | ForEach-Object {
        $h = Get-Content $_.FullName -Encoding UTF8 -TotalCount 14
        $to=""; $ty=""; $stt=""; $id=""; $ref=""
        foreach($l in $h){
          if($l -match '^to:\s*"?(.*?)"?\s*$'){ $to=$matches[1] }
          elseif($l -match '^type:\s*"?(.*?)"?\s*$'){ $ty=$matches[1] }
          elseif($l -match '^status:\s*"?(.*?)"?\s*$'){ $stt=$matches[1] }
          elseif($l -match '^id:\s*"?(.*?)"?\s*$'){ $id=$matches[1].Trim() }
          elseif($l -match '^ref:\s*"?(.*?)"?\s*$'){ $ref=$matches[1].Trim() }
        }
        if($ty -eq 'response' -and $ref){ [void]$answered.Add($ref) }
        if(($to -eq $ai -or $to -eq 'all') -and $ty -eq 'request' -and $stt -eq 'open'){
          $opens += [pscustomobject]@{ Id=$id; File=$_.BaseName }
        }
      }
    }
  }
  return @($opens | Where-Object { -not (($_.Id -and $answered.Contains($_.Id)) -or $answered.Contains($_.File)) }).Count
}

# Reroute on backoff (audit 2026-06-17): when an AI is PARKED (quota or hard-fail backoff) yet has
# OPEN orders it cannot serve, those orders rot in the queue (the codex shared-pool-quota / AG dead-
# headless symptom). File a deduped request to the AI's reroute_to lane (models.json) so a healthy
# AI / Claude picks them up instead. Self-replacing (one note per parked AI) + 1h cooldown = no spam.
$script:lastReroute = @{}
function Reroute-Orders([string]$ai,[string]$reason){
  $target = Get-ModelCfg $ai 'reroute_to' ''
  if(-not $target -or $target -eq $ai){ return }
  $open = 0; try { $open = Count-OpenOrders $ai } catch {}
  if($open -le 0){ return }   # nothing to reroute
  $nowE = [int][double]::Parse((Get-Date -UFormat %s))
  if($script:lastReroute[$ai] -and ($nowE - [int]$script:lastReroute[$ai]) -lt 3600){ return }  # 1h cooldown
  $script:lastReroute[$ai] = $nowE
  $inbox = Join-Path $root "agents\$target\inbox"
  if(-not (Test-Path $inbox)){ New-Item -ItemType Directory -Force $inbox | Out-Null }
  Get-ChildItem $inbox -Filter "*-reroute-$ai.md" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $body = @"
---
from: hub-daemon
to: $target
type: request
priority: high
status: open
id: $stamp-reroute-$ai
created: $(Now) KST
---

# [reroute] $ai backoff ($reason) - $open open order(s) need a new owner

[$(Now) KST] Lane $ai is parked ($reason). $open OPEN order(s) addressed to it cannot be served and sit in the queue.
$target : take them over or re-assign. Scan agents/*/outbox for (to: $ai or all) + (type: request) + (status: open).

(auto-reroute by hub-daemon; max 1/hour per parked lane, note is self-replacing, stops when $ai returns. Body is ASCII on purpose: lane daemons run under powershell.exe 5.1 which reads BOM-less UTF-8 as cp949 and mojibakes Korean literals.)
"@
  try { [System.IO.File]::WriteAllText((Join-Path $inbox "$stamp-reroute-$ai.md"), $body, $utf8) } catch {}
  Log "$ai parked with $open open orders ($reason) -> reroute notice filed to $target inbox"
}

function Invoke-AI([string]$ai,[string]$tier='primary'){
  # Single-line, NO embedded double-quotes: PS 5.1 mangles native-exe arguments
  # that contain " or span lines (this broke grok+codex in the first test).
  # Paths are plain text; the AI quotes them itself when it runs commands.
  $lane = switch($ai){
    'codex'       { "codex lane = 2nd-B UI/anti-slop/bug-QA/native-safety; work in a git worktree off origin/main, branch only, do NOT push (Claude is the merge gate), submit to agents/codex/outbox." }
    'grok'        { "grok lane = market/X/consumer-signal advisory; written advisory text only, no code." }
    'antigravity' { "antigravity lane = native/emulator QA; report findings only, no push." }
  }
  $prompt = "You are $ai in the 4-AI hub (root: $root). Run ONE autonomous poll cycle (PROTOCOL 12/19/35.4). Step 1: read your inbox with tools/board.ps1 -Me $ai and scan agents/*/outbox for OPEN requests addressed to $ai or all. Step 2: if an open order exists do the next one, otherwise autonomously do the single most valuable task in your lane per BOARD.md current focus. Step 3 constraints: single-writer (write only agents/$ai/ in the hub), NEVER push 2nd-B, no destructive/cost/secrets actions (escalate to Claude via outbox), apply section 35 self-panel, ONE task only this cycle. Step 4 (REPORT - PROTOCOL section 16, only for cycles that did REAL NEW work - see NO-OP RULE at the end): write a SELF-CONTAINED HTML report of this cycle to agents/$ai/outbox/preview/<yyyyMMdd-HHmmss>-<slug>.html - ALL human-readable text (title, body, captions, table headers, button labels) in KOREAN, dark theme, <=3 colors, no emoji/ornament (anti-slop); reference its path in your outbox .md under a '## Links' section. Do NOT run start/Invoke-Item/auto-open - you are a HEADLESS daemon and it cannot surface a browser; the user opens reports via tools/open-reports.ps1. Step 5: commit BOTH the .md and the .html via tools/commit.ps1 -As $ai -Message <conventional msg> -Files <your files> (quote paths containing spaces), then refresh agents/$ai/STATUS.md with a fresh updated stamp and one activity line. RESPONSE FRONTMATTER CONTRACT (2026-07-03, hub-health enforced): every outbox .md you write MUST open with a frontmatter block containing ALL 9 keys, exactly these names - id: <yyyyMMdd-HHmmss>-<you>-re-<slug> | from: <you> | to: <requester or claude> | type: <response or fyi or request> | ref: <the request id you answer; empty string if none> | project: <mirror the request, else hub> | priority: <mirror the request, else normal> | status: <done or open> | created: <real Get-Date timestamp> KST. Missing keys count as hub-health WARN violations (created and project were the ones dropped in the 4ai test). Timestamps via Get-Date KST. NO-OP RULE (2026-07-03): if there is NO actionable open order AND no genuinely new lane task (queue unchanged since your previous cycle), write NOTHING this cycle - no report, no commit, no STATUS touch; end quietly (the daemon log is the record; repeated stale-queue-hold reports are FORBIDDEN, cf. 2026-07-02 incident with dozens of identical hold commits). HUB GIT RULE: the hub repo stays on branch master - NEVER git checkout/switch/branch inside the hub repo (commit.ps1 blocks non-master commits; 2nd-B work runs in separate worktrees, never in the hub tree). MOA CROSS-VERIFY (ROUTING-MOA.md section 3): if your deliverable this cycle is HIGH-RISK (merge diff, schema change, security-sensitive code, math/quant result, live external-fact claim) also file ONE verify request in your outbox to the mapped verifier seat (code/schema -> antigravity, math/external-facts -> grok, UI -> codex; if the verifier would be you -> claude) and add a line verify: requested to your deliverable frontmatter. $lane"
  $liveDir = Join-Path $root "tools\live"
  if(-not (Test-Path $liveDir)){ New-Item -ItemType Directory -Force $liveDir | Out-Null }
  $live = Join-Path $liveDir ($ai + ".log")
  # Resolve THIS AI's model+effort for the requested tier from models.json (always-best, §MODELS.md):
  # 'primary' = highest-benchmark; 'fallback' = cheaper model used after usage/quota exhaustion.
  # Resolved in the PARENT (Get-AIModelTier reads $Models here), then passed into the job below.
  $mt    = Get-AIModelTier $ai $tier
  $model = $mt.Model
  $eff   = $mt.Effort
  # Antigravity migrated OFF the deprecated gemini CLI (sunset 2026-06-18) to agy run
  # HEADLESS via the ConPTY wrapper (tools/agy-pty/agy-headless.js). `agy -p` emits ~0
  # bytes under redirected stdout, which SILENTLY no-op'd the AG seat (exit 0, empty
  # transcript, STATUS stale for hours). The wrapper gives agy a pseudo-terminal and
  # extracts the answer. AGY_MODEL takes the agy picker LABEL ("Gemini 3.1 Pro (High)"),
  # not the gemini model id. Needs node + node-pty installed (tools/agy-pty/node_modules).
  # See agy-pty/README.md.
  $agyHeadless = Join-Path $PSScriptRoot "agy-pty\agy-headless.js"
  $agyModel    = Get-ModelCfg 'antigravity' 'agy_model' 'Gemini 3.1 Pro (High)'
  # Fallback-tier wiring (2026-07-04 audit): the quota fallback previously swapped only
  # $model (the LOG label) while re-spawning the exhausted primary agy picker label --
  # the fallback was cosmetic. If models.json carries agy_fallback_model, use it on the
  # fallback tier; else keep primary and say so honestly in the log.
  if($tier -ne 'primary'){
    $agyFb = Get-ModelCfg 'antigravity' 'agy_fallback_model' ''
    if($agyFb){ $agyModel = $agyFb }
    else { Log "WARN: antigravity fallback tier requested but models.json has no agy_fallback_model picker label - re-spawning primary label '$agyModel' (likely still quota-parked)" }
  }

  # P0 timeout guard: run the CLI inside a background job bounded by Wait-Job -Timeout. A hung
  # CLI (codex stdin-EOF hang, network stall) previously blocked the whole sequential loop
  # forever; now it is killed after $PerAITimeoutSec and the loop continues.
  $sb = {
    param($ai,$root,$prompt,$model,$eff,$agyHeadless,$agyModel)
    $o = ""
    switch($ai){
      'codex'       { $o = ("" | codex exec -s danger-full-access --skip-git-repo-check -C $root -m $model -c "model_reasoning_effort=$eff" $prompt) 2>&1 | Out-String }
      'grok'        { $env:GROK_MODEL = $model; $env:GROK_REASONING_EFFORT = $eff; $o = (grok -m $model -p $prompt) 2>&1 | Out-String }
      'antigravity' {
        $env:AGY_CWD = $root; $env:AGY_MODEL = $agyModel; $env:AGY_USE_CONPTY = '0'
        # Suppress UAC (2026-07-11): agy's auto-updater elevates via ShellExecute/runas on
        # launch (dedicated updater at antigravity-cli-auto-updater-*.run.app + the .old
        # binary-swap), popping a User Account Control prompt in this headless daemon where
        # nobody can approve it. Disabling auto-update removes that elevation path entirely.
        # Also persisted as a User env var. To update agy: clear both, run agy once, re-set.
        $env:AGY_CLI_DISABLE_AUTO_UPDATE = '1'
        # Suppress the SECOND UAC source (2026-07-11): agy ALSO ShellExecute(runas)-elevates for a
        # privileged op (sandbox/sbox setup) despite having NO elevation manifest -- neither the
        # auto-update disable nor Developer Mode stopped it. __COMPAT_LAYER=RUNASINVOKER forces agy +
        # its child processes to run as the invoker (no UAC) for this headless job. Interactive
        # launches are covered separately by the per-app HKCU AppCompatFlags RUNASINVOKER shim on agy.exe.
        $env:__COMPAT_LAYER = 'RUNASINVOKER'
        # Real tasks take minutes: the wrapper's old 90s per-attempt kill murdered agy
        # MID-TASK, the retry re-ran the task (duplicate outputs), then AGY_EMPTY exit 1
        # (2026-07-03 4ai roundtrip test). 15min/attempt x2 tries fits PerAITimeoutSec.
        $env:AGY_TIMEOUT_MS = '900000'; $env:AGY_TRIES = '2'
        $o = (node $agyHeadless $prompt) 2>&1 | Out-String
      }
    }
    # $LASTEXITCODE can be $null if the CLI never launched (spawn failure) -- report -1,
    # not a silent success (a null coerced to 0 made dead lanes look healthy).
    [pscustomobject]@{ Out = $o; Code = $(if($null -ne $LASTEXITCODE){ $LASTEXITCODE } else { -1 }) }
  }
  $job = Start-Job -ScriptBlock $sb -ArgumentList $ai,$root,$prompt,$model,$eff,$agyHeadless,$agyModel
  $fin = Wait-Job $job -Timeout $PerAITimeoutSec
  if(-not $fin){
    Stop-Job $job -ErrorAction SilentlyContinue
    Kill-JobChildren
    Remove-Job $job -Force -ErrorAction SilentlyContinue
    Log "cycle TIMEOUT($ai) after ${PerAITimeoutSec}s -- killed CLI (incl. child process tree), continuing"
    try { [System.IO.File]::WriteAllText($live, "[$(Now) KST] $ai [$($tier):$model] (TIMEOUT ${PerAITimeoutSec}s)`n", $utf8) } catch {}
    return [pscustomobject]@{ Code = -1; Quota = $false; TimedOut = $true; Model = $model; Tier = $tier }
  }
  $rcv = Receive-Job $job 2>&1
  Remove-Job $job -Force -ErrorAction SilentlyContinue
  # Job results are deserialized, so match by property name (not [pscustomobject] type).
  $obj  = $rcv | Where-Object { $_ -and ($_.PSObject.Properties.Name -contains 'Out') } | Select-Object -Last 1
  $out  = if($obj){ [string]$obj.Out } else { ($rcv | Out-String) }
  # No result object = the job scriptblock itself crashed (binding/serialization/terminating
  # error). That is a FAILURE (-1), not exit 0 -- a 0 here bypassed the hard-fail backoff and
  # reset failStrikes while the lane was completely dead.
  $code = if($obj){ [int]$obj.Code } else { -1 }
  # Detect quota/rate-limit exhaustion so the caller can back off instead of re-spawning.
  # §quota-false-positive fix (2026-06-17): the loose terms (bare "rate limit"/"429") were matched
  # against the WHOLE transcript regardless of exit code, so a SUCCESSFUL exit-0 cycle that merely
  # built rate-limit UI / discussed throttling got false-flagged QUOTA and backed off after success.
  # Now: a real exhaustion BANNER counts even on exit 0 (codex prints the banner then exits 0);
  # loose terms count only when the CLI actually failed ($code -ne 0).
  $quotaBanner = ($out -match 'hit your usage limit|TerminalQuotaError|RESOURCE_EXHAUSTED|QUOTA_EXHAUSTED|exhausted your capacity')
  # audit D2 (2026-07-11): the old loose terms (bare "rate.?limit" / "429 ") matched the WHOLE
  # transcript, so a nonzero-exit crash (untrusted-folder, network) whose transcript merely QUOTES
  # 429/rate-limit handling from the 2nd-B code it read was misrouted into ~8h quota backoff instead
  # of the LOUD 4-strike hard-fail. Anchor on the CLI's own error framing (prefer under-detecting
  # quota -- the hard-fail path logs the real error).
  $quotaLoose  = ($out -match 'usage limit|"code":\s*429|429 Too Many Requests|Too Many Requests|rate limit exceeded|RateLimitError|rate_limit_exceeded')
  $quota = [bool]($quotaBanner -or ($code -ne 0 -and $quotaLoose))
  # Phantom-success guard (2026-06-17): a clean exit 0 with an essentially EMPTY transcript is not
  # real work (the AG seat's old silent no-op: gemini/agy -p emitted ~0 bytes yet exited 0). Force a
  # failure so the hard-fail backoff + LOUD log fire instead of recording a fake success.
  $bodyLen = ($out -replace '\s','').Length
  if($code -eq 0 -and -not $quota -and $bodyLen -lt 24){
    Log "cycle $ai exit 0 but EMPTY transcript ($bodyLen chars) -> NO-OP failure (dead lane / broken CLI / headless wrapper produced nothing)"
    $code = -1
  }
  Log "cycle exit($ai/$tier=$model)=$code$(if($quota){' QUOTA'})"
  # Keep the last ~45 non-empty lines (the AI's closing summary = its "what I just did")
  # as a live transcript -- written UTF-8 (Korean-safe) so feed.ps1 can show it like a chat message.
  $tail = (($out -split "`r?`n") | Where-Object { $_.Trim() -ne "" } | Select-Object -Last 45) -join "`n"
  try { [System.IO.File]::WriteAllText($live, "[$(Now) KST] $ai [$($tier):$model] (exit $code$(if($quota){' QUOTA-EXHAUSTED'}))`n`n$tail`n", $utf8) } catch {}
  return [pscustomobject]@{ Code = $code; Quota = [bool]$quota; TimedOut = $false; Model = $model; Tier = $tier }
}

# CONTROL.md run-state (§13): the daemon must not spawn AIs while the hub is paused/draining.
# FAIL-CLOSED (2026-07-03): a missing/unparseable semaphore now means PAUSED, not running --
# CONTROL is a safety stop; corruption must not silently restart the hub.
function Get-ControlState {
  $cf = Join-Path $root "CONTROL.md"
  if(-not (Test-Path -LiteralPath $cf)){ Log "CONTROL.md MISSING -> treating as paused (fail-closed)"; return 'paused' }
  $h = Get-Content -LiteralPath $cf -Encoding UTF8 -TotalCount 30
  foreach($l in $h){ if($l -match '^\s*state:\s*"?(\w+)'){ return $matches[1].ToLower() } }
  Log "CONTROL.md has no state: line in first 30 lines -> treating as paused (fail-closed)"
  return 'paused'
}

Log "hub-daemon START interval=${IntervalSec}s AIs=$($AIs -join ',') maxTasks=$MaxTasksPerCycle timeout=${PerAITimeoutSec}s maxCycles=$MaxCycles"
$cycle = 0
while($true){
  # CONTROL.state gate (§13): only spawn AIs while running. paused/draining -> skip this cycle
  # (no fake heartbeat, no new work) and re-check after the interval.
  $cs = Get-ControlState
  if($cs -ne 'running'){
    Log "cycle skipped -- CONTROL.state=$cs (waiting; resumes when running)"
    if($MaxCycles -gt 0){ break }
    Start-Sleep -Seconds $IntervalSec
    continue
  }
  $cycle++
  Log "cycle $cycle BEGIN"
  # audit F2: warn once per change if the applied models.json diverged from what this daemon loaded.
  if($modelsMtime -and (Test-Path $modelsFile)){ $mt=(Get-Item $modelsFile).LastWriteTime; if($mt -gt $modelsMtime){ Log "WARN: models.json changed on disk since daemon start ($($mt.ToString('MM-dd HH:mm'))) -- lane '$laneKey' is running STALE model config; restart the daemon to apply."; $modelsMtime=$mt } }
  foreach($ai in $AIs){
    # Quota backoff: skip this AI while its backoff window is open (e.g. gemini 429 / 8h reset).
    if($quotaSkip[$ai] -gt 0){
      $quotaSkip[$ai]--
      Log "cycle $cycle -> $ai SKIP (quota backoff, $($quotaSkip[$ai]) cycles left)"
      continue
    }
    # Hard-failure backoff: stop hammering an AI that is failing every cycle (bad config).
    if($failSkip[$ai] -gt 0){
      $failSkip[$ai]--
      Log "cycle $cycle -> $ai SKIP (hard-failure backoff, $($failSkip[$ai]) cycles left -- check tools/live/$ai.log for the real error: AG=ConPTY/console (AGY_USE_CONPTY), model id, CLI auth, trusted-folder; fix then restart)"
      continue
    }
    # Model-switch re-probe: if this AI is on its fallback model, count down the window; when it
    # elapses, flip back to primary so the next invoke re-tests the (possibly reset) primary quota.
    if($activeTier[$ai] -eq 'fallback'){
      if($tierReprobe[$ai] -gt 0){ $tierReprobe[$ai]-- }
      if($tierReprobe[$ai] -le 0){ $activeTier[$ai] = 'primary'; Log "cycle $cycle -> $ai re-probe PRIMARY model (fallback window elapsed)" }
    }
    # Anti-idle drain: do the first task, then keep going while OPEN orders remain for this AI,
    # up to MaxTasksPerCycle. With no open orders this is exactly one self-directed task (no busywork).
    $task = 0
    while($task -lt $MaxTasksPerCycle){
      $task++
      Log "cycle $cycle -> $ai poll (task $task/$MaxTasksPerCycle, model=$($activeTier[$ai]))"
      $res = $null
      try { $res = Invoke-AI $ai $activeTier[$ai] } catch { Log "cycle $cycle $ai ERROR: $($_.Exception.Message)" }
      # MODEL-SWITCH-ON-QUOTA: primary model exhausted + a distinct fallback exists -> switch the
      # AI to its fallback model and retry THIS cycle once. If the fallback is also exhausted (or
      # none is defined) the existing quota-backoff below takes over.
      if($res -and $res.Quota -and $activeTier[$ai] -eq 'primary'){
        $fb = Get-AIModelTier $ai 'fallback'
        $pr = Get-AIModelTier $ai 'primary'
        if($fb.Has -and ($fb.Model -ne $pr.Model -or $fb.Effort -ne $pr.Effort)){
          Log "cycle $cycle $ai QUOTA on primary $($pr.Model)@$($pr.Effort) -> SWITCH to fallback $($fb.Model)@$($fb.Effort), retrying this cycle"
          $activeTier[$ai] = 'fallback'; $tierReprobe[$ai] = $PrimaryReprobeAfter
          try { $res = Invoke-AI $ai 'fallback' } catch { Log "cycle $cycle $ai fallback ERROR: $($_.Exception.Message)" }
        } else {
          Log "cycle $cycle $ai QUOTA on primary but no distinct fallback_model in models.json -> backing off"
        }
      }
      if($res -and $res.Quota){
        $quotaStrikes[$ai]++
        $skip = [Math]::Min(48, [Math]::Pow(2, $quotaStrikes[$ai]))
        $quotaSkip[$ai] = [int]$skip
        Log "cycle $cycle $ai QUOTA strike $($quotaStrikes[$ai]) -> backing off $([int]$skip) cycles (~$([int]($skip*$IntervalSec/60))m)"
        Reroute-Orders $ai 'quota'
        break
      } else {
        $quotaStrikes[$ai] = 0
        # Non-quota hard failure (bad model id, untrusted folder, missing/erroring CLI). After
        # 4 in a row, back off with a LOUD log instead of spinning silently for hours.
        if((-not $res) -or ($res.Code -ne 0)){
          $failStrikes[$ai]++
          if($failStrikes[$ai] -ge 4){
            $skip = [Math]::Min(36, [Math]::Pow(2, $failStrikes[$ai] - 3))
            $failSkip[$ai] = [int]$skip
            Log "cycle $cycle $ai HARD-FAIL x$($failStrikes[$ai]) (exit $(if($res){$res.Code}else{'spawn'})) -> backing off $([int]$skip) cycles. Check tools/live/$ai.log for the REAL error (AG: ConPTY 'AttachConsole failed' under jobs -> AGY_USE_CONPTY=0; also model id / CLI auth / trusted-folder), fix, then restart daemon."
            Reroute-Orders $ai 'hard-fail'
          } else {
            Log "cycle $cycle $ai fail strike $($failStrikes[$ai]) (exit $(if($res){$res.Code}else{'spawn'}))"
          }
          break
        } else {
          $failStrikes[$ai] = 0
        }
      }
      if($task -lt $MaxTasksPerCycle){
        $remaining = 0
        try { $remaining = Count-OpenOrders $ai } catch {}
        if($remaining -le 0){ break }   # nothing left to drain -> don't manufacture busywork
        Log "cycle $cycle -> $ai drain ($remaining open orders remain)"
      }
    }
  }
  # BRANCH SELF-HEAL (2026-07-03): a spawned CLI once left HEAD on a stray branch; commits
  # then missed master and HubBackup (which pushes master) silently backed up nothing for a
  # day. If HEAD drifted off master and master is a pure ancestor, ff master forward and
  # drop the stray branch; otherwise log LOUD for Claude to repair (never force anything).
  try {
    $curB = (git -C $root rev-parse --abbrev-ref HEAD 2>$null)
    if($curB -and $curB -ne 'master'){
      git -C $root merge-base --is-ancestor master $curB 2>$null
      $ffable = ($LASTEXITCODE -eq 0)
      # audit D3 (2026-07-11): --untracked-files=no so only TRACKED mid-write changes block the heal.
      # Daemon-authored reroute/self-feedback notes drop UNTRACKED into agents/*/inbox and left the
      # tree permanently dirty, which disabled this auto-repair entirely (it always fell to
      # BRANCH-ALERT). Untracked files are untouched by checkout/ff-merge, so they must not block it.
      $dirty = @(git -C $root status --porcelain --untracked-files=no 2>$null).Count -gt 0
      if($ffable -and -not $dirty){
        git -C $root checkout master 2>&1 | Out-Null
        git -C $root merge --ff-only $curB 2>&1 | Out-Null
        git -C $root branch -d $curB 2>&1 | Out-Null
        Log "BRANCH-HEAL: HEAD was on stray '$curB' -> ff-merged into master, branch deleted"
      } else {
        Log "BRANCH-ALERT: HEAD on '$curB' (dirty=$dirty ffable=$ffable) -> Claude repair needed (hub stays on master, PROTOCOL 5)"
      }
    }
  } catch { Log "BRANCH-HEAL check failed: $($_.Exception.Message)" }
  Log "cycle $cycle END"
  if($MaxCycles -gt 0 -and $cycle -ge $MaxCycles){ Log "reached MaxCycles=$MaxCycles, stopping"; break }
  Start-Sleep -Seconds $IntervalSec
}
