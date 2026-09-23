# Compatibility name: a guarded /vibe ready wave, not a terminal/window launcher.
# Invoke with pwsh -NoProfile -NonInteractive -File (do not dot-source).
# Default/DryRun only previews an existing registered plan and shared DB.
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
$legacy = @('ConfigPath', 'Tasks', 'CostThreshold') |
    Where-Object { $PSBoundParameters.ContainsKey($_) }
if ($legacy -or [string]::IsNullOrWhiteSpace($PlanPath) -or
    [string]::IsNullOrWhiteSpace($DbPath) -or ($DryRun -and $Action -ne 'preview') -or
    ($PSBoundParameters.ContainsKey('Node') -and (-not $Node -or
        @($Node | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count))) {
    [Console]::Out.WriteLine('{"status":"blocked","error":"WAVE_INPUT_REQUIRED","message":"Use an existing registered PlanPath and shared DbPath. Legacy Tasks/ConfigPath/CostThreshold are not supported. DryRun is preview only."}')
    exit 2
}
$helper = Join-Path $PSScriptRoot '../skills-src/multi-terminal-dispatcher/scripts/dispatch_wave.py'
$python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $python -or -not (Test-Path -LiteralPath $helper -PathType Leaf)) {
    [Console]::Out.WriteLine('{"status":"blocked","error":"WAVE_HELPER_UNAVAILABLE"}')
    exit 2
}
$waveArgs = @('-B', $helper, $Action, '--plan', $PlanPath, '--db', $DbPath)
if ($PSBoundParameters.ContainsKey('CertificatesPath')) {
    $waveArgs += @('--certificates', $CertificatesPath)
}
foreach ($nodeId in $Node) { $waveArgs += @('--node', $nodeId) }
try {
    & $python.Source @waveArgs
    exit $LASTEXITCODE
} catch {
    [Console]::Out.WriteLine('{"status":"blocked","error":"WAVE_HELPER_FAILED"}')
    exit 2
}
