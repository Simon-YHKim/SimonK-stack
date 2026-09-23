# simonK is an offline compatibility entry point, not an LLM launcher.
# Dot-source this file, then:
#   $ErrorActionPreference = 'Stop'  # In batch scripts: catch binding errors too.
#   simonK -RequestPath request.json -RuntimePath runtime.json
#   exit $LASTEXITCODE   # In batch scripts only; never exit an interactive host.
# Text/no-argument invocations now fail closed. Use /simonk in an existing host.
# No profile, cloud bootstrap, credentials, provider, run state or budget writes.

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

    # Bind to this checkout, even when dot-sourced from a profile or called
    # from another directory. Never silently fall back to an installed skill.
    $planner = Join-Path $PSScriptRoot '../skills-src/vibe/scripts/orchestrate.py'
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

    # Native argv, never a shell-built command. Keep the central request and
    # its run ID, ancestry, DAG, registry, policy and runtime evidence unchanged.
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
