# simonk.ps1 — PowerShell entry point for the simonK unified harness
#
# Sourced from $PROFILE (one-time install via scripts/install-simonk-profile.ps1).
# Defines a global `simonK` function callable from any PowerShell session.
#
# Usage:
#   simonK <task description>     → non-interactive: launches `claude -p "/simonK <task>"`
#   simonK                        → interactive: opens `claude` in C:\Coding
#
# Project root default: C:\Coding (overridable via $env:SIMONK_PROJECT_DIR)
# Wiki vault default: $env:SIMON_WIKI_DIR (set during 2026-05-23 vault consolidation)
#
# Auto helpers (silent if OK, 안내만 출력):
#   - gcloud-bootstrap : Google Cloud SDK 인증 + project + ADC 자동 진단·inject
#                        (사용자 인터랙션 = 첫 1회 `gcloud auth login` browser OAuth만)

# Load helper functions (silent dot-source)
$_simonkScriptDir = $PSScriptRoot
$_gcloudBootstrap = Join-Path $_simonkScriptDir 'gcloud-bootstrap.ps1'
if (Test-Path $_gcloudBootstrap) { . $_gcloudBootstrap }

function global:simonK {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $TaskArgs
    )

    $task = if ($TaskArgs) { ($TaskArgs -join ' ').Trim() } else { '' }
    $projectDir = if ($env:SIMONK_PROJECT_DIR) { $env:SIMONK_PROJECT_DIR } else { 'C:\Coding' }

    if (-not (Test-Path $projectDir)) {
        Write-Host "[simonK] project dir not found: $projectDir" -ForegroundColor Red
        return
    }

    $claude = Get-Command claude -ErrorAction SilentlyContinue
    if (-not $claude) {
        Write-Host "[simonK] 'claude' CLI not found on PATH. Install Claude Code first." -ForegroundColor Red
        return
    }

    # Auto: gcloud 인증 진단 + ADC + project 자동 inject (silent if OK)
    if (Get-Command Invoke-GcloudBootstrap -ErrorAction SilentlyContinue) {
        Invoke-GcloudBootstrap -Silent | Out-Null
    }

    Push-Location $projectDir
    try {
        if (-not $task) {
            Write-Host "[simonK] interactive mode @ $projectDir" -ForegroundColor Cyan
            Write-Host "         use '/simonK <task>' inside the session to trigger the harness" -ForegroundColor DarkGray
            & claude
        } else {
            Write-Host "[simonK] task: $task" -ForegroundColor Cyan
            Write-Host "[simonK] dispatching: claude -p '/simonK $task'" -ForegroundColor DarkGray
            & claude -p "/simonK $task"
        }
    } finally {
        Pop-Location
    }
}

# Expose Invoke-GcloudBootstrap as a global helper (수동 호출용)
if (Get-Command Invoke-GcloudBootstrap -ErrorAction SilentlyContinue) {
    Set-Item function:global:simonk-gcloud-check (Get-Command Invoke-GcloudBootstrap).ScriptBlock
}

# PowerShell function/command lookup is case-insensitive — `simonK`, `simonk`, `SIMONK`
# all resolve to the function above. No aliases needed; aliases here would create a
# circular self-reference because alias names collapse to the same case-insensitive key.
