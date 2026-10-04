# Build and verify the four /vibe candidate packages (source, candidate-safety,
# codex-overlay-safety, codex-subset-safety) from a clean detached worktree at a commit.
# Default: preview (no writes except `git fetch` refreshing remote-tracking refs).
# -Apply builds into <ReleasesDir>\<Tag>-candidate and writes <Tag>-receipts.json last.
# Refuses when the candidate, src worktree or receipts already exist.
# Use PowerShell 7: pwsh -NoProfile -NonInteractive -File scripts/windows/build-candidate.ps1
[CmdletBinding(PositionalBinding = $false)]
param(
    [string] $RepoRoot,
    [string] $Ref = 'origin/main',
    [string] $Tag,
    [string] $ReleasesDir,
    [string] $PluginPins,
    [string] $UserHome,
    [double] $MinFreeMemoryGB = 3,
    [switch] $NoFetch,
    [switch] $Apply
)
$ErrorActionPreference = 'Stop'
$stage = 'start'
$exitCode = 2
$lock = $null
try {
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'POWERSHELL_7_REQUIRED: run with pwsh -NoProfile -File' }
    Import-Module (Join-Path $PSScriptRoot 'SimonKLocalInstall.psm1') -Force
    $stage = 'discover'
    $repo = Resolve-SkRepoRoot $RepoRoot
    $userHomeDir = Resolve-SkUserHome $UserHome
    if ($Apply) { $lock = Enter-SkInstallLock }
    if (-not $NoFetch) { $null = Invoke-SkGit $repo @('fetch', '-q', 'origin') }
    $sha = Resolve-SkCommit $repo $Ref
    $releases = Resolve-SkReleasesDir $ReleasesDir (Get-SkInstalledCandidate $userHomeDir)
    if (-not $Tag) { $Tag = New-SkCandidateTag $repo $sha }
    $stage = 'memory'
    $memory = [ordered]@{ free_gb = Get-SkFreeMemoryGB; min_gb = $MinFreeMemoryGB }
    if ($Apply) { Assert-SkFreeMemory $MinFreeMemoryGB }
    $stage = 'pins'
    $inputsJson = (Invoke-SkGit $repo @('show', "${sha}:distribution/plugin-inputs.v1.json")).Out -join "`n"
    $pins = Find-SkPluginPins $PluginPins $releases $inputsJson
    $stage = 'build'
    $result = Invoke-SkBuildCandidate -RepoRoot $repo -Commit $sha -Tag $Tag -ReleasesDir $releases -PluginPins $pins.path -Apply:$Apply
    $result.memory = $memory
    $result.plugin_pins_source = $pins.source
    Write-SkJson $result
    $exitCode = 0
} catch {
    $message = $_.Exception.Message
    $code = if ($message -match '^([A-Z][A-Z0-9_]+):') { $Matches[1] } else { 'UNEXPECTED' }
    [Console]::Out.WriteLine((@{ status = 'blocked'; error = $code; detail = $message; stage = $stage } | ConvertTo-Json -Compress))
    $exitCode = 2
} finally {
    if ($lock) { Exit-SkInstallLock $lock }
}
exit $exitCode
