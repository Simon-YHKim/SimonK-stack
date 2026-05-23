# install-simonk-profile.ps1 — one-time installer for the `simonK` PowerShell entry
#
# What it does (idempotent):
#   1. Creates user PowerShell profile if missing
#   2. Appends a marker-guarded block that dot-sources simonk.ps1
#   3. Sets SIMONK_PROJECT_DIR env var (user scope) if not already set
#
# Run once: pwsh -File scripts/install-simonk-profile.ps1
#           (or)  powershell -ExecutionPolicy Bypass -File scripts/install-simonk-profile.ps1

$ErrorActionPreference = 'Stop'

$marker = '<!-- simonk-profile-block:v1 -->'
$repoRoot = Split-Path -Parent $PSScriptRoot
$simonkPath = Join-Path $repoRoot 'scripts\simonk.ps1'

if (-not (Test-Path $simonkPath)) {
    Write-Host "[install] simonk.ps1 not found at $simonkPath" -ForegroundColor Red
    exit 1
}

# Choose profile path - prefer CurrentUserAllHosts (works in any host)
$profilePath = if ($PROFILE.CurrentUserAllHosts) { $PROFILE.CurrentUserAllHosts } else { $PROFILE }
$profileDir = Split-Path -Parent $profilePath
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
}

# Idempotent: check if block already present
$existing = if (Test-Path $profilePath) { Get-Content $profilePath -Raw } else { '' }
if ($existing -match [regex]::Escape($marker)) {
    Write-Host "[install] simonk profile block already present in $profilePath" -ForegroundColor DarkGray
} else {
    $block = @"

# $marker
# Added by SimonK-stack/scripts/install-simonk-profile.ps1
if (Test-Path '$simonkPath') {
    . '$simonkPath'
}

"@
    Add-Content -Path $profilePath -Value $block
    Write-Host "[install] appended simonk profile block to $profilePath" -ForegroundColor Green
}

# Set SIMONK_PROJECT_DIR (user scope) if not already set
$existingEnv = [Environment]::GetEnvironmentVariable('SIMONK_PROJECT_DIR', 'User')
if (-not $existingEnv) {
    [Environment]::SetEnvironmentVariable('SIMONK_PROJECT_DIR', 'E:\Coding Infra', 'User')
    Write-Host "[install] set SIMONK_PROJECT_DIR=E:\Coding Infra (User scope)" -ForegroundColor Green
} else {
    Write-Host "[install] SIMONK_PROJECT_DIR already set: $existingEnv" -ForegroundColor DarkGray
}

# Load into current session immediately
. $simonkPath
Write-Host "[install] simonK function loaded into current session." -ForegroundColor Cyan
Write-Host "          Try: simonK 'test task'  (won't actually run claude — verify function exists)" -ForegroundColor DarkGray
Write-Host "          New PowerShell sessions will auto-load via $profilePath" -ForegroundColor DarkGray
