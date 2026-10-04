# Package-local offline entry. Dot-source this file from its verified skill home.
# The root scripts/simonk.ps1 entry remains for existing pinned profiles.
# Both adapters share the central planner; tests permit only the relative-path
# difference below. Never add routing, billing or provider fallback here.

function global:simonK {
    [CmdletBinding(PositionalBinding = $false)]
    param(
        [string] $RequestPath,
        [string] $RuntimePath,
        [string] $RegistryPath,
        [string[]] $Root,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $TaskArgs
    )

    $failure = $null
    $message = $null
    if ($TaskArgs -or [string]::IsNullOrWhiteSpace($RequestPath) -or
        [string]::IsNullOrWhiteSpace($RuntimePath)) {
        $failure = 'SIMONK_PLAN_INPUT_REQUIRED'
        $message = 'Use /simonk <task> in an existing host, or simonK -RequestPath request.json -RuntimePath runtime.json. Planning never dispatches.'
    }

    # Bind only to the matched sibling vibe in this source/plugin/flat package.
    # Never fall back to a repo checkout, home copy or provider executable.
    $planner = Join-Path $PSScriptRoot '../../vibe/scripts/orchestrate.py'
    if (-not $failure -and -not (Test-Path -LiteralPath $planner -PathType Leaf)) {
        $failure = 'SIMONK_PLANNER_UNAVAILABLE'
        $message = 'The sibling /vibe planner is missing. Use a complete matching checkout.'
    }
    $python = $null
    if (-not $failure) {
        $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (-not $python) {
            $failure = 'SIMONK_PYTHON_UNAVAILABLE'
            $message = 'A trusted Python 3 application must be available on PATH.'
        }
    }
    if ($failure) {
        $global:LASTEXITCODE = 2
        [Console]::Error.WriteLine((@{status = 'blocked'; error = $failure; message = $message} |
            ConvertTo-Json -Compress))
        return
    }

    # Pass literal argv; the central planner owns all model, effort and cost policy.
    $plannerArgs = @('-B', $planner, 'plan', '--input', $RequestPath, '--runtime', $RuntimePath)
    if ($PSBoundParameters.ContainsKey('RegistryPath')) {
        $plannerArgs += @('--registry', $RegistryPath)
    }
    foreach ($skillRoot in $Root) { $plannerArgs += @('--root', $skillRoot) }
    try {
        & $python.Source @plannerArgs
        $global:LASTEXITCODE = $LASTEXITCODE
    } catch {
        $global:LASTEXITCODE = 2
        [Console]::Error.WriteLine('{"status":"blocked","error":"SIMONK_PLANNER_FAILED","message":"The offline planner could not run; no provider fallback was attempted."}')
    }
}
