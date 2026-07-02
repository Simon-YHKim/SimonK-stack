# hub-health.ps1 -- AI Hub self-test (read-only). Verifies the hub TOOLING is intact:
# script syntax, commit.ps1 guards (single-writer / encoding-size / mutex / attribution),
# state files (CONTROL/BOARD/MODELS), models.json best-model contract, outbox frontmatter,
# git+UTF-8 integrity, and daemon liveness. Complements monitor.ps1 (which shows live STATE);
# this asserts the machinery itself works. Default run is 100% side-effect-free.
# ASCII-only source (PS 5.1 no-BOM safe).
#
# Usage (VS Code terminal, cwd = hub root or tools/):
#   powershell -ExecutionPolicy Bypass -File "tools/hub-health.ps1"
#   powershell -ExecutionPolicy Bypass -File "tools/hub-health.ps1" -Deep    # adds lane-guard behavioral test in a temp repo
#   powershell -ExecutionPolicy Bypass -File "tools/hub-health.ps1" -Json    # machine output
#   powershell -ExecutionPolicy Bypass -File "tools/hub-health.ps1" -StrictWarn  # WARN also exits 1
# Exit: 0 = all invariants OK; 1 = a FAIL (or WARN under -StrictWarn). Safe to run every cycle.
param([switch]$Deep, [switch]$Json, [int]$MaxAgeMin = 20, [switch]$StrictWarn, [switch]$Quick)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
$toolsDir = $PSScriptRoot

$script:results = @()
function Res($s, $d) { return [pscustomobject]@{ S = $s; D = $d } }
function Check([string]$Area, [string]$Name, [scriptblock]$Test) {
  $r = $null
  try { $r = & $Test } catch { $r = Res 'FAIL' ("exception: " + $_.Exception.Message) }
  if (-not $r -or -not $r.S) { $r = Res 'FAIL' 'no result' }
  $script:results += [pscustomobject]@{ Area = $Area; Name = $Name; Status = $r.S; Detail = [string]$r.D }
}

# ---- helpers ----
# Read a log the daemon may be appending to right now. Plain Get-Content throws
# "file in use by another process" mid-append; open with FileShare.ReadWrite + retry.
function Read-SharedLog([string]$path, [int]$tail = 0) {
  if (-not (Test-Path -LiteralPath $path)) { return @() }
  for ($i = 0; $i -lt 4; $i++) {
    try {
      $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
      try { $sr = New-Object System.IO.StreamReader($fs, [System.Text.UTF8Encoding]::new($false)); $text = $sr.ReadToEnd(); $sr.Close() }
      finally { $fs.Close() }
      $ls = @($text -split "`r?`n")
      if ($tail -gt 0 -and $ls.Count -gt $tail) { $ls = $ls[($ls.Count - $tail)..($ls.Count - 1)] }
      return @($ls)
    } catch { Start-Sleep -Milliseconds 60 }
  }
  return @()
}
function Test-Ps1Syntax([string]$path) {
  $tokens = $null; $perrs = $null
  try { [void][System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$perrs) }
  catch { return @{ ok = $false; n = 1; msg = $_.Exception.Message } }
  return @{ ok = ($perrs.Count -eq 0); n = $perrs.Count; msg = ($perrs | Select-Object -First 1 | ForEach-Object { $_.Message }) }
}
function Test-Utf8Clean([string]$path) {
  # mirror commit.ps1: reject BOM + U+FFFD replacement bytes + non-strict-UTF8 decode
  try { $bytes = [System.IO.File]::ReadAllBytes($path) } catch { return @{ ok = $false; why = 'unreadable' } }
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { return @{ ok = $false; why = 'has BOM' } }
  for ($i = 0; $i -lt $bytes.Length - 2; $i++) {
    if ($bytes[$i] -eq 0xEF -and $bytes[$i + 1] -eq 0xBF -and $bytes[$i + 2] -eq 0xBD) { return @{ ok = $false; why = 'U+FFFD at byte ' + $i } }
  }
  try { [void]([System.Text.UTF8Encoding]::new($false, $true)).GetString($bytes) } catch { return @{ ok = $false; why = 'invalid utf8' } }
  return @{ ok = $true; why = '' }
}
function Invoke-Child([string]$relPath, [string[]]$argv, [int]$timeoutSec = 25) {
  $path = Join-Path $root $relPath
  if (-not (Test-Path $path)) { return [pscustomobject]@{ Code = -1; Out = 'missing'; TimedOut = $false } }
  # Build a properly-quoted argument string ([Diagnostics.Process] reliably yields ExitCode + output;
  # Start-Process -RedirectStandardOutput proved flaky for fast-exiting children).
  $quoted = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $path + '"'))
  foreach ($a in $argv) { if ($a -match '\s') { $quoted += ('"' + $a + '"') } else { $quoted += $a } }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = 'powershell'
  $psi.Arguments = ($quoted -join ' ')
  $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
  $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
  $p = $null
  try { $p = [System.Diagnostics.Process]::Start($psi) } catch { return [pscustomobject]@{ Code = -3; Out = $_.Exception.Message; TimedOut = $false } }
  $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
  if (-not $p.WaitForExit($timeoutSec * 1000)) {
    try { $p.Kill() } catch {}
    return [pscustomobject]@{ Code = -2; Out = ''; TimedOut = $true }
  }
  $txt = ''
  try { $txt = [string]$so.Result + [string]$se.Result } catch {}
  return [pscustomobject]@{ Code = $p.ExitCode; Out = [string]$txt; TimedOut = $false }
}
function Read-Src([string]$rel) { $p = Join-Path $root $rel; if (Test-Path $p) { return (Get-Content $p -Raw -Encoding UTF8) } return '' }
# O-19: read-only git on the hub repo with --no-optional-locks + a hard timeout, so a
# concurrent committer's index.lock can never hang a health check (was 22s+). git status
# normally takes an *optional* index-refresh lock and waits on the committer; the flag
# tells it to skip that lock. The process kill is a backstop. Returns Out/Code/TimedOut.
function Invoke-GitRO([string[]]$gitArgs, [int]$timeoutSec = 4) {
  $full = @('--no-optional-locks', '-C', $root) + $gitArgs
  $sb = New-Object System.Text.StringBuilder
  foreach ($a in $full) { if ($a -match '\s') { [void]$sb.Append('"' + $a + '" ') } else { [void]$sb.Append($a + ' ') } }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = 'git'
  $psi.Arguments = $sb.ToString().TrimEnd()
  $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
  $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
  $p = $null
  try { $p = [System.Diagnostics.Process]::Start($psi) } catch { return @{ Out = ''; Code = -3; TimedOut = $false } }
  $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
  if (-not $p.WaitForExit($timeoutSec * 1000)) {
    try { $p.Kill() } catch {}
    return @{ Out = ''; Code = -2; TimedOut = $true }
  }
  $txt = ''
  try { $txt = [string]$so.Result } catch {}
  return @{ Out = $txt; Code = $p.ExitCode; TimedOut = $false }
}

# =====================================================================
# AREA: Scripts (static syntax + read-only execution)
# =====================================================================
Check 'Scripts' 'ps1 syntax (all tools)' {
  $ps1 = Get-ChildItem $toolsDir -Filter *.ps1 -File
  $bad = @()
  foreach ($f in $ps1) { $t = Test-Ps1Syntax $f.FullName; if (-not $t.ok) { $bad += ($f.Name + ': ' + $t.msg) } }
  if ($bad.Count -gt 0) { Res 'FAIL' (($bad | Select-Object -First 3) -join ' | ') }
  else { Res 'PASS' ($ps1.Count.ToString() + ' scripts, 0 parse errors') }
}
# O-19: the 5 tool-execution smoke tests each cold-start a PowerShell child (~1.5s),
# dominating runtime. -Quick skips them so the phone health tab gets a sub-5s integrity
# snapshot (static syntax + state + git + liveness still run). Full smoke is the default.
if ($Quick) {
  Check 'Scripts' 'tool exec smoke (5 read-only runs)' { Res 'SKIP' 'deferred (-Quick fast snapshot); run without -Quick for full smoke' }
} else {
Check 'Scripts' 'board.ps1 -Me claude (read-only run)' {
  $r = Invoke-Child 'tools/board.ps1' @('-Me', 'claude') 20
  if ($r.TimedOut) { Res 'FAIL' 'timed out' }
  elseif ($r.Code -eq 0 -and $r.Out -match 'RUN STATE') { Res 'PASS' 'exit 0, RUN STATE present' }
  else { Res 'FAIL' ('exit ' + $r.Code + '; banner missing') }
}
Check 'Scripts' 'monitor.ps1 -Once (read-only run)' {
  $r = Invoke-Child 'tools/monitor.ps1' @('-Once') 25
  if ($r.TimedOut) { Res 'FAIL' 'hung (--Once should not loop)' }
  elseif ($r.Code -eq 0 -and $r.Out -match 'AI HUB MONITOR') { Res 'PASS' 'renders, exit 0' }
  else { Res 'WARN' ('exit ' + $r.Code) }
}
Check 'Scripts' 'feed.ps1 -Once (read-only run)' {
  $r = Invoke-Child 'tools/feed.ps1' @('-Once') 20
  if ($r.TimedOut) { Res 'WARN' 'hung/looped on -Once' }
  elseif ($r.Code -eq 0) { Res 'PASS' 'exit 0' }
  else { Res 'WARN' ('exit ' + $r.Code) }
}
Check 'Scripts' 'wiki-ingest.ps1 -ListOnly (read-only run)' {
  $r = Invoke-Child 'tools/wiki-ingest.ps1' @('-ListOnly') 20
  if ($r.TimedOut) { Res 'WARN' 'timed out' }
  elseif ($r.Code -eq 0) { Res 'PASS' 'exit 0' }
  else { Res 'WARN' ('exit ' + $r.Code) }
}
Check 'Scripts' 'expo-smoke.ps1 (read-only, no -Report)' {
  $r = Invoke-Child 'tools/expo-smoke.ps1' @() 35
  if ($r.TimedOut) { Res 'WARN' 'timed out (adb slow / no device)' }
  elseif ($r.Out -match 'NO-EMULATOR|NO-DEVICE|NO-ADB') { Res 'WARN' 'no emulator/device (expected when off)' }
  elseif ($r.Out -match 'PASS|CRASH') { Res 'PASS' 'crash gate ran' }
  else { Res 'WARN' ('verdict unclear, exit ' + $r.Code) }
}
}
Check 'Scripts' 'hub-daemon.ps1 (static only - cost-gated)' {
  $src = Read-Src 'tools/hub-daemon.ps1'
  if (-not $src) { return Res 'FAIL' 'missing' }
  # Assert CURRENT invariants (not 'Set-Heartbeat' — that was removed 2026-06-14 and only
  # survives in a comment, so the old check false-passed). agy-headless = the migrated AG lane.
  $need = @('models.json', 'Get-ModelCfg', 'Get-AIModelTier', 'quotaSkip', 'activeTier', 'agy-headless')
  $miss = @($need | Where-Object { $src -notmatch [regex]::Escape($_) })
  if ($miss.Count -gt 0) { Res 'FAIL' ('missing: ' + ($miss -join ', ')) }
  else { Res 'PASS' 'models.json injection + tier/quota backoff + agy-headless AG lane present' }
}
Check 'Scripts' 'AI CLIs resolvable (codex/grok/agy + node)' {
  # AG runs agy HEADLESS via the node-pty wrapper now (gemini CLI sunset 2026-06-18),
  # so the real AG-lane deps are agy + node, not gemini.
  $miss = @('codex', 'grok', 'agy', 'node') | Where-Object { -not (Get-Command $_ -ErrorAction SilentlyContinue) }
  if ($miss.Count -eq 0) { Res 'PASS' 'codex, grok, agy, node on PATH (AG = agy headless via node-pty)' }
  else { Res 'WARN' ('not on PATH: ' + ($miss -join ', ') + ' (AG lane needs agy + node for the headless wrapper)') }
}

# =====================================================================
# AREA: Guards (commit.ps1 invariants)
# =====================================================================
$commitSrc = Read-Src 'tools/commit.ps1'
Check 'Guards' 'commit.ps1 lane-guard (single-writer)' {
  if (-not $commitSrc) { return Res 'FAIL' 'commit.ps1 missing' }
  if ($commitSrc -match 'agents/\$As/' -and $commitSrc -match 'claude' -and $commitSrc -match 'exit 1') { Res 'PASS' 'non-claude writes confined to agents/<As>/' }
  else { Res 'FAIL' 'lane-guard pattern not found' }
}
Check 'Guards' 'commit.ps1 encoding+size guard' {
  if (-not $commitSrc) { return Res 'FAIL' 'missing' }
  $hasSize = ($commitSrc -match '256' -and $commitSrc -match '1024')
  $hasEnc = ($commitSrc -match '0xEF' -or $commitSrc -match 'EF BF BD' -or $commitSrc -match 'UTF8Encoding')
  if ($hasSize -and $hasEnc) { Res 'PASS' '256KB cap + U+FFFD/utf8 scan present' }
  else { Res 'WARN' ('size=' + $hasSize + ' enc=' + $hasEnc) }
}
Check 'Guards' 'commit.ps1 concurrency (mutex)' {
  if (-not $commitSrc) { return Res 'FAIL' 'missing' }
  if ($commitSrc -match 'Mutex' -and $commitSrc -match 'hub-git-commit') { Res 'PASS' 'global commit mutex present' }
  else { Res 'WARN' 'commit mutex not found (index.lock races possible)' }
}
Check 'Guards' 'commit.ps1 per-AI attribution' {
  if (-not $commitSrc) { return Res 'FAIL' 'missing' }
  $n = ([regex]::Matches($commitSrc, '@2nd-b\.ai')).Count
  if ($n -ge 4) { Res 'PASS' ($n.ToString() + ' @2nd-b.ai identities') }
  else { Res 'WARN' ('only ' + $n + ' canonical identities found') }
}
if ($Deep) {
  Check 'Guards' 'commit.ps1 lane-guard BEHAVIORAL (temp repo)' {
    $cp = Join-Path $toolsDir 'commit.ps1'
    if (-not (Test-Path $cp)) { return Res 'FAIL' 'missing' }
    $tmp = Join-Path $env:TEMP ('hubhealth-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    try {
      New-Item -ItemType Directory -Force $tmp | Out-Null
      Push-Location $tmp
      git init -q 2>$null | Out-Null
      git config user.email 't@t' 2>$null; git config user.name 't' 2>$null
      New-Item -ItemType Directory -Force (Join-Path $tmp 'agents/claude') | Out-Null
      Set-Content (Join-Path $tmp 'agents/claude/x.md') 'x' -Encoding UTF8
      Copy-Item $cp (Join-Path $tmp 'commit.ps1')
      $before = (git rev-list --count HEAD 2>$null); if (-not $before) { $before = 0 }
      & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tmp 'commit.ps1') -As codex -Message 'should reject' -Files 'agents/claude/x.md' 2>&1 | Out-Null
      $rc = $LASTEXITCODE
      $after = (git rev-list --count HEAD 2>$null); if (-not $after) { $after = 0 }
      Pop-Location; Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
      if ($rc -ne 0 -and $after -eq $before) { Res 'PASS' ('codex blocked from agents/claude/ (exit ' + $rc + ', no commit)') }
      else { Res 'FAIL' ('guard did not block: rc=' + $rc + ' commits ' + $before + '->' + $after) }
    } catch { try { Pop-Location } catch {}; Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue; Res 'WARN' ('temp-repo test skipped: ' + $_.Exception.Message) }
  }
}

# =====================================================================
# AREA: State + Models
# =====================================================================
function Get-Front2([string]$rel, [string]$key) {
  $p = Join-Path $root $rel; if (-not (Test-Path $p)) { return $null }
  $h = Get-Content $p -Encoding UTF8 -TotalCount 14
  $m = $h | Select-Object -First 14 | Select-String -Pattern ('^' + $key + ':\s*"?(.*?)"?\s*$') | Select-Object -First 1
  if ($m) { return $m.Matches[0].Groups[1].Value } return ''
}
Check 'State' 'CONTROL.md run-state' {
  if (-not (Test-Path (Join-Path $root 'CONTROL.md'))) { return Res 'FAIL' 'missing' }
  $owner = Get-Front2 'CONTROL.md' 'owner'; $state = Get-Front2 'CONTROL.md' 'state'
  if ($owner -ne 'claude') { return Res 'WARN' ("owner=" + $owner + " (expected claude)") }
  if ($state -notin @('running', 'paused', 'draining')) { return Res 'FAIL' ("unparseable state=" + $state) }
  if ($state -eq 'paused' -and -not (Get-Front2 'CONTROL.md' 'pause_reason')) { return Res 'WARN' 'paused but no pause_reason' }
  Res 'PASS' ('state=' + $state + ', owner=claude')
}
Check 'State' 'BOARD.md single-writer = claude' {
  if (-not (Test-Path (Join-Path $root 'BOARD.md'))) { return Res 'FAIL' 'missing' }
  $owner = Get-Front2 'BOARD.md' 'owner'
  $g = Invoke-GitRO @('log', '--format=%ae', '--', 'BOARD.md')
  $authors = @()
  if (-not $g.TimedOut -and $g.Code -eq 0) { $authors = @($g.Out -split "`r?`n" | Where-Object { $_ } | Sort-Object -Unique) }
  $rivals = @($authors | Where-Object { $_ -match 'codex@2nd-b\.ai|grok@2nd-b\.ai|antigravity@2nd-b\.ai' })
  if ($owner -ne 'claude') { Res 'FAIL' ('owner=' + $owner) }
  elseif ($rivals.Count -gt 0) { Res 'FAIL' ('rival author(s): ' + ($rivals -join ',')) }
  else { Res 'PASS' 'owner=claude, no rival-AI authors' }
}
Check 'Models' 'models.json best-model contract' {
  $p = Join-Path $toolsDir 'models.json'
  if (-not (Test-Path $p)) { return Res 'FAIL' 'tools/models.json missing' }
  try { $m = Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return Res 'FAIL' 'invalid json' }
  # Value-asserting (2026-06-17): not just presence — the pinned id+effort must MATCH the
  # canonical target. A hallucinated/wrong id (gpt-6, grok-4.3) would otherwise PASS a
  # presence-only check and reach the daemon = silent death (grok-4.3 incident). Bump this
  # map when the contract is intentionally upgraded.
  $expect = @{
    claude      = @('claude-fable-5','max')   # re-pinned 2026-07-03: fable available again (was opus-4-8 while fable was down)
    codex       = @('gpt-5.5','medium')
    grok        = @('grok-build','high')
    antigravity = @('gemini-3.1-pro-preview','high')
  }
  $deny = @('grok-4.3','grok-4','gemini-3.5-flash','gpt-6')
  $bad = @()
  foreach ($ai in $expect.Keys) {
    if (-not $m.$ai -or -not $m.$ai.model -or -not $m.$ai.effort) { $bad += ($ai + ':missing'); continue }
    if ([string]$m.$ai.model  -ne $expect[$ai][0]) { $bad += ($ai + ':model='  + $m.$ai.model  + '!=' + $expect[$ai][0]) }
    if ([string]$m.$ai.effort -ne $expect[$ai][1]) { $bad += ($ai + ':effort=' + $m.$ai.effort + '!=' + $expect[$ai][1]) }
    if ($deny -contains [string]$m.$ai.model) { $bad += ($ai + ':DENY-LISTED ' + $m.$ai.model) }
  }
  if ([string]$m.antigravity.agy_model -ne 'Gemini 3.1 Pro (High)') { $bad += ('antigravity:agy_model=' + $m.antigravity.agy_model) }
  if ($bad.Count -gt 0) { Res 'FAIL' (($bad | Select-Object -First 4) -join ' | ') }
  else { Res 'PASS' 'contract OK: codex=gpt-5.5/medium grok=grok-build/high AG=gemini-3.1-pro-preview/high claude=fable-5/max' }
}
Check 'Models' 'MODELS.md present' {
  if (Test-Path (Join-Path $root 'MODELS.md')) { Res 'PASS' 'doc present' } else { Res 'WARN' 'MODELS.md missing (json is source of truth)' }
}
Check 'State' 'agent layout + STATUS hygiene' {
  $bad = @(); $big = @()
  foreach ($a in @('claude', 'codex', 'antigravity', 'grok')) {
    $sf = Join-Path $root ("agents/$a/STATUS.md"); $ob = Join-Path $root ("agents/$a/outbox")
    if (-not (Test-Path $sf)) { $bad += ($a + '/STATUS') }
    elseif ((Get-Item $sf).Length -gt 256 * 1024) { $big += $a }
    if (-not (Test-Path $ob)) { $bad += ($a + '/outbox') }
  }
  if ($bad.Count -gt 0) { Res 'FAIL' ('missing: ' + ($bad -join ', ')) }
  elseif ($big.Count -gt 0) { Res 'WARN' ('STATUS > 256KB: ' + ($big -join ', ')) }
  else { Res 'PASS' '4 agents: STATUS + outbox present, sizes OK' }
}
Check 'State' 'outbox frontmatter contract' {
  $files = Get-ChildItem (Join-Path $root 'agents') -Recurse -Filter *.md -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match 'outbox' -and $_.FullName -notmatch '\\preview\\' -and $_.Name -ne 'README.md' }
  $bad = 0; $total = 0
  foreach ($f in $files) {
    # Frontmatter contract established 2026-06-15 (INCIDENTS) -- older messages are
    # grandfathered legacy, not violations. Count only date-prefixed post-contract files.
    if (-not ($f.Name -match '^(\d{8})') -or [int]$matches[1] -lt 20260615) { continue }
    $total++
    $h = Get-Content $f.FullName -Encoding UTF8 -TotalCount 14
    if (-not ($h -join "`n").StartsWith('---')) { $bad++; continue }
    $type = ($h | Select-String '^type:\s*"?(.*?)"?\s*$' | Select-Object -First 1)
    if ($type -and $type.Matches[0].Groups[1].Value -eq 'request') {
      foreach ($k in @('to', 'from', 'status')) { if (-not ($h | Select-String ('^' + $k + ':'))) { $bad++; break } }
    }
  }
  if ($bad -gt 0) { Res 'WARN' ($bad.ToString() + ' / ' + $total + ' post-contract (2026-06-15+) messages malformed/missing keys') }
  else { Res 'PASS' ($total.ToString() + ' post-contract outbox messages well-formed (pre-contract legacy exempt)') }
}

# =====================================================================
# AREA: Git + encoding
# =====================================================================
Check 'Git' 'hub repo + tree integrity' {
  $rp = Invoke-GitRO @('rev-parse', '--is-inside-work-tree')
  if ($rp.TimedOut) { return Res 'WARN' 'git busy (lock) - rev-parse skipped, re-checks next run' }
  if ($rp.Out.Trim() -ne 'true') { return Res 'FAIL' 'not a git work tree' }
  # O-19: distinguish an active committer's transient lock from a stale one (dead committer).
  $lock = Join-Path $root '.git/index.lock'
  if (Test-Path $lock) {
    $age = ((Get-Date) - (Get-Item $lock).LastWriteTime).TotalSeconds
    if ($age -lt 30) { return Res 'WARN' ('commit in progress (transient index.lock, ' + [int]$age + 's) - skipped') }
    return Res 'FAIL' ('stale .git/index.lock (' + [int]$age + 's, dead committer)')
  }
  $st = Invoke-GitRO @('status', '--porcelain')
  if ($st.TimedOut) { return Res 'WARN' 'git status busy (lock) - skipped, re-checks next run' }
  if ($st.Code -ne 0) { Res 'FAIL' 'git status failed' } else { Res 'PASS' 'work tree clean-readable, no index.lock' }
}
Check 'Git' 'UTF-8 no-BOM integrity (focused set)' {
  $targets = @()
  $targets += @('CONTROL.md', 'BOARD.md', 'PROTOCOL.md', 'MODELS.md') | ForEach-Object { Join-Path $root $_ }
  $targets += (Get-ChildItem $toolsDir -Filter *.ps1 -File | ForEach-Object { $_.FullName })
  $targets += (Get-ChildItem $toolsDir -Filter *.json -File | ForEach-Object { $_.FullName })
  $targets += (Get-ChildItem (Join-Path $root 'prompts') -Filter *.md -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
  $targets += @('claude', 'codex', 'antigravity', 'grok') | ForEach-Object { Join-Path $root "agents/$_/STATUS.md" }
  $bad = @()
  foreach ($t in ($targets | Where-Object { $_ -and (Test-Path $_) })) {
    $c = Test-Utf8Clean $t; if (-not $c.ok) { $bad += ((Split-Path $t -Leaf) + ': ' + $c.why) }
  }
  if ($bad.Count -gt 0) { Res 'FAIL' (($bad | Select-Object -First 3) -join ' | ') }
  else { Res 'PASS' ('checked ' + ($targets.Count) + ' files, all UTF-8 no-BOM') }
}

# =====================================================================
# AREA: Liveness
# =====================================================================
Check 'Liveness' 'daemon heartbeat + process' {
  $dlog = Join-Path $toolsDir 'hub-daemon.log'
  $ageMsg = 'no daemon log'; $fresh = $false
  if (Test-Path $dlog) {
    $last = Read-SharedLog $dlog 40 | Where-Object { $_ -match '^\[' } | Select-Object -Last 1
    if ($last -match '^\[([^\]]+) KST\]') {
      try {
        $ts = [datetime]::Parse(($matches[1] -replace '/', '').Trim())
        $age = ((Get-Date) - $ts).TotalMinutes
        $fresh = ($age -lt $MaxAgeMin)
        $ageMsg = ('{0:n0}m ago' -f $age)
      } catch { $ageMsg = 'unparseable stamp' }
    }
  }
  $proc = @()
  try { $proc = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'hub-daemon\.ps1' }) } catch {}
  if ($fresh -and $proc.Count -gt 0) { Res 'PASS' ('daemon alive (' + $ageMsg + ', ' + $proc.Count + ' proc)') }
  elseif ($proc.Count -gt 0) { Res 'WARN' ('daemon proc up but log stale (' + $ageMsg + ')') }
  else { Res 'WARN' ('no daemon running (log ' + $ageMsg + ') - in-window/manual mode?') }
}

# =====================================================================
# OUTPUT
# =====================================================================
$pass = @($script:results | Where-Object { $_.Status -eq 'PASS' }).Count
$warn = @($script:results | Where-Object { $_.Status -eq 'WARN' }).Count
$fail = @($script:results | Where-Object { $_.Status -eq 'FAIL' }).Count
$stamp = Get-Date -Format 'yyyy-MM-dd / HH:mm:ss'

if ($Json) {
  [pscustomobject]@{ generated = "$stamp KST"; pass = $pass; warn = $warn; fail = $fail; results = $script:results } | ConvertTo-Json -Depth 5
} else {
  $bar = ('=' * 78)
  Write-Host $bar -ForegroundColor Cyan
  Write-Host ("  AI HUB HEALTH     {0} KST     (read-only{1})" -f $stamp, $(if ($Deep) { ' +deep' } else { '' })) -ForegroundColor Cyan
  Write-Host $bar -ForegroundColor Cyan
  $lastArea = ''
  foreach ($r in $script:results) {
    if ($r.Area -ne $lastArea) { Write-Host ("-- " + $r.Area + " " + ('-' * [Math]::Max(1, 72 - $r.Area.Length))) -ForegroundColor DarkGray; $lastArea = $r.Area }
    $col = switch ($r.Status) { 'PASS' { 'Green' } 'WARN' { 'Yellow' } 'SKIP' { 'DarkGray' } default { 'Red' } }
    Write-Host ("  {0,-5} {1,-40} {2}" -f $r.Status, $r.Name, $r.Detail) -ForegroundColor $col
  }
  Write-Host $bar -ForegroundColor Cyan
  $sumCol = if ($fail -gt 0) { 'Red' } elseif ($warn -gt 0) { 'Yellow' } else { 'Green' }
  Write-Host ("  hub-health: PASS={0}  WARN={1}  FAIL={2}   @ {3} KST" -f $pass, $warn, $fail, $stamp) -ForegroundColor $sumCol
}

if ($fail -gt 0) { exit 1 } elseif ($StrictWarn -and $warn -gt 0) { exit 1 } else { exit 0 }
