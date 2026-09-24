# Compatibility facade; the matching skill-local script owns the wave policy.
# Invoke with pwsh -NoProfile -NonInteractive -File (do not dot-source).
# Preserve typed bindings, including explicitly empty or false legacy inputs.
[CmdletBinding(PositionalBinding = $false)]
param(
    [ValidateSet('preview', 'dispatch', 'reconcile')][string] $Action = 'preview',
    [string] $PlanPath,
    [string] $DbPath,
    [string] $CertificatesPath,
    [string[]] $Node,
    [switch] $DryRun,
    # Retained only to issue a closed migration error, including empty values.
    [string] $ConfigPath,
    [array] $Tasks,
    [double] $CostThreshold
)
$ErrorActionPreference = 'Stop'
$canonical = Join-Path $PSScriptRoot '../skills-src/multi-terminal-dispatcher/scripts/multi-terminal-launch.ps1'
if (-not (Test-Path -LiteralPath $canonical -PathType Leaf)) {
    [Console]::Out.WriteLine('{"status":"blocked","error":"WAVE_HELPER_UNAVAILABLE"}')
    exit 2
}
try {
    & $canonical @PSBoundParameters
    exit $LASTEXITCODE
} catch {
    [Console]::Out.WriteLine('{"status":"blocked","error":"WAVE_HELPER_FAILED"}')
    exit 2
}
