# multi-terminal-launch.ps1 — Windows Terminal 기반 multi-task launcher
#
# 사용:
#   .\multi-terminal-launch.ps1 -ConfigPath dispatch.json
#   .\multi-terminal-launch.ps1 -Tasks @(...) -DryRun
#
# Config JSON 예시 (model-router 출력):
# {
#   "dispatch_id": "v25-multi-001",
#   "tasks": [
#     {"id": "t1", "type": "CODE_NEW", "model": "claude-sonnet-4-6", "prompt": "...", "cwd": "C:\\repo1"},
#     {"id": "t2", "type": "RESEARCH", "model": "claude-opus-4-7", "prompt": "...", "cwd": "C:\\repo2"}
#   ]
# }
#
# 환경 요건:
#   - Windows Terminal (wt.exe) — Windows 11 기본 / 또는 winget install Microsoft.WindowsTerminal
#   - Claude Code CLI (`claude`) — 또는 다른 model CLI (gemini, openai 등)
#
# 안전 가드:
#   - DryRun 모드: 실행 X, 명령만 출력
#   - Cost > $5 시 사용자 confirm 요구
#   - 파괴적 keyword (rm -rf, force push, DROP TABLE) 감지 시 STOP

param(
    [Parameter(Mandatory=$false)][string]$ConfigPath = $null,
    [Parameter(Mandatory=$false)][array]$Tasks = @(),
    [switch]$DryRun = $false,
    [switch]$Verbose = $false,
    [int]$CostThreshold = 5  # USD
)

$ErrorActionPreference = "Stop"

# --- 1. Config load ---
if ($ConfigPath -and (Test-Path $ConfigPath)) {
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    $Tasks = $config.tasks
    Write-Host "[load] $ConfigPath ($($Tasks.Count) tasks, dispatch_id: $($config.dispatch_id))"
} elseif ($Tasks.Count -eq 0) {
    Write-Error "ConfigPath 또는 Tasks 필요"
    exit 1
}

# --- 2. Cost estimate (rough) ---
$PriceTable = @{
    'claude-opus-4-7'       = @{ 'in' = 15; 'out' = 75 }
    'claude-sonnet-4-6'     = @{ 'in' = 3;  'out' = 15 }
    'claude-haiku-4-5-20251001' = @{ 'in' = 1;  'out' = 5 }
    'gpt-5.4'               = @{ 'in' = 5;  'out' = 30 }
    'gpt-5.3-codex'         = @{ 'in' = 4;  'out' = 20 }
    'gpt-5'                 = @{ 'in' = 5;  'out' = 25 }
    'gemini-3.1-pro'        = @{ 'in' = 7;  'out' = 21 }
    'gemini-3.5-flash'      = @{ 'in' = 0.3; 'out' = 2 }
    'grok-4'                = @{ 'in' = 5;  'out' = 25 }
    'deepseek-v3'           = @{ 'in' = 0.27; 'out' = 1.10 }
    'glm-5'                 = @{ 'in' = 0.6; 'out' = 2.5 }
}

$TotalCost = 0
$EstimateRows = @()
foreach ($task in $Tasks) {
    # Default token estimate (override 가능)
    $inTok = if ($task.input_tokens) { $task.input_tokens } else { 50000 }
    $outTok = if ($task.output_tokens) { $task.output_tokens } else { 20000 }
    $modelId = $task.model
    if ($PriceTable.ContainsKey($modelId)) {
        $price = $PriceTable[$modelId]
        $cost = ($inTok / 1000000 * $price['in']) + ($outTok / 1000000 * $price['out'])
    } else {
        $cost = 0
        Write-Warning "Unknown model price: $modelId (cost estimate skip)"
    }
    $TotalCost += $cost
    $EstimateRows += [PSCustomObject]@{
        TaskID = $task.id
        Type = $task.type
        Model = $modelId
        InTok = $inTok
        OutTok = $outTok
        Cost = "`$$([math]::Round($cost, 3))"
    }
}

Write-Host "`n=== Dispatch Plan ===" -ForegroundColor Cyan
$EstimateRows | Format-Table -AutoSize
Write-Host "Total estimated cost: `$$([math]::Round($TotalCost, 2))" -ForegroundColor Yellow

# --- 3. Safety guard: cost threshold ---
if ($TotalCost -gt $CostThreshold) {
    if (-not $DryRun) {
        $confirm = Read-Host "Total cost `$$([math]::Round($TotalCost, 2)) > `$$CostThreshold threshold. Proceed? (y/N)"
        if ($confirm -notmatch '^[yY]') {
            Write-Host "Aborted by user (cost guard)" -ForegroundColor Red
            exit 0
        }
    } else {
        Write-Warning "[DRY-RUN] Cost > threshold would require confirmation"
    }
}

# --- 4. Safety guard: destructive keywords ---
$DestructivePatterns = @('rm\s+-rf', 'git\s+push\s+--force', 'DROP\s+TABLE', 'reset\s+--hard', 'rd\s+/s\s+/q')
foreach ($task in $Tasks) {
    foreach ($pat in $DestructivePatterns) {
        if ($task.prompt -match $pat) {
            Write-Error "Destructive pattern '$pat' in task $($task.id). dispatch X — manually single-terminal."
            exit 2
        }
    }
}

# --- 5. Launch each task in Windows Terminal tab ---
if (-not (Get-Command wt.exe -ErrorAction SilentlyContinue)) {
    Write-Warning "Windows Terminal (wt.exe) not found. Falling back to Start-Process."
    $UseStartProcess = $true
} else {
    $UseStartProcess = $false
}

foreach ($task in $Tasks) {
    $title = "$($task.id)-$($task.model.Split('-')[1..2] -join '-')"
    $cwd = if ($task.cwd) { $task.cwd } else { (Get-Location).Path }
    # Claude Code CLI: claude --model <id> "<prompt>"
    # 다른 model: 추후 mapping (gpt-5 → openai cli, gemini → antigravity cli 등)
    $cmd = "claude --model $($task.model) `"$($task.prompt -replace '"','`"')`""

    if ($DryRun) {
        Write-Host "[DRY-RUN] would launch: $title" -ForegroundColor Magenta
        Write-Host "  cwd: $cwd"
        Write-Host "  cmd: $cmd"
        continue
    }

    if ($UseStartProcess) {
        # Fallback: separate PowerShell window
        Start-Process pwsh -ArgumentList "-NoExit", "-WorkingDirectory", $cwd, "-Command", $cmd -WindowStyle Normal
        Write-Host "[launched] $title (PowerShell window, fallback)" -ForegroundColor Green
    } else {
        # Windows Terminal new tab
        $wtArgs = @('-w', '0', 'new-tab', '-p', 'PowerShell', '-d', $cwd, '--title', $title, 'pwsh', '-NoExit', '-Command', $cmd)
        & wt.exe $wtArgs
        Write-Host "[launched] $title (wt tab)" -ForegroundColor Green
    }
    Start-Sleep -Milliseconds 300  # Stagger
}

Write-Host "`n[done] $($Tasks.Count) terminals launched. Observe each window for output." -ForegroundColor Cyan
Write-Host "Total estimated cost: `$$([math]::Round($TotalCost, 2))" -ForegroundColor Yellow
