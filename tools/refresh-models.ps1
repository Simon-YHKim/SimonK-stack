# refresh-models.ps1 -- Daily benchmark refresh for the hub's best-model config.
# Researches the current highest-benchmark model + max effort per provider via a
# web-capable headless AI (gemini -> grok fallback), then PROPOSES an update to
# tools/models.json. It does NOT overwrite the live source of truth: a wrong/
# hallucinated model id would break every daemon spawn, so application is gated.
# Output: tools/models.proposed.json + a log line + an inbox note to Claude, who
# (or Simon) reviews and applies. Subscription CLIs => no token cost.
# ASCII-only source (PS 5.1 no-BOM safe).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File "tools/refresh-models.ps1"
# Scheduled daily by the 'HubModelBenchmarkRefresh' Windows task (see install note at bottom).
param([int]$TimeoutSec = 180)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
$stamp = Get-Date -Format 'yyyy-MM-dd / HH:mm:ss'
$today = Get-Date -Format 'yyyy-MM-dd'
$log = Join-Path $PSScriptRoot 'models-refresh.log'
function LogLine([string]$m) { $l = "[$stamp KST] $m"; Write-Host $l; try { Add-Content -LiteralPath $log -Value $l -Encoding utf8 } catch {} }

$prompt = "Today is $today. You have web/Google search - USE IT to confirm what is current. For a multi-AI coding hub, find the single HIGHEST-BENCHMARK model AND the exact MAX reasoning-effort setting currently available for each CLI as of today: (1) Anthropic Claude Code, (2) OpenAI Codex CLI, (3) xAI grok CLI, (4) Google gemini / Antigravity agy CLI. Output ONLY a compact JSON object, no prose, no markdown fences, with top-level keys claude, codex, grok, antigravity. Each value is an object with fields: model (exact id string the CLI accepts), effort (exact max effort flag or value), reason (one short line citing the benchmark and release date). Prefer official docs and reputable leaderboards. Begin your reply with the open brace."

LogLine "refresh START (provider best-model research via headless AI)"

# --- spawn a web-capable AI; gemini first (Google search grounding), grok fallback ---
$raw = ''
$used = ''
function Spawn([string]$exe, [string[]]$pre) {
  if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { return $null }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $exe
  $psi.Arguments = (@($pre) -join ' ')
  $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
  $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
  try { $p = [System.Diagnostics.Process]::Start($psi) } catch { return $null }
  try { $p.StandardInput.Write($script:prompt); $p.StandardInput.Close() } catch {}
  $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
  if (-not $p.WaitForExit($TimeoutSec * 1000)) { try { $p.Kill() } catch {}; return $null }
  return ([string]$so.Result + "`n" + [string]$se.Result)
}
$script:prompt = $prompt

# gemini -m gemini-3.1-pro-preview -p "<prompt>" -y  (pass prompt as arg; -y auto-approve)
if (Get-Command gemini -ErrorAction SilentlyContinue) {
  $used = 'gemini'
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = 'gemini'; $psi.Arguments = '-m gemini-3.1-pro-preview -p "' + ($prompt -replace '"', '\"') + '" -y'
  $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
  try {
    $p = [System.Diagnostics.Process]::Start($psi)
    $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
    if ($p.WaitForExit($TimeoutSec * 1000)) { $raw = [string]$so.Result } else { try { $p.Kill() } catch {} }
  } catch { $raw = '' }
}
if (-not ($raw -match '\{')) {
  if (Get-Command grok -ErrorAction SilentlyContinue) {
    $used = 'grok'
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'grok'; $psi.Arguments = '-p "' + ($prompt -replace '"', '\"') + '"'
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    try {
      $p = [System.Diagnostics.Process]::Start($psi)
      $so = $p.StandardOutput.ReadToEndAsync()
      if ($p.WaitForExit($TimeoutSec * 1000)) { $raw = [string]$so.Result } else { try { $p.Kill() } catch {} }
    } catch { $raw = '' }
  }
}

if (-not ($raw -match '\{')) { LogLine "refresh FAIL: no JSON from headless AI ($used). Nothing written."; exit 1 }

# --- extract the JSON object (first '{' .. last '}') and validate ---
$jsonText = $raw.Substring($raw.IndexOf('{'), ($raw.LastIndexOf('}') - $raw.IndexOf('{') + 1))
$parsed = $null
try { $parsed = $jsonText | ConvertFrom-Json } catch { LogLine "refresh FAIL: AI output not valid JSON. Raw saved to models.proposed.raw.txt"; Set-Content (Join-Path $PSScriptRoot 'models.proposed.raw.txt') $raw -Encoding UTF8; exit 1 }
$miss = @('claude', 'codex', 'grok', 'antigravity') | Where-Object { -not $parsed.$_ -or -not $parsed.$_.model -or -not $parsed.$_.effort }
if ($miss.Count -gt 0) { LogLine ("refresh FAIL: proposal incomplete for " + ($miss -join ', ')); Set-Content (Join-Path $PSScriptRoot 'models.proposed.raw.txt') $raw -Encoding UTF8; exit 1 }

# --- compare vs current models.json ---
$curFile = Join-Path $PSScriptRoot 'models.json'
$cur = $null; try { $cur = Get-Content $curFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch {}
$changes = @()
foreach ($ai in @('claude', 'codex', 'grok', 'antigravity')) {
  $cm = if ($cur) { $cur.$ai.model } else { '' }
  $ce = if ($cur) { $cur.$ai.effort } else { '' }
  if ($parsed.$ai.model -ne $cm) { $changes += ("$ai model: $cm -> " + $parsed.$ai.model) }
  if ($parsed.$ai.effort -ne $ce) { $changes += ("$ai effort: $ce -> " + $parsed.$ai.effort) }
}

# --- write proposal (NEVER overwrite live models.json automatically) ---
$proposal = [pscustomobject]@{
  _meta    = [pscustomobject]@{ proposed = "$stamp KST"; source = "refresh-models.ps1 via $used"; today = $today; apply = "Claude/Simon reviews; if sane, copy fields into tools/models.json + bump MODELS.md, then commit.ps1 -As claude" }
  claude   = $parsed.claude; codex = $parsed.codex; grok = $parsed.grok; antigravity = $parsed.antigravity
  changes  = $changes
}
$proposal | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $PSScriptRoot 'models.proposed.json') -Encoding UTF8

if ($changes.Count -eq 0) {
  LogLine "refresh OK: no change vs current models.json (still current). proposal written."
} else {
  LogLine ("refresh OK: " + $changes.Count + " change(s) PROPOSED -> " + ($changes -join ' ; '))
  # drop an inbox note so Claude's loop reviews + applies (gated, not auto-applied)
  $inbox = Join-Path $root 'agents/claude/inbox'
  if (Test-Path $inbox) {
    $note = Join-Path $inbox ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-from-refresh-models-benchmark-change.md')
    $body = "---`nfrom: refresh-models`nto: claude`ntype: request`nproject: hub`npriority: normal`ncreated: $stamp KST`n---`n`n## 일일 벤치마크 갱신 - 모델 변동 제안 ($used)`n`ntools/models.proposed.json 에 변동 " + $changes.Count + "건:`n`n- " + ($changes -join "`n- ") + "`n`n검토 후 sane하면 tools/models.json 에 반영 + MODELS.md last_checked 갱신 + commit.ps1 -As claude. 잘못된/환각 모델 id면 무시.`n"
    try { Set-Content $note $body -Encoding UTF8 } catch {}
  }
}
LogLine "refresh END"
exit 0

# --- Install the daily scheduled task (run once, from an elevated-or-user PowerShell) ---
# $action  = New-ScheduledTaskAction -Execute 'powershell' -Argument '-NoProfile -ExecutionPolicy Bypass -File "E:\Coding Infra\AI Infra\Communication\tools\refresh-models.ps1"'
# $trigger = New-ScheduledTaskTrigger -Daily -At 9:00am
# Register-ScheduledTask -TaskName 'HubModelBenchmarkRefresh' -Action $action -Trigger $trigger -Description 'Daily best-model benchmark refresh for the AI hub (proposes models.json update)'
