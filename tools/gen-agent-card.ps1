# gen-agent-card.ps1 -- write an A2A-style capability card for a lane (audit H4).
# ASCII-only. Each AI runs this with -As <self> to (re)write ONLY agents/<self>/agent-card.json
# (single-writer preserved). Gives the orchestrator/routing a MACHINE-READABLE per-agent manifest
# (skills array + live model + status) so lane selection can be programmatic instead of prose-only.
# A2A-shaped: { name, role, skills[], status, model, effort, reroute_to, updated }.
#
#   powershell -ExecutionPolicy Bypass -File tools/gen-agent-card.ps1 -As claude
#   powershell -ExecutionPolicy Bypass -File tools/gen-agent-card.ps1 -As codex -Status quota
param(
  [Parameter(Mandatory=$true)][ValidateSet('claude','codex','antigravity','grok')][string]$As,
  [string]$Status = 'active'
)
$utf8 = [System.Text.UTF8Encoding]::new($false)
$root = Split-Path $PSScriptRoot -Parent

# skills per ROUTING.md role definitions (static, well-known 4-agent set).
$skills = @{
  claude      = @('orchestration','coding','architecture','merge-gate','online-git','review','security','ai-debate-judge')
  codex       = @('ui-ux','images','aesthetics','i18n','multimodal-gen','test-authoring','verify-safety')
  antigravity = @('android-native','google-native','emulator-qa','device-qa','perf','crash-analysis','multimodal-render')
  grok        = @('x-social-research','consumer-signal','trend-monitoring','external-fact-verify')
}
$roles = @{
  claude='orchestrator + main coder + merge gate'; codex='UI/UX + images + tests'
  antigravity='Android/Google native + emulator/device QA'; grok='X/social + consumer research (request-only)'
}

# live model/effort from models.json (source of truth)
$model = ''; $effort = ''; $reroute = ''
try {
  $mj = Get-Content (Join-Path $PSScriptRoot 'models.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($mj.$As) { $model = [string]$mj.$As.model; $effort = [string]$mj.$As.effort; if ($mj.$As.reroute_to) { $reroute = [string]$mj.$As.reroute_to } }
} catch {}

$card = [ordered]@{
  name       = $As
  role       = $roles[$As]
  skills     = $skills[$As]
  status     = $Status            # active | quota | parked | paused
  model      = $model
  effort     = $effort
  reroute_to = $reroute
  updated    = (Get-Date -Format 's') + ' KST'
}

$dir = Join-Path $root ("agents/" + $As)
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$out = Join-Path $dir 'agent-card.json'
[System.IO.File]::WriteAllText($out, ($card | ConvertTo-Json -Depth 4), $utf8)
Write-Host "[gen-agent-card] wrote $out  (skills: $($skills[$As] -join ', '); model: $model $effort; status: $Status)" -ForegroundColor Green
