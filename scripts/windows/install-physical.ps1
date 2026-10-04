# Replace physical skill folders in ~/.claude/skills with byte-exact copies of
# skills-src/<name> at a commit, but only where the installed bytes differ from it.
# Default: preview (no writes except `git fetch`). -Apply stages the git blobs, verifies
# their ids, moves the current folder to ~/.claude/flat-link-archive/<name>-<ArchiveTag>
# (never deletes) and rolls back every replaced skill if any step fails.
# Use PowerShell 7: pwsh -NoProfile -NonInteractive -File scripts/windows/install-physical.ps1
[CmdletBinding(PositionalBinding = $false)]
param(
    [string[]] $Skills = @('ai-debate', 'careful', 'freeze', 'guard', 'unfreeze'),
    [string] $RepoRoot,
    [string] $Ref = 'origin/main',
    [string] $UserHome,
    [string] $ArchiveTag,
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
    # pwsh -File passes "a,b" as one string; accept both forms.
    $names = @($Skills | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($Apply) { $lock = Enter-SkInstallLock }
    if (-not $NoFetch) { $null = Invoke-SkGit $repo @('fetch', '-q', 'origin') }
    $sha = Resolve-SkCommit $repo $Ref
    if (-not $ArchiveTag) { $ArchiveTag = (Get-SkKstNow).ToString('yyMMdd-HHmm') + '-' + $sha.Substring(0, 7) }
    $stage = 'sync'
    $result = Invoke-SkPhysicalSync -RepoRoot $repo -Commit $sha -Skills $names -UserHome $userHomeDir -ArchiveTag $ArchiveTag -Apply:$Apply
    $result.Remove('undo')
    $result.main = $sha
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
