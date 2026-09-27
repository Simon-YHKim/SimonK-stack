# Tool-restricted Claude host preview for a verified five-plugin /vibe candidate.
# Default CheckOnly makes no model call. -Run consumes included subscription usage.
[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory = $true)] [string] $CandidateRoot,
    [Parameter(Mandatory = $true)] [string] $ExpectedDigest,
    [switch] $Run,
    [switch] $AllPlugins,
    [switch] $SubscriptionOnlyConfirmed
)

$ErrorActionPreference = 'Stop'
$reason = 'PREVIEW_BLOCKED'

try {
    if ($ExpectedDigest -cnotmatch '^[0-9a-fA-F]{64}$') {
        $reason = 'DIGEST_INVALID'; throw 'blocked'
    }
    $digest = $ExpectedDigest.ToLowerInvariant()
    if ($Run -and -not $SubscriptionOnlyConfirmed) {
        $reason = 'SUBSCRIPTION_CONFIRMATION_REQUIRED'; throw 'blocked'
    }
    if (-not [IO.Path]::IsPathFullyQualified($CandidateRoot)) {
        $reason = 'CANDIDATE_PATH_INVALID'; throw 'blocked'
    }
    $candidate = [IO.Path]::GetFullPath($CandidateRoot)
    if (-not (Test-Path -LiteralPath $candidate -PathType Container)) {
        $reason = 'CANDIDATE_MISSING'; throw 'blocked'
    }
    $verifier = Join-Path $PSScriptRoot 'plugin_bundle.py'
    if (-not (Test-Path -LiteralPath $verifier -PathType Leaf)) {
        $reason = 'VERIFIER_MISSING'; throw 'blocked'
    }
    $python = Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $reason = 'CANDIDATE_VERIFY_FAILED'
    $receiptText = & $python.Source -B $verifier verify --package $candidate --expected-digest $digest 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'blocked' }
    $receipt = $receiptText | ConvertFrom-Json
    if ($receipt.bundle_digest -cne $digest -or $receipt.plugins -ne 5 -or
        $receipt.skills -lt 1 -or $receipt.status -cne 'candidate_bytes_verified') {
        throw 'blocked'
    }
    $core = Join-Path $candidate 'plugins\SimonKCore'
    if (-not (Test-Path -LiteralPath (Join-Path $core '.claude-plugin\plugin.json') -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $core 'skills\vibe\SKILL.md') -PathType Leaf)) {
        $reason = 'CORE_PLUGIN_MISSING'; throw 'blocked'
    }
    $pluginNames = if ($AllPlugins) {
        @('SimonKCore', 'SimonKDesign', 'SimonKStack', 'SimonKMarket', 'SimonKAIHub')
    } else {
        @('SimonKCore')
    }
    $pluginArgs = @()
    foreach ($name in $pluginNames) {
        $pluginPath = Join-Path $candidate "plugins\$name"
        if (-not (Test-Path -LiteralPath (Join-Path $pluginPath '.claude-plugin\plugin.json') -PathType Leaf)) {
            $reason = 'PLUGIN_MISSING'; throw 'blocked'
        }
        $pluginArgs += '--plugin-dir', $pluginPath
    }

    if (-not $Run) {
        [Console]::Out.WriteLine((@{status='candidate_verified'; bundle_digest=$digest;
            plugins=$receipt.plugins; skills=$receipt.skills; model_called=$false;
            preview_plugins=$pluginNames.Count; installation_ready=$false} | ConvertTo-Json -Compress))
        exit 0
    }

    foreach ($key in @('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL',
            'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY',
            'CLAUDE_CODE_OAUTH_TOKEN')) {
        if ([Environment]::GetEnvironmentVariable($key, 'Process')) {
            $reason = 'NON_SUBSCRIPTION_CREDENTIAL_PRESENT'; throw 'blocked'
        }
    }
    $claude = Get-Command claude -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $reason = 'SUBSCRIPTION_LOGIN_UNVERIFIED'
    $auth = (& $claude.Source auth status --json 2>$null) | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or -not $auth.loggedIn -or $auth.authMethod -cne 'claude.ai' -or
        $auth.apiProvider -cne 'firstParty' -or $auth.subscriptionType -cne 'max') {
        throw 'blocked'
    }

    $oldMcp = [Environment]::GetEnvironmentVariable('ENABLE_CLAUDEAI_MCP_SERVERS', 'Process')
    try {
        # Session-local only: avoid unrelated claude.ai connector schemas during routing evaluation.
        $env:ENABLE_CLAUDEAI_MCP_SERVERS = 'false'
        [Console]::Out.WriteLine('Tool-restricted candidate preview; included subscription usage is consumed.')
        [Console]::Out.WriteLine('Only Skill is available to the model; plugin hooks and host startup are not an OS sandbox.')
        [Console]::Out.WriteLine('This launcher cannot verify the account overage toggle; it relies on the explicit confirmation for this run.')
        & $claude.Source --setting-sources '' --strict-mcp-config @pluginArgs `
            --model claude-sonnet-5 --effort low --permission-mode dontAsk `
            --allowedTools Skill --tools Skill --disallowedTools 'mcp__*' `
            --permission-prompts none
        $sessionExit = $LASTEXITCODE
    } finally {
        if ($null -eq $oldMcp) {
            Remove-Item Env:ENABLE_CLAUDEAI_MCP_SERVERS -ErrorAction SilentlyContinue
        } else {
            $env:ENABLE_CLAUDEAI_MCP_SERVERS = $oldMcp
        }
    }
    if ($sessionExit -ne 0) { $reason = 'CLAUDE_SESSION_FAILED'; throw 'blocked' }
    $reason = 'CANDIDATE_CHANGED_AFTER_SESSION'
    $after = & $python.Source -B $verifier verify --package $candidate --expected-digest $digest 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $after) { throw 'blocked' }
    [Console]::Out.WriteLine('Candidate digest remains valid. Host behavior and installation readiness are not certified.')
    exit 0
} catch {
    [Console]::Error.WriteLine($reason)
    exit 2
}
