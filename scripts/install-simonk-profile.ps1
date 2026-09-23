# Safe, opt-in profile migration for the offline simonK compatibility entry point.
# Preview is the default. Use PowerShell 7, -NoProfile and -File; do not dot-source.
[CmdletBinding(PositionalBinding = $false)]
param(
    [string] $RepoRoot,
    [string] $ProfilePath,
    [switch] $Apply
)
$ErrorActionPreference = 'Stop'
$stage = 'target'
$tempPath = $null
$ownsTemp = $false
$backupPath = $null

function Assert-PlainPath([string] $Path) {
    $cursor = [IO.Path]::GetFullPath($Path)
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_PATH' }
        }
        $parent = [IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}
function Hash-Bytes([byte[]] $Bytes) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($algorithm.ComputeHash($Bytes)).Replace('-', '') }
    finally { $algorithm.Dispose() }
}
function Profile-Block([string] $Target, [string] $Hash, [string] $Newline) {
    $literal = $Target.Replace("'", "''")
    return (@(
        '# simonk-profile-block:v2:begin'
        '# Managed by SimonK-stack; offline planner only. Review before reapplying.'
        '& {'
        '    $simonkPinnedStream = $null'
        '    try {'
        "        `$simonkPinnedStream = [IO.File]::Open('$literal', [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)"
        "        if ((Get-FileHash -LiteralPath '$literal' -Algorithm SHA256 -ErrorAction Stop).Hash -eq '$Hash') {"
        "            . '$literal'"
        '        } else {'
        "            Write-Warning 'SimonK profile target changed; review and rerun the installer.'"
        '        }'
        '    } catch {'
        "        Write-Warning 'SimonK profile target unavailable; review and rerun the installer.'"
        '    } finally {'
        '        if ($null -ne $simonkPinnedStream) { $simonkPinnedStream.Dispose() }'
        '    }'
        '}'
        '# simonk-profile-block:v2:end'
    ) -join $Newline)
}

try {
    if ($PSVersionTable.PSVersion.Major -lt 7 -or [string]::IsNullOrWhiteSpace($RepoRoot) -or
        -not [IO.Path]::IsPathFullyQualified($RepoRoot)) { throw 'EXPLICIT_PERSISTENT_REPO_REQUIRED' }
    $repo = [IO.Path]::GetFullPath($RepoRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
    Assert-PlainPath $repo
    if (-not (Test-Path -LiteralPath (Join-Path $repo '.git') -PathType Container)) {
        throw 'PRIMARY_CLONE_REQUIRED'
    }
    Assert-PlainPath (Join-Path $repo '.git')
    $git = Get-Command git -CommandType Application | Select-Object -First 1
    $top = & $git.Source -C $repo rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($top) -ne $repo) { throw 'REPO_ROOT_REQUIRED' }
    $sourceRoot = Split-Path -Parent $PSScriptRoot
    # This proves selected entry/planner parity, not whole-package integrity.
    foreach ($relative in @('scripts/simonk.ps1', 'skills-src/vibe/scripts/orchestrate.py',
                           'skills-src/vibe/scripts/model_registry.py', 'skills-src/vibe/scripts/routing.py',
                           'skills-src/vibe/references/model-registry.json')) {
        $target = Join-Path $repo $relative
        $source = Join-Path $sourceRoot $relative
        Assert-PlainPath $target
        if (-not (Test-Path -LiteralPath $target -PathType Leaf) -or
            -not (Test-Path -LiteralPath $source -PathType Leaf) -or
            (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne
            (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash) { throw 'TARGET_REVISION_MISMATCH' }
        $tracked = & $git.Source -C $repo ls-files --error-unmatch -- $relative 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'TRACKED_ENTRY_REQUIRED' }
        & $git.Source -C $repo diff --quiet HEAD -- $relative
        if ($LASTEXITCODE -ne 0) { throw 'CLEAN_ENTRY_REQUIRED' }
    }
    $simonkPath = Join-Path $repo 'scripts/simonk.ps1'
    $wrapperHash = (Get-FileHash -LiteralPath $simonkPath -Algorithm SHA256).Hash

    $stage = 'profile'
    if (-not $PSBoundParameters.ContainsKey('ProfilePath')) { $ProfilePath = $PROFILE.CurrentUserAllHosts }
    if ([string]::IsNullOrWhiteSpace($ProfilePath) -or -not [IO.Path]::IsPathFullyQualified($ProfilePath) -or
        [IO.Path]::GetExtension($ProfilePath) -ne '.ps1') { throw 'EXACT_PROFILE_REQUIRED' }
    $profileFile = [IO.Path]::GetFullPath($ProfilePath)
    Assert-PlainPath $profileFile
    $existed = Test-Path -LiteralPath $profileFile
    if ($existed -and -not (Test-Path -LiteralPath $profileFile -PathType Leaf)) { throw 'PROFILE_NOT_FILE' }
    [byte[]] $original = @()
    if ($existed) { $original = [IO.File]::ReadAllBytes($profileFile) }
    if ($original.Length -gt 2MB) { throw 'PROFILE_TOO_LARGE' }
    $encoding = [Text.UTF8Encoding]::new($false, $true)
    $offset = 0
    if ($original.Length -ge 4 -and
        (($original[0] -eq 255 -and $original[1] -eq 254 -and $original[2] -eq 0 -and $original[3] -eq 0) -or
         ($original[0] -eq 0 -and $original[1] -eq 0 -and $original[2] -eq 254 -and $original[3] -eq 255))) {
        throw 'UNSUPPORTED_ENCODING'
    }
    if ($original.Length -ge 3 -and $original[0] -eq 239 -and $original[1] -eq 187 -and $original[2] -eq 191) {
        $encoding = [Text.UTF8Encoding]::new($true, $true); $offset = 3
    } elseif ($original.Length -ge 2 -and $original[0] -eq 255 -and $original[1] -eq 254) {
        $encoding = [Text.UnicodeEncoding]::new($false, $true, $true); $offset = 2
    } elseif ($original.Length -ge 2 -and $original[0] -eq 254 -and $original[1] -eq 255) {
        $encoding = [Text.UnicodeEncoding]::new($true, $true, $true); $offset = 2
    }
    $existing = $encoding.GetString($original, $offset, $original.Length - $offset)
    if ($existing.Contains([char]0)) { throw 'UNSUPPORTED_ENCODING' }
    [byte[]] $roundtrip = $encoding.GetPreamble() + $encoding.GetBytes($existing)
    if ((Hash-Bytes $roundtrip) -ne (Hash-Bytes $original)) { throw 'ENCODING_NOT_ROUNDTRIPPABLE' }
    $newlineMatch = [regex]::Match($existing, "\r\n|\n")
    $newline = if ($newlineMatch.Success) { $newlineMatch.Value } else { [Environment]::NewLine }
    $block = Profile-Block $simonkPath $wrapperHash $newline
    $markerCount = [regex]::Matches($existing, 'simonk-profile-block:').Count
    $owned = $null
    if ($markerCount -eq 1) {
        $v1 = "(?m)^# <!-- simonk-profile-block:v1 -->\r?\n" +
              "# Added by SimonK-stack/scripts/install-simonk-profile\.ps1\r?\n" +
              "if \(Test-Path '(?<old>[^'\r\n]+)'\) \{\r?\n    \. '\k<old>'\r?\n\}(?=\r?$)"
        $ownedMatches = [regex]::Matches($existing, $v1)
        if ($ownedMatches.Count -ne 1) { throw 'AMBIGUOUS_V1_BLOCK' }
        $owned = $ownedMatches[0]
    } elseif ($markerCount -eq 2) {
        $ownedMatches = [regex]::Matches($existing,
            '(?ms)^# simonk-profile-block:v2:begin\r?\n.*?^# simonk-profile-block:v2:end(?=\r?$)')
        if ($ownedMatches.Count -ne 1) { throw 'AMBIGUOUS_V2_BLOCK' }
        $owned = $ownedMatches[0]
        $paths = [regex]::Matches($owned.Value, "(?m)^            \. '(?<p>(?:[^'\r\n]|'')*)'\r?$")
        $hashes = [regex]::Matches($owned.Value, "\.Hash -eq '(?<h>[0-9A-F]{64})'")
        if ($paths.Count -ne 1 -or $hashes.Count -ne 1) { throw 'MODIFIED_V2_BLOCK' }
        $lf = [string][char]10
        $expected = Profile-Block ($paths[0].Groups['p'].Value.Replace("''", "'")) $hashes[0].Groups['h'].Value $lf
        if ($owned.Value.Replace(([string][char]13 + $lf), $lf) -cne $expected) { throw 'MODIFIED_V2_BLOCK' }
    } elseif ($markerCount -ne 0) { throw 'AMBIGUOUS_MARKERS' }
    if ($owned) {
        # Text that resembles our block inside a here-string, comment or nested
        # function is user data, not installer-owned startup code.
        $oldTokens = $null; $oldErrors = $null
        $oldAst = [Management.Automation.Language.Parser]::ParseInput($existing, [ref]$oldTokens, [ref]$oldErrors)
        $codeStart = $owned.Value.IndexOf($(if ($markerCount -eq 1) { 'if (' } else { '& {' }))
        $codeEnd = $owned.Value.LastIndexOf('}') + 1
        $headerComments = @($oldTokens | Where-Object {
            $_.Kind -eq 'Comment' -and $_.Extent.StartOffset -eq $owned.Index -and
            $_.Text -ceq $owned.Value.Split([char]10)[0].TrimEnd([char]13)
        })
        $statements = @($oldAst.EndBlock.Statements | Where-Object {
            $_.Extent.StartOffset -eq ($owned.Index + $codeStart) -and
            $_.Extent.EndOffset -eq ($owned.Index + $codeEnd)
        })
        if ($oldErrors.Count -or $headerComments.Count -ne 1 -or $statements.Count -ne 1) {
            throw 'BLOCK_NOT_TOP_LEVEL_CODE'
        }
    }
    $unowned = if ($owned) { $existing.Remove($owned.Index, $owned.Length) } else { $existing }
    if ($unowned -match '(?i)simonk\.ps1') { throw 'UNMANAGED_SIMONK_REFERENCE' }
    if ($owned) {
        $updated = $existing.Substring(0, $owned.Index) + $block + $existing.Substring($owned.Index + $owned.Length)
    } else {
        $separator = if ($existing -and -not $existing.EndsWith([string][char]10)) { $newline } else { '' }
        $updated = $existing + $separator + $block + $newline
    }
    $tokens = $null; $parseErrors = $null
    $null = [Management.Automation.Language.Parser]::ParseInput($updated, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count) { throw 'PROFILE_SYNTAX_INVALID' }
    [byte[]] $replacement = $encoding.GetPreamble() + $encoding.GetBytes($updated)
    $beforeHash = Hash-Bytes $original
    $afterHash = Hash-Bytes $replacement
    $changed = $beforeHash -ne $afterHash
    $result = [ordered]@{status = 'preview'; changed = $changed; repo_root = $repo;
        profile_path = $profileFile; wrapper_sha256 = $wrapperHash;
        before_sha256 = $beforeHash; after_sha256 = $afterHash; backup_path = $null}
    if ($Apply -and $changed) {
        $stage = 'write'
        $directory = [IO.Path]::GetDirectoryName($profileFile)
        $null = [IO.Directory]::CreateDirectory($directory)
        Assert-PlainPath $profileFile
        $tempPath = Join-Path $directory ('.simonk-profile-' + [Guid]::NewGuid().ToString('N') + '.tmp')
        $stream = [IO.File]::Open($tempPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $ownsTemp = $true
        try { $stream.Write($replacement, 0, $replacement.Length); $stream.Flush($true) } finally { $stream.Dispose() }
        # Optimistic freshness check, not a universal cross-editor lock.
        if ((Test-Path -LiteralPath $profileFile) -ne $existed -or
            ($existed -and (Hash-Bytes ([IO.File]::ReadAllBytes($profileFile))) -ne $beforeHash)) {
            throw 'PROFILE_CHANGED_DURING_PREVIEW'
        }
        if ($existed) {
            $backupPath = $profileFile + '.simonk-backup-' + [Guid]::NewGuid().ToString('N')
            [IO.File]::Replace($tempPath, $profileFile, $backupPath)
        } else {
            [IO.File]::Move($tempPath, $profileFile)
        }
        $tempPath = $null
        $result.status = 'installed'
        $result.backup_path = $backupPath
    } elseif ($Apply) { $result.status = 'unchanged' }
    [Console]::Out.WriteLine(($result | ConvertTo-Json -Compress))
    exit 0
} catch {
    # Never echo profile contents, provider output, environment values or raw exceptions.
    [Console]::Out.WriteLine((@{status='blocked'; error='PROFILE_INSTALL_BLOCKED'; stage=$stage} | ConvertTo-Json -Compress))
    exit 2
} finally {
    if ($ownsTemp -and $tempPath -and (Test-Path -LiteralPath $tempPath -PathType Leaf)) {
        # Only the unique file this invocation created; never a profile or backup.
        Remove-Item -LiteralPath $tempPath -Force
    }
}
