# Switch the eight /vibe user-home junctions (Claude vibe, vibe-bot, model-router, simonk,
# multi-terminal-dispatcher, qa; Codex vibe, vibe-bot) and the Codex /vibe config line
# from the installed candidate to <Tag>-candidate.
# Default: preview (no writes). -Apply checks topology and tree digests, moves the old links
# to ~/.claude/flat-link-archive/vibe-<Tag> (never deletes), links the new candidate, re-checks
# digests and rolls back automatically on any failure. Refuses while a vibe run is open,
# an attempt is active or the budget is halted. -OldTag defaults to the installed candidate.
# Use PowerShell 7: pwsh -NoProfile -NonInteractive -File scripts/windows/install-junctions.ps1 -Tag <tag>
[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory = $true)] [string] $Tag,
    [string] $OldTag,
    [string] $ReleasesDir,
    [string] $UserHome,
    [string] $CodexHome,
    [string] $Decision = 'manual',
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
    $userHomeDir = Resolve-SkUserHome $UserHome
    $codexDir = if ($CodexHome) { [IO.Path]::GetFullPath($CodexHome).TrimEnd('\') } else { Join-Path $userHomeDir '.codex' }
    $releases = Resolve-SkReleasesDir $ReleasesDir (Get-SkInstalledCandidate $userHomeDir)
    if ($Apply) { $lock = Enter-SkInstallLock }
    $stage = 'swap'
    $result = Invoke-SkJunctionSwap -Tag $Tag -OldTag $OldTag -ReleasesDir $releases -UserHome $userHomeDir `
        -CodexHome $codexDir -Decision $Decision -Apply:$Apply
    $result.Remove('undo')
    $result.agy = Get-SkAgyLinks $userHomeDir
    Write-SkJson $result
    $exitCode = 0
} catch {
    $message = $_.Exception.Message
    $code = if ($message -match '^([A-Z][A-Z0-9_]+):') { $Matches[1] } else { 'UNEXPECTED' }
    [Console]::Out.WriteLine((@{ status = 'blocked'; error = $code; detail = $message; stage = $stage } | ConvertTo-Json -Compress))
    $exitCode = if ($code -eq 'ROLLBACK_FAILED') { 3 } else { 2 }
} finally {
    if ($lock) { Exit-SkInstallLock $lock }
}
exit $exitCode
