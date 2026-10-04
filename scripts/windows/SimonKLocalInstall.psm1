# Shared steps for the Windows user-home install of SimonK-stack (PowerShell 7).
# Ported from the D-59..D-71 session wrappers (build_candidate, install_junctions,
# install_physical). Every function is read-only unless it receives -Apply.
# No user path is hardcoded: locations come from parameters or are discovered
# from the current install. Old links and folders are moved to
# <home>\.claude\flat-link-archive and never deleted.

Set-StrictMode -Version 1.0
$ErrorActionPreference = 'Stop'

$script:ClaudeCore = 'candidate-safety\plugins\SimonKCore\skills'
$script:ClaudeStack = 'candidate-safety\plugins\SimonKStack\skills'
$script:CodexCore = 'codex-subset-safety\plugins\SimonKCore\skills'
$script:VibeSuffix = '\candidate-safety\plugins\SimonKCore\skills\vibe'
$script:DefaultReleasesDir = 'E:\Coding Infra\Releases\SimonK-stack'
# Everything the four package builders read from the repository. A change
# outside these paths cannot change the candidate bytes.
$script:CandidateInputs = @('skills-src', '.claude/skills', 'distribution', 'LICENSE', 'NOTICE',
    'scripts/skill_release.py', 'scripts/plugin_bundle.py', 'scripts/dist_release.py',
    'scripts/codex_overlay.py', 'scripts/codex_safe_subset.py')
$script:ActiveAttemptStates = @('intent', 'running', 'uncertain')
$script:CodexLinePattern = '(?m)^path = "(?<p>[^"\r\n]*/candidate-safety/plugins/SimonKCore/skills/vibe/SKILL\.md)"[ \t]*\r?$'
$script:GitExe = $null
$script:PythonExe = $null

# ---------------------------------------------------------------- basics

function Assert-SkPowerShell7 {
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'POWERSHELL_7_REQUIRED: run with pwsh -NoProfile -File' }
}

function Get-SkKstNow {
    $zone = $null
    foreach ($id in @('Korea Standard Time', 'Asia/Seoul')) {
        try { $zone = [TimeZoneInfo]::FindSystemTimeZoneById($id); break } catch { $zone = $null }
    }
    if (-not $zone) { return [DateTime]::UtcNow.AddHours(9) }
    [TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, $zone)
}

function Get-SkErrorCode([string] $Message) {
    if ($Message -match '^([A-Z][A-Z0-9_]+):') { return $Matches[1] }
    'UNEXPECTED'
}

function Write-SkJson($Value) {
    [Console]::Out.WriteLine(($Value | ConvertTo-Json -Depth 12))
}

function Enter-SkInstallLock {
    # One install at a time per Windows session; released automatically if the process dies.
    $mutex = [Threading.Mutex]::new($false, 'Local\SimonK-stack-update-local')
    $acquired = $false
    try { $acquired = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $acquired = $true }
    if (-not $acquired) {
        $mutex.Dispose()
        throw 'INSTALL_BUSY: another SimonK install run holds the lock'
    }
    $mutex
}

function Exit-SkInstallLock($Mutex) {
    if ($Mutex) {
        try { $Mutex.ReleaseMutex() } catch { $null = $_ }
        $Mutex.Dispose()
    }
}

function Test-SkLexists([string] $Path) {
    # True for a broken junction too (Test-Path follows the link).
    try { $null = [IO.File]::GetAttributes($Path); return $true } catch { return $false }
}

function Get-SkFreePath([string] $Path) {
    $candidate = $Path
    $n = 2
    while (Test-SkLexists $candidate) { $candidate = "$Path-$n"; $n++ }
    $candidate
}

function Resolve-SkExecutable([string] $Name) {
    $command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { throw "TOOL_MISSING: $Name is not on PATH" }
    $command.Source
}

function Invoke-SkNative {
    param([Parameter(Mandatory)] [string] $FilePath, [string[]] $ArgumentList = @(),
          [string] $WorkingDirectory, [switch] $AllowFailure)
    $ErrorActionPreference = 'Continue'
    $pushed = $false
    if ($WorkingDirectory) { Push-Location -LiteralPath $WorkingDirectory; $pushed = $true }
    try {
        $raw = @(& $FilePath @ArgumentList 2>&1)
        $code = $LASTEXITCODE
    } finally {
        if ($pushed) { Pop-Location }
    }
    $stdout = @($raw | Where-Object { $_ -isnot [Management.Automation.ErrorRecord] } | ForEach-Object { [string] $_ })
    $stderr = @($raw | Where-Object { $_ -is [Management.Automation.ErrorRecord] } | ForEach-Object { $_.ToString() })
    if ($code -ne 0 -and -not $AllowFailure) {
        $what = [IO.Path]::GetFileName($FilePath) + ' ' + (($ArgumentList | Select-Object -First 4) -join ' ')
        $tail = ($stderr | Select-Object -Last 3) -join ' | '
        throw "NATIVE_FAILED: $what (rc=$code) $tail"
    }
    [pscustomobject]@{ ExitCode = $code; Out = $stdout; Err = $stderr }
}

function Invoke-SkGit {
    param([Parameter(Mandatory)] [string] $Repo, [string[]] $ArgumentList = @(), [switch] $AllowFailure)
    if (-not $script:GitExe) { $script:GitExe = Resolve-SkExecutable 'git' }
    Invoke-SkNative -FilePath $script:GitExe -ArgumentList (@('-C', $Repo) + $ArgumentList) -AllowFailure:$AllowFailure
}

function Invoke-SkPython {
    param([string[]] $ArgumentList = @(), [string] $WorkingDirectory, [switch] $AllowFailure)
    if (-not $script:PythonExe) { $script:PythonExe = Resolve-SkExecutable 'python' }
    $env:PYTHONDONTWRITEBYTECODE = '1'
    Invoke-SkNative -FilePath $script:PythonExe -ArgumentList (@('-B') + $ArgumentList) `
        -WorkingDirectory $WorkingDirectory -AllowFailure:$AllowFailure
}

function ConvertFrom-SkJsonOutput([string[]] $Lines) {
    ($Lines -join "`n") | ConvertFrom-Json
}

# ---------------------------------------------------------------- hashing

function Get-SkTreeDigest([string] $Path) {
    # Same algorithm as the D-59..D-71 installer: sorted "relative:sha256" rows.
    $base = [IO.Path]::GetFullPath($Path).TrimEnd('\') + '\'
    $rows = @(Get-ChildItem -LiteralPath $Path -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
        $_.FullName.Substring($base.Length) + ':' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash })
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($rows -join "`n"))))).Replace('-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
}

function Get-SkGitBlobId([string] $Path) {
    # Git blob id of the raw bytes (no filters), so CRLF/LF drift counts as a difference.
    $bytes = [IO.File]::ReadAllBytes($Path)
    $header = [Text.Encoding]::ASCII.GetBytes("blob $($bytes.Length)`0")
    $sha = [Security.Cryptography.SHA1]::Create()
    try {
        $null = $sha.TransformBlock($header, 0, $header.Length, $null, 0)
        $null = $sha.TransformFinalBlock($bytes, 0, $bytes.Length)
        ([BitConverter]::ToString($sha.Hash)).Replace('-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
}

function Save-SkGitBlobs([string] $Repo, $Items) {
    # Stream blob bytes straight to disk through one `git cat-file --batch`; PowerShell
    # text pipelines would re-encode them. $Items: objects with Blob and Path.
    if (-not $script:GitExe) { $script:GitExe = Resolve-SkExecutable 'git' }
    $info = [Diagnostics.ProcessStartInfo]::new($script:GitExe)
    foreach ($a in @('-C', $Repo, 'cat-file', '--batch')) { $info.ArgumentList.Add($a) }
    $info.UseShellExecute = $false
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.CreateNoWindow = $true
    $process = [Diagnostics.Process]::Start($info)
    try {
        $errTask = $process.StandardError.ReadToEndAsync()
        $stdin = $process.StandardInput.BaseStream
        $stdout = $process.StandardOutput.BaseStream
        $buffer = [byte[]]::new(65536)
        foreach ($item in $Items) {
            $request = [Text.Encoding]::ASCII.GetBytes("$($item.Blob)`n")
            $stdin.Write($request, 0, $request.Length)
            $stdin.Flush()
            $header = [Collections.Generic.List[byte]]::new()
            while ($true) {
                $b = $stdout.ReadByte()
                if ($b -lt 0) { throw "NATIVE_FAILED: git cat-file --batch ended early at $($item.Blob)" }
                if ($b -eq 10) { break }
                $header.Add([byte] $b)
            }
            $parts = [Text.Encoding]::ASCII.GetString($header.ToArray()).Split(' ')
            if ($parts.Count -ne 3 -or $parts[0] -ne $item.Blob -or $parts[1] -ne 'blob') {
                throw "NATIVE_FAILED: git cat-file --batch returned '$($parts -join ' ')' for $($item.Blob)"
            }
            $left = [long] $parts[2]
            $file = [IO.File]::Open($item.Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            try {
                while ($left -gt 0) {
                    $n = $stdout.Read($buffer, 0, [int] [Math]::Min([long] $buffer.Length, $left))
                    if ($n -le 0) { throw "NATIVE_FAILED: short read for $($item.Blob)" }
                    $file.Write($buffer, 0, $n)
                    $left -= $n
                }
            } finally { $file.Dispose() }
            if ($stdout.ReadByte() -ne 10) { throw "NATIVE_FAILED: git cat-file --batch framing after $($item.Blob)" }
        }
        $stdin.Close()
        $process.WaitForExit()
        $null = $errTask.Result
        if ($process.ExitCode -ne 0) { throw "NATIVE_FAILED: git cat-file --batch (rc=$($process.ExitCode))" }
    } finally {
        if (-not $process.HasExited) { try { $process.Kill() } catch { $null = $_ } }
        $process.Dispose()
    }
}

# ---------------------------------------------------------------- repository

function Resolve-SkRepoRoot([string] $RepoRoot) {
    if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
    $top = (Invoke-SkGit $RepoRoot @('rev-parse', '--show-toplevel')).Out | Select-Object -First 1
    [IO.Path]::GetFullPath($top)
}

function Resolve-SkCommit([string] $Repo, [string] $Ref) {
    $r = Invoke-SkGit $Repo @('rev-parse', '--verify', '--quiet', "$Ref^{commit}") -AllowFailure
    $sha = $r.Out | Select-Object -First 1
    if ($r.ExitCode -ne 0 -or $sha -notmatch '^[0-9a-f]{40}$') { throw "REF_UNKNOWN: $Ref" }
    $sha
}

function Test-SkCommitKnown([string] $Repo, [string] $Commit) {
    if ($Commit -notmatch '^[0-9a-f]{40}$') { return $false }
    (Invoke-SkGit $Repo @('cat-file', '-e', "$Commit^{commit}") -AllowFailure).ExitCode -eq 0
}

function Get-SkCandidateInputChanges([string] $Repo, [string] $From, [string] $To) {
    # $null when the installed commit is unknown here; otherwise the changed input paths.
    if (-not (Test-SkCommitKnown $Repo $From)) { return $null }
    $r = Invoke-SkGit $Repo (@('-c', 'core.quotepath=on', 'diff', '--name-only', $From, $To, '--') + $script:CandidateInputs)
    , @($r.Out | Where-Object { $_ })
}

$script:TreeCache = @{}
$script:VersionCache = @{}

function Get-SkSkillsSrcIndex([string] $Repo, [string] $Commit) {
    # One `git ls-tree` per commit (process start is slow on Windows); commits are immutable.
    $key = "$Repo|$Commit"
    if ($script:TreeCache.ContainsKey($key)) { return $script:TreeCache[$key] }
    $index = @{}
    $r = Invoke-SkGit $Repo @('-c', 'core.quotepath=on', 'ls-tree', '-r', $Commit, '--', 'skills-src/')
    foreach ($line in $r.Out) {
        if (-not $line) { continue }
        $tab = $line.IndexOf("`t")
        $meta = $line.Substring(0, $tab).Split(' ')
        $path = $line.Substring($tab + 1)
        $m = [regex]::Match($path, '^"?skills-src/([^/]+)/(.+)$')
        if (-not $m.Success) { continue }
        $name = $m.Groups[1].Value
        if (-not $index.ContainsKey($name)) { $index[$name] = [ordered]@{} }
        $ok = (-not $path.StartsWith('"')) -and $meta[1] -eq 'blob' -and $meta[0] -in @('100644', '100755')
        # $null marks an entry this installer cannot copy byte-exactly (quoted path, link, submodule).
        $index[$name][$m.Groups[2].Value] = $(if ($ok) { $meta[2] } else { $null })
    }
    $script:TreeCache[$key] = $index
    $index
}

function Get-SkSkillFiles([string] $Repo, [string] $Commit, [string] $Name) {
    $index = Get-SkSkillsSrcIndex $Repo $Commit
    $files = [ordered]@{}
    if (-not $index.ContainsKey($Name)) { return $files }
    foreach ($rel in $index[$Name].Keys) {
        if (-not $index[$Name][$rel]) { throw "UNSUPPORTED_TREE_ENTRY: skills-src/$Name/$rel" }
        $files[$rel] = $index[$Name][$rel]
    }
    $files
}

function Get-SkVersionFromText([string] $Text) {
    $m = [regex]::Match($Text, '(?m)^version:[ \t]*["'']?(?<v>[^"''\r\n]+?)["'']?[ \t]*\r?$')
    if ($m.Success) { return $m.Groups['v'].Value }
    $null
}

function Get-SkGitSkillVersion([string] $Repo, [string] $Commit, [string] $Name) {
    # One `git grep` per commit for every skills-src/<n>/SKILL.md; the first match is the frontmatter.
    $key = "$Repo|$Commit"
    if (-not $script:VersionCache.ContainsKey($key)) {
        $map = @{}
        $r = Invoke-SkGit $Repo @('-c', 'core.quotepath=on', 'grep', '-n', '-I', '-e', '^version:', $Commit, '--',
            'skills-src/*/SKILL.md') -AllowFailure
        if ($r.ExitCode -gt 1) { throw "NATIVE_FAILED: git grep versions at $Commit (rc=$($r.ExitCode))" }
        foreach ($line in $r.Out) {
            $m = [regex]::Match($line, '^[0-9a-f]+:skills-src/([^/]+)/SKILL\.md:(\d+):(.*)$')
            if (-not $m.Success) { continue }
            # Not $name: PowerShell variables ignore case, so it would overwrite the $Name parameter.
            $grepSkill = $m.Groups[1].Value
            $number = [int] $m.Groups[2].Value
            if (-not $map.ContainsKey($grepSkill) -or $map[$grepSkill].Line -gt $number) {
                $map[$grepSkill] = @{ Line = $number; Version = (Get-SkVersionFromText $m.Groups[3].Value) }
            }
        }
        $script:VersionCache[$key] = $map
    }
    $map = $script:VersionCache[$key]
    if ($map.ContainsKey($Name)) { return $map[$Name].Version }
    $null
}

function Get-SkFileSkillVersion([string] $SkillDir) {
    $file = Join-Path $SkillDir 'SKILL.md'
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { return $null }
    Get-SkVersionFromText ([IO.File]::ReadAllText($file))
}

function Compare-SkSkillTree([string] $Repo, [string] $Commit, [string] $Name, [string] $Path) {
    # Installed bytes against skills-src/<Name> blobs at $Commit. Generated __pycache__ is ignored.
    $want = Get-SkSkillFiles $Repo $Commit $Name
    $result = [ordered]@{ skill = $Name; path = $Path; state = ''; main_files = $want.Count
        changed = @(); missing = @(); extra = @(); ignored_generated = 0 }
    if ($want.Count -eq 0) { $result.state = 'not-in-main'; return $result }
    if ($want.Contains('.simonk-no-install')) { $result.state = 'no-install'; return $result }
    if (-not (Test-SkLexists $Path)) { $result.state = 'missing'; return $result }
    $base = [IO.Path]::GetFullPath($Path).TrimEnd('\') + '\'
    $have = @{}
    foreach ($f in Get-ChildItem -LiteralPath $Path -Recurse -File -Force) {
        $rel = $f.FullName.Substring($base.Length).Replace('\', '/')
        if ($rel -match '(^|/)__pycache__/[^/]+\.pyc$') { $result.ignored_generated++; continue }
        $have[$rel] = $f.FullName
    }
    $changed = [Collections.Generic.List[string]]::new()
    $missing = [Collections.Generic.List[string]]::new()
    foreach ($rel in $want.Keys) {
        if (-not $have.ContainsKey($rel)) { $missing.Add($rel) }
        elseif ((Get-SkGitBlobId $have[$rel]) -ne $want[$rel]) { $changed.Add($rel) }
    }
    $result.changed = @($changed)
    $result.missing = @($missing)
    $result.extra = @($have.Keys | Where-Object { -not $want.Contains($_) } | Sort-Object)
    $result.state = if ($changed.Count -or $missing.Count -or $result.extra.Count) { 'differs' } else { 'same' }
    $result
}

# ---------------------------------------------------------------- user home

function Resolve-SkUserHome([string] $UserHome) {
    if (-not $UserHome) { $UserHome = [Environment]::GetFolderPath('UserProfile') }
    if (-not (Test-Path -LiteralPath $UserHome -PathType Container)) { throw "USER_HOME_MISSING: $UserHome" }
    [IO.Path]::GetFullPath($UserHome).TrimEnd('\')
}

function Get-SkJunctionSpecs([string] $UserHome, [string] $CodexHome) {
    # The eight links the /vibe user-home install owns.
    $claude = Join-Path $UserHome '.claude\skills'
    $codex = Join-Path $CodexHome 'skills'
    foreach ($skill in @('vibe', 'vibe-bot', 'model-router', 'simonk', 'multi-terminal-dispatcher')) {
        [ordered]@{ Name = "claude-$skill"; Skill = $skill; Side = 'claude'
            Path = Join-Path $claude $skill; Relative = "$script:ClaudeCore\$skill" }
    }
    [ordered]@{ Name = 'claude-qa'; Skill = 'qa'; Side = 'claude'
        Path = Join-Path $claude 'qa'; Relative = "$script:ClaudeStack\qa" }
    foreach ($skill in @('vibe', 'vibe-bot')) {
        [ordered]@{ Name = "codex-$skill"; Skill = $skill; Side = 'codex'
            Path = Join-Path $codex $skill; Relative = "$script:CodexCore\$skill" }
    }
}

function Get-SkInstalledCandidate([string] $UserHome) {
    $path = Join-Path $UserHome '.claude\skills\vibe'
    $result = [ordered]@{ state = 'absent'; path = $path; target = $null; tag = $null; candidate = $null
        releases_dir = $null; receipts_file = $null; main = $null }
    $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    if (-not $item) { return $result }
    if (-not $item.LinkType) { $result.state = 'directory'; return $result }
    $target = [string] ($item.Target -join '')
    $result.target = $target
    if ($item.LinkType -ne 'Junction') { $result.state = 'other-link'; return $result }
    if (-not $target.EndsWith($script:VibeSuffix, [StringComparison]::OrdinalIgnoreCase)) {
        $result.state = 'unexpected-target'; return $result
    }
    $root = $target.Substring(0, $target.Length - $script:VibeSuffix.Length)
    $leaf = Split-Path -Leaf $root
    if (-not $leaf.EndsWith('-candidate')) { $result.state = 'unexpected-target'; return $result }
    $result.state = 'junction'
    $result.candidate = $root
    $result.tag = $leaf.Substring(0, $leaf.Length - '-candidate'.Length)
    $result.releases_dir = Split-Path -Parent $root
    $receiptsFile = Join-Path $result.releases_dir "$($result.tag)-receipts.json"
    if (Test-Path -LiteralPath $receiptsFile -PathType Leaf) {
        $result.receipts_file = $receiptsFile
        $result.main = [string] (Get-Content -LiteralPath $receiptsFile -Raw | ConvertFrom-Json).main
    }
    $result
}

function Resolve-SkReleasesDir([string] $Explicit, $Installed) {
    if ($Explicit) {
        if (-not (Test-Path -LiteralPath $Explicit -PathType Container)) { throw "RELEASES_DIR_MISSING: $Explicit" }
        return [IO.Path]::GetFullPath($Explicit).TrimEnd('\')
    }
    if ($Installed -and $Installed.releases_dir -and (Test-Path -LiteralPath $Installed.releases_dir -PathType Container)) {
        return $Installed.releases_dir
    }
    if (Test-Path -LiteralPath $script:DefaultReleasesDir -PathType Container) { return $script:DefaultReleasesDir }
    throw 'RELEASES_DIR_REQUIRED: pass -ReleasesDir <folder that holds the candidates>'
}

function Read-SkReceipts([string] $ReleasesDir, [string] $Tag) {
    $file = Join-Path $ReleasesDir "$Tag-receipts.json"
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { return $null }
    Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
}

function Find-SkCandidateForCommit([string] $ReleasesDir, [string] $Commit) {
    # A finished build writes its receipts last, so receipts + folder = a complete candidate.
    foreach ($file in Get-ChildItem -LiteralPath $ReleasesDir -Filter '*-receipts.json' -File | Sort-Object LastWriteTimeUtc -Descending) {
        try { $data = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch { continue }
        if ([string] $data.main -ne $Commit) { continue }
        $tag = $file.Name.Substring(0, $file.Name.Length - '-receipts.json'.Length)
        $root = Join-Path $ReleasesDir "$tag-candidate"
        if (Test-Path -LiteralPath $root -PathType Container) {
            return [ordered]@{ tag = $tag; candidate = $root; receipts = $data }
        }
    }
    $null
}

function Get-SkCodexConfigState([string] $CodexHome, [string] $VibeTarget) {
    $file = Join-Path $CodexHome 'config.toml'
    $state = [ordered]@{ file = $file; lines = 0; path = $null; matches_junction = $false }
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { $state.lines = -1; return $state }
    $found = [regex]::Matches([IO.File]::ReadAllText($file), $script:CodexLinePattern)
    $state.lines = $found.Count
    if ($found.Count -eq 1) {
        $state.path = $found[0].Groups['p'].Value
        if ($VibeTarget) {
            $expected = (Join-Path $VibeTarget 'SKILL.md').Replace('\', '/')
            $state.matches_junction = [string]::Equals($state.path, $expected, [StringComparison]::OrdinalIgnoreCase)
        }
    }
    $state
}

function Test-SkVibeRunGuard([string] $UserHome) {
    # Refuse to swap the skill under an open run. A DB with only closed runs is fine.
    $db = Join-Path $UserHome 'AppData\Local\SimonK\vibe\runs.sqlite3'
    $guard = [ordered]@{ db = $db; present = $false; runs = 0; open_runs = @(); active_attempts = 0
        halted = $false; blocked = $false; reason = '' }
    if (-not (Test-Path -LiteralPath $db -PathType Leaf)) { return $guard }
    $guard.present = $true
    $tool = Join-Path $UserHome '.claude\skills\vibe\scripts\run_state.py'
    if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
        $guard.blocked = $true; $guard.reason = 'run DB exists but run_state.py is missing'; return $guard
    }
    $r = Invoke-SkPython @($tool, '--db', $db, 'status') -AllowFailure
    if ($r.ExitCode -ne 0) { $guard.blocked = $true; $guard.reason = "run_state status rc=$($r.ExitCode)"; return $guard }
    $snap = ConvertFrom-SkJsonOutput $r.Out
    $guard.runs = @($snap.runs).Count
    $guard.open_runs = @($snap.runs | Where-Object { $_.closed -eq 0 } | ForEach-Object { [string] $_.run_id })
    $fromAccounts = (@($snap.accounts | ForEach-Object { [int] $_.active_attempts }) | Measure-Object -Sum).Sum
    $fromAttempts = @($snap.attempts | Where-Object { $_.state -in $script:ActiveAttemptStates }).Count
    $guard.active_attempts = [Math]::Max([int] $fromAccounts, $fromAttempts)
    $guard.halted = [bool] $snap.budget.halted
    if ($guard.open_runs.Count -or $guard.active_attempts -or $guard.halted) {
        $guard.blocked = $true
        $guard.reason = "open runs [$($guard.open_runs -join ', ')], active attempts $($guard.active_attempts), halted $($guard.halted)"
    }
    $guard
}

function Get-SkFreeMemoryGB {
    try {
        $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
        return [Math]::Round([double] $os.FreePhysicalMemory / 1MB, 2)
    } catch { return $null }
}

function Assert-SkFreeMemory([double] $MinGB) {
    # The build plus a 96 s selftest has stalled this PC when other agents held the RAM.
    if ($MinGB -le 0) { return }
    $free = Get-SkFreeMemoryGB
    if ($null -eq $free) { throw 'LOW_MEMORY: free memory could not be measured; pass -MinFreeMemoryGB 0 to skip the check' }
    if ($free -lt $MinGB) { throw "LOW_MEMORY: $free GB free, below $MinGB GB; close other apps or agents and rerun" }
}

function New-SkCandidateTag([string] $Repo, [string] $Commit) {
    # yyyyMMdd-vibe-<version digits>-<sha7>, e.g. 20261004-vibe-2142-e40b975 (KST date).
    $version = Get-SkGitSkillVersion $Repo $Commit 'vibe'
    if (-not $version) { throw "VERSION_UNKNOWN: skills-src/vibe/SKILL.md at $Commit" }
    '{0}-vibe-{1}-{2}' -f (Get-SkKstNow).ToString('yyyyMMdd'), ($version -replace '[^0-9A-Za-z]', ''), $Commit.Substring(0, 7)
}

function Get-SkAgyLinks([string] $UserHome) {
    # agy 1.2.x does not follow junctions but follows symlinks, so its folder holds
    # symlinks to ~/.claude/skills/<n>. Swapping junction targets needs no agy change.
    $dir = Join-Path $UserHome '.gemini\antigravity-cli\skills'
    $result = [ordered]@{ dir = $dir; present = (Test-Path -LiteralPath $dir -PathType Container); ok = @(); absent = @(); other = @() }
    if (-not $result.present) { return $result }
    foreach ($name in @('vibe', 'vibe-bot', 'model-router', 'simonk', 'multi-terminal-dispatcher', 'qa')) {
        $item = Get-Item -LiteralPath (Join-Path $dir $name) -Force -ErrorAction SilentlyContinue
        $expected = Join-Path $UserHome ".claude\skills\$name"
        if (-not $item) { $result.absent += $name }
        elseif ($item.LinkType -eq 'SymbolicLink' -and [string]::Equals([string] ($item.Target -join ''), $expected, [StringComparison]::OrdinalIgnoreCase)) { $result.ok += $name }
        else { $result.other += $name }
    }
    $result
}

function Invoke-SkSelftest([string] $Script) {
    $result = [ordered]@{ script = $Script; rc = $null; pass = 0; fail = 0; ok = $false }
    if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) { $result.rc = -1; return $result }
    $r = Invoke-SkPython @($Script) -AllowFailure
    $result.rc = $r.ExitCode
    $m = [regex]::Matches(($r.Out -join "`n"), 'PASS\s+(\d+)\D+FAIL\s+(\d+)')
    if ($m.Count) {
        $last = $m[$m.Count - 1]
        $result.pass = [int] $last.Groups[1].Value
        $result.fail = [int] $last.Groups[2].Value
    }
    $result.ok = ($r.ExitCode -eq 0 -and $result.fail -eq 0 -and $result.pass -gt 0)
    $result
}

# ---------------------------------------------------------------- plugin pins

function Test-SkPluginPinsDir([string] $Dir, $PluginInputs, [switch] $Deep) {
    # '' when valid. Cheap: each owner clone is at its pinned commit. Deep: also clean,
    # no untracked files and an LF working tree (CRLF bytes would change the bundle digest).
    foreach ($p in $PluginInputs.plugins.PSObject.Properties) {
        $root = Join-Path $Dir $p.Name
        if (-not (Test-Path -LiteralPath (Join-Path $root '.git') -PathType Container)) { return "$($p.Name)/.git missing" }
        $head = (Invoke-SkGit $root @('rev-parse', 'HEAD') -AllowFailure).Out | Select-Object -First 1
        if ($head -ne [string] $p.Value.commit) { return "$($p.Name) HEAD is not the pinned commit" }
    }
    if (-not $Deep) { return '' }
    foreach ($p in $PluginInputs.plugins.PSObject.Properties) {
        $root = Join-Path $Dir $p.Name
        $status = @((Invoke-SkGit $root @('status', '--porcelain=v1', '--untracked-files=all')).Out | Where-Object { $_ })
        if ($status.Count) { return "$($p.Name) working tree is not clean" }
        $crlf = @((Invoke-SkGit $root @('ls-files', '--eol')).Out | Where-Object { $_ -match '^i/lf\s+w/crlf' })
        if ($crlf.Count) { return "$($p.Name) has $($crlf.Count) CRLF working-tree files" }
    }
    ''
}

function Find-SkPluginPins([string] $Explicit, [string] $ReleasesDir, [string] $PluginInputsJson) {
    $pins = $PluginInputsJson | ConvertFrom-Json
    if ($Explicit) {
        $full = [IO.Path]::GetFullPath($Explicit)
        $why = Test-SkPluginPinsDir $full $pins -Deep
        if ($why) { throw "PLUGIN_PINS_INVALID: $full ($why)" }
        return [ordered]@{ path = $full; source = 'parameter'; rejected = @() }
    }
    $found = [Collections.Generic.List[object]]::new()
    foreach ($dir in Get-ChildItem -LiteralPath $ReleasesDir -Directory -Force) {
        if (Test-Path -LiteralPath (Join-Path $dir.FullName 'SimonKCore\.git') -PathType Container) { $found.Add($dir) }
        foreach ($sub in Get-ChildItem -LiteralPath $dir.FullName -Directory -Filter 'plugin-pins*' -Force -ErrorAction SilentlyContinue) {
            $found.Add($sub)
        }
    }
    $rejected = [Collections.Generic.List[string]]::new()
    foreach ($dir in ($found | Sort-Object LastWriteTimeUtc -Descending)) {
        $why = Test-SkPluginPinsDir $dir.FullName $pins
        if (-not $why) { $why = Test-SkPluginPinsDir $dir.FullName $pins -Deep }
        if (-not $why) { return [ordered]@{ path = $dir.FullName; source = 'discovered'; rejected = @($rejected) } }
        $rejected.Add("$($dir.FullName): $why")
    }
    throw "PLUGIN_PINS_REQUIRED: no valid pins dir under $ReleasesDir; pass -PluginPins <dir holding the five plugin clones at the plugin-inputs.v1.json commits with an LF working tree>"
}

# ---------------------------------------------------------------- candidate build

function Test-SkCandidatePackages([string] $CandidateRoot, $Receipts, [string] $ScriptsDir) {
    # Verify the four packages against their receipts. One retry: a first verify right
    # after a junction swap has twice returned rc=2 transiently (D-59, D-70).
    $checks = [ordered]@{
        source = @("$ScriptsDir\skill_release.py", 'verify', '--package', "$CandidateRoot\source", '--expected-digest', [string] $Receipts.source)
        bundle = @("$ScriptsDir\plugin_bundle.py", 'verify', '--package', "$CandidateRoot\candidate-safety", '--expected-digest', [string] $Receipts.claude)
        overlay = @("$ScriptsDir\codex_overlay.py", 'verify', '--package', "$CandidateRoot\codex-overlay-safety", '--overlay-digest', [string] $Receipts.overlay)
        subset = @("$ScriptsDir\codex_safe_subset.py", 'verify', '--package', "$CandidateRoot\codex-subset-safety", '--subset-digest', [string] $Receipts.codex,
            '--source-overlay', "$CandidateRoot\codex-overlay-safety", '--overlay-digest', [string] $Receipts.overlay)
    }
    $failed = @()
    foreach ($name in $checks.Keys) {
        $rc = (Invoke-SkPython $checks[$name] -AllowFailure).ExitCode
        if ($rc -ne 0) { $rc = (Invoke-SkPython $checks[$name] -AllowFailure).ExitCode }
        if ($rc -ne 0) { $failed += $name }
    }
    [ordered]@{ ok = ($failed.Count -eq 0); failed = $failed }
}

function Invoke-SkBuildCandidate {
    param([Parameter(Mandatory)] [string] $RepoRoot, [Parameter(Mandatory)] [string] $Commit,
          [Parameter(Mandatory)] [string] $Tag, [Parameter(Mandatory)] [string] $ReleasesDir,
          [string] $PluginPins, [switch] $Apply)
    $candidate = Join-Path $ReleasesDir "$Tag-candidate"
    $src = Join-Path $ReleasesDir "$Tag-src"
    $receiptsFile = Join-Path $ReleasesDir "$Tag-receipts.json"
    foreach ($p in @($candidate, $src, $receiptsFile)) {
        if (Test-SkLexists $p) { throw "CANDIDATE_EXISTS: $p (refuse to overwrite; pass another -Tag)" }
    }
    $result = [ordered]@{ status = 'preview'; tag = $Tag; main = $Commit; candidate = $candidate; src = $src
        receipts_file = $receiptsFile; plugin_pins = $PluginPins; receipts = $null }
    if (-not $Apply) { return $result }
    if (-not $PluginPins) { throw 'PLUGIN_PINS_REQUIRED: no plugin pins dir' }

    # Clean detached worktree at the exact commit; its own build scripts build the packages.
    $null = Invoke-SkGit $RepoRoot @('worktree', 'add', '-q', '--detach', $src, $Commit)
    if (@((Invoke-SkGit $src @('status', '--short')).Out | Where-Object { $_ }).Count) { throw "SRC_DIRTY: $src" }
    if (((Invoke-SkGit $src @('rev-parse', 'HEAD')).Out | Select-Object -First 1) -ne $Commit) { throw "SRC_HEAD_MISMATCH: $src" }
    $null = New-Item -ItemType Directory -Path $candidate
    $s = Join-Path $src 'scripts'
    $o1 = ConvertFrom-SkJsonOutput (Invoke-SkPython -WorkingDirectory $src @("$s\skill_release.py", 'build', '--repo', $src,
        '--ownership', "$src\distribution\skills-release.v1.json", '--output', "$candidate\source")).Out
    $o2 = ConvertFrom-SkJsonOutput (Invoke-SkPython -WorkingDirectory $src @("$s\plugin_bundle.py", 'build', '--source-package', "$candidate\source",
        '--source-digest', [string] $o1.release_digest, '--plugin-parent', $PluginPins,
        '--inputs', "$src\distribution\plugin-inputs.v1.json", '--output', "$candidate\candidate-safety", '--safety-adapter')).Out
    $o3 = ConvertFrom-SkJsonOutput (Invoke-SkPython -WorkingDirectory $src @("$s\codex_overlay.py", 'build', '--candidate', "$candidate\candidate-safety",
        '--candidate-digest', [string] $o2.bundle_digest, '--output', "$candidate\codex-overlay-safety")).Out
    $o4 = ConvertFrom-SkJsonOutput (Invoke-SkPython -WorkingDirectory $src @("$s\codex_safe_subset.py", 'build', '--source-overlay', "$candidate\codex-overlay-safety",
        '--overlay-digest', [string] $o3.overlay_digest, '--output', "$candidate\codex-subset-safety")).Out
    $receipts = [ordered]@{ main = $Commit; source = [string] $o1.release_digest; source_skills = $o1.skills
        claude = [string] $o2.bundle_digest; claude_skills = $o2.skills; overlay = [string] $o3.overlay_digest
        codex = [string] $o4.subset_digest; codex_skills = $o4.skills; codex_excluded = @($o4.excluded_skills) }
    $verify = Test-SkCandidatePackages $candidate ([pscustomobject] $receipts) $s
    if (-not $verify.ok) { throw "PACKAGE_VERIFY_FAILED: $($verify.failed -join ', ') in $candidate" }
    # Receipts are written last: their presence marks a complete, verified candidate.
    $receipts | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receiptsFile -Encoding utf8
    $result.status = 'built'
    $result.receipts = $receipts
    $result
}

# ---------------------------------------------------------------- junction swap

function Invoke-SkJunctionSwap {
    param([Parameter(Mandatory)] [string] $Tag, [string] $OldTag,
          [Parameter(Mandatory)] [string] $ReleasesDir, [Parameter(Mandatory)] [string] $UserHome,
          [Parameter(Mandatory)] [string] $CodexHome, [string] $Decision = 'manual', [switch] $Apply)
    $newRoot = Join-Path $ReleasesDir "$Tag-candidate"
    if (-not (Test-Path -LiteralPath $newRoot -PathType Container)) { throw "CANDIDATE_MISSING: $newRoot" }
    $receipts = Read-SkReceipts $ReleasesDir $Tag
    if (-not $receipts) { throw "RECEIPTS_MISSING: $Tag-receipts.json (a candidate without receipts is incomplete)" }
    $installed = Get-SkInstalledCandidate $UserHome
    $oldRoot = $null
    if ($OldTag) {
        $oldRoot = Join-Path $ReleasesDir "$OldTag-candidate"
        if (-not (Test-Path -LiteralPath $oldRoot -PathType Container)) { throw "OLD_CANDIDATE_MISSING: $oldRoot" }
    } elseif ($installed.state -eq 'junction') {
        $OldTag = $installed.tag
        $oldRoot = $installed.candidate
    } elseif ($installed.state -notin @('absent', 'directory')) {
        throw "TOPOLOGY_CHANGED: ~/.claude/skills/vibe is $($installed.state) $($installed.target)"
    }
    $result = [ordered]@{ status = 'preview'; tag = $Tag; old_tag = $OldTag; mode = $(if ($oldRoot) { 'swap' } else { 'first-install' })
        candidate = $newRoot; archive = $null; run_guard = $null; config = $null; entries = @(); undo = $null }
    if ($OldTag -and $OldTag -eq $Tag) { $result.status = 'unchanged'; return $result }

    $archive = Join-Path $UserHome ".claude\flat-link-archive\vibe-$Tag"
    if (Test-SkLexists $archive) {
        # A rolled-back attempt may be retried into a fresh sibling; anything else is never overwritten.
        $previous = $null
        try { $previous = (Get-Content -LiteralPath (Join-Path $archive 'manifest.json') -Raw | ConvertFrom-Json).state } catch { $previous = $null }
        if ($previous -ne 'rolled-back') { throw "ARCHIVE_EXISTS: $archive (state $previous; refuse to overwrite)" }
        $archive = Get-SkFreePath $archive
    }
    $result.archive = $archive
    $guard = Test-SkVibeRunGuard $UserHome
    $result.run_guard = $guard
    if ($guard.blocked) { throw "VIBE_RUN_OPEN: $($guard.reason); close it with run_state.py complete first" }

    $codexPresent = Test-Path -LiteralPath $CodexHome -PathType Container
    $entries = [Collections.Generic.List[object]]::new()
    foreach ($spec in Get-SkJunctionSpecs $UserHome $CodexHome) {
        if ($spec.Side -eq 'codex' -and -not $codexPresent) { continue }
        $e = [ordered]@{ name = $spec.Name; skill = $spec.Skill; path = $spec.Path
            old = $(if ($oldRoot) { Join-Path $oldRoot $spec.Relative } else { $null })
            new = Join-Path $newRoot $spec.Relative; action = ''; backup = Join-Path $archive $spec.Name
            before_digest = $null; new_digest = $null }
        $item = Get-Item -LiteralPath $spec.Path -Force -ErrorAction SilentlyContinue
        if ($oldRoot) {
            # Fail closed if any link points anywhere but the installed candidate.
            if (-not $item -or $item.LinkType -ne 'Junction' -or [string] ($item.Target -join '') -ne $e.old) {
                $seen = if ($item) { "$($item.LinkType) $([string] ($item.Target -join ''))" } else { 'absent' }
                throw "TOPOLOGY_CHANGED: $($spec.Name) -> $seen"
            }
            $e.action = 'swap'
        } elseif (-not $item) {
            $e.action = 'create'; $e.backup = $null
        } elseif (-not $item.LinkType) {
            $e.action = 'archive-directory'
        } else {
            throw "TOPOLOGY_CHANGED: $($spec.Name) is a $($item.LinkType)"
        }
        if (-not (Test-Path -LiteralPath (Join-Path $e.new 'SKILL.md') -PathType Leaf)) { throw "NEW_SKILL_MISSING: $($spec.Name)" }
        if ($e.action -ne 'create') { $e.before_digest = Get-SkTreeDigest $spec.Path }
        $e.new_digest = Get-SkTreeDigest $e.new
        $entries.Add($e)
    }

    # Codex config: the /vibe dedup line must name the Claude vibe junction target.
    $configFile = Join-Path $CodexHome 'config.toml'
    $newLine = 'path = "' + (Join-Path $newRoot "$script:ClaudeCore\vibe\SKILL.md").Replace('\', '/') + '"'
    $oldLine = $null
    $config = [ordered]@{ file = $configFile; action = 'none'; old_line = $null; new_line = $newLine }
    $cfgBytes = $null; $newBytes = $null
    if (-not $codexPresent) {
        $config.action = 'skip-no-codex'
    } elseif (-not (Test-Path -LiteralPath $configFile -PathType Leaf)) {
        if ($oldRoot) { throw "CODEX_CONFIG_MISSING: $configFile" }
        $config.action = 'skip-no-config'
    } else {
        $cfgBytes = [IO.File]::ReadAllBytes($configFile)
        $bom = ($cfgBytes.Length -ge 3 -and $cfgBytes[0] -eq 0xEF -and $cfgBytes[1] -eq 0xBB -and $cfgBytes[2] -eq 0xBF)
        $offset = if ($bom) { 3 } else { 0 }
        $encoding = [Text.UTF8Encoding]::new($bom, $true)
        $cfgText = $encoding.GetString($cfgBytes, $offset, $cfgBytes.Length - $offset)
        $found = [regex]::Matches($cfgText, $script:CodexLinePattern)
        if ($oldRoot) {
            $oldLine = 'path = "' + (Join-Path $oldRoot "$script:ClaudeCore\vibe\SKILL.md").Replace('\', '/') + '"'
            if ($found.Count -ne 1 -or ([regex]::Matches($cfgText, [regex]::Escape($oldLine))).Count -ne 1) {
                throw "CODEX_CONFIG_MISMATCH: expected exactly one /vibe skills.config line for $OldTag in $configFile"
            }
            $newText = $cfgText.Replace($oldLine, $newLine)
            $config.action = 'replace'
        } elseif ($found.Count -eq 0) {
            $nl = if ($cfgText.Contains("`r`n")) { "`r`n" } else { "`n" }
            $sep = if ($cfgText.Length -and -not $cfgText.EndsWith("`n")) { $nl } else { '' }
            $block = @('[[skills.config]]',
                '# Codex-safe /vibe remains in .codex/skills. Codex canonicalizes the .agents',
                '# alias to this Claude-candidate path before applying skills.config.',
                '# Remove this exact block to restore the alias in a new Codex session.',
                $newLine, 'enabled = false') -join $nl
            $newText = $cfgText + $sep + $nl + $block + $nl
            $config.action = 'append'
        } else {
            throw "CODEX_CONFIG_MISMATCH: a /vibe skills.config line exists but no candidate junction is installed"
        }
        $config.old_line = $oldLine
        $newBytes = [byte[]] ($encoding.GetPreamble() + $encoding.GetBytes($newText))
    }
    $result.config = $config
    $result.entries = @($entries | ForEach-Object { [ordered]@{ name = $_.name; action = $_.action; old = $_.old; new = $_.new } })
    if (-not $Apply) { return $result }

    $null = New-Item -ItemType Directory -Path $archive
    if ($cfgBytes) { [IO.File]::WriteAllBytes((Join-Path $archive 'codex-config.toml.before'), $cfgBytes) }
    $manifest = [ordered]@{ decision = $Decision; main = [string] $receipts.main; state = 'prepared'; receipts = $receipts
        created_kst = (Get-SkKstNow).ToString('yyyy-MM-dd HH:mm:ss'); tag = $Tag; old_tag = $OldTag
        entries = $entries; config_old = $oldLine; config_new = $newLine; config_action = $config.action }
    $manifestFile = Join-Path $archive 'manifest.json'
    $manifest | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $manifestFile -Encoding utf8
    $undo = [ordered]@{ archive = $archive; manifest = $manifest; manifest_file = $manifestFile
        applied = [Collections.Generic.List[object]]::new(); config_file = $configFile
        config_before = $cfgBytes; config_written = $null }
    $result.undo = $undo
    try {
        foreach ($e in $entries) {
            if ($e.action -ne 'create') {
                if ((Get-SkTreeDigest $e.path) -ne $e.before_digest) { throw "CHANGED_BEFORE_TRANSITION: $($e.name)" }
                [IO.Directory]::Move($e.path, $e.backup)
            }
            $undo.applied.Add($e)
            $null = New-Item -ItemType Junction -Path $e.path -Target $e.new
            if ((Get-SkTreeDigest $e.path) -ne $e.new_digest) { throw "INSTALLED_BYTES_DIFFER: $($e.name)" }
        }
        if ($newBytes) {
            [IO.File]::WriteAllBytes($configFile, $newBytes)
            $undo.config_written = $newBytes
            $after = Get-SkCodexConfigState $CodexHome (Join-Path $newRoot "$script:ClaudeCore\vibe")
            if (-not $after.matches_junction) { throw 'CODEX_CONFIG_MISMATCH: written line does not match the new vibe junction' }
        }
        $manifest.state = 'installed'
        $manifest | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $manifestFile -Encoding utf8
    } catch {
        $failure = $_
        $problems = Undo-SkJunctionSwap $undo
        if ($problems.Count) { throw "ROLLBACK_FAILED: $($failure.Exception.Message); rollback: $($problems -join '; ')" }
        throw $failure
    }
    $result.status = 'installed'
    $result
}

function Undo-SkJunctionSwap($Undo) {
    # Reverse order; new links go to <archive>\<name>-failed-new-link, backups move back.
    $problems = [Collections.Generic.List[string]]::new()
    for ($i = $Undo.applied.Count - 1; $i -ge 0; $i--) {
        $e = $Undo.applied[$i]
        try {
            if (Test-SkLexists $e.path) {
                [IO.Directory]::Move($e.path, (Get-SkFreePath (Join-Path $Undo.archive ($e.name + '-failed-new-link'))))
            }
            if ($e.backup -and (Test-SkLexists $e.backup)) { [IO.Directory]::Move($e.backup, $e.path) }
        } catch { $problems.Add("$($e.name): $($_.Exception.Message)") }
    }
    if ($Undo.config_written) {
        try {
            $now = [IO.File]::ReadAllBytes($Undo.config_file)
            if ([Convert]::ToBase64String($now) -ceq [Convert]::ToBase64String([byte[]] $Undo.config_written)) {
                [IO.File]::WriteAllBytes($Undo.config_file, [byte[]] $Undo.config_before)
            } else {
                $problems.Add('codex config changed after install; left as is')
            }
        } catch { $problems.Add("codex config: $($_.Exception.Message)") }
    }
    $Undo.applied.Clear()
    $Undo.config_written = $null
    $Undo.manifest.state = if ($problems.Count) { 'rollback-failed' } else { 'rolled-back' }
    try { $Undo.manifest | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $Undo.manifest_file -Encoding utf8 } catch { $problems.Add('manifest not updated') }
    , @($problems)
}

# ---------------------------------------------------------------- physical skills

function Invoke-SkPhysicalSync {
    param([Parameter(Mandatory)] [string] $RepoRoot, [Parameter(Mandatory)] [string] $Commit,
          [string[]] $Skills = @(), [Parameter(Mandatory)] [string] $UserHome,
          [Parameter(Mandatory)] [string] $ArchiveTag, [switch] $Apply)
    $skillsDir = Join-Path $UserHome '.claude\skills'
    $archiveRoot = Join-Path $UserHome '.claude\flat-link-archive'
    $plan = [Collections.Generic.List[object]]::new()
    foreach ($name in $Skills) {
        $dst = Join-Path $skillsDir $name
        $cmp = Compare-SkSkillTree $RepoRoot $Commit $name $dst
        $item = Get-Item -LiteralPath $dst -Force -ErrorAction SilentlyContinue
        $cmp.link = if ($item) { [string] $item.LinkType } else { '' }
        $cmp.version_main = Get-SkGitSkillVersion $RepoRoot $Commit $name
        $cmp.version_installed = Get-SkFileSkillVersion $dst
        $cmp.action = switch ($cmp.state) {
            'same' { 'none' }
            'missing' { 'replace' }
            'differs' { if ($cmp.link) { 'refuse-link' } else { 'replace' } }
            default { 'none' }
        }
        $cmp.archive = $null
        $plan.Add($cmp)
    }
    $result = [ordered]@{ status = 'preview'; archive_tag = $ArchiveTag; skills = @($plan); undo = $null }
    $refused = @($plan | Where-Object { $_.action -eq 'refuse-link' })
    if (-not $Apply) { return $result }
    if ($refused.Count) { throw "PHYSICAL_IS_LINK: $(($refused | ForEach-Object { $_.skill }) -join ', ') differ from main but are links; refuse" }

    $undo = [ordered]@{ applied = [Collections.Generic.List[object]]::new(); archive_root = $archiveRoot; tag = $ArchiveTag }
    $result.undo = $undo
    try {
        foreach ($p in @($plan | Where-Object { $_.action -eq 'replace' })) {
            # Fresh, never-existing paths: a retry in the same minute must not overwrite anything.
            $arch = Get-SkFreePath (Join-Path $archiveRoot "$($p.skill)-$ArchiveTag")
            $stage = Get-SkFreePath "$arch-staging"
            # Stage byte-exact blobs first, verify, then swap folders with two renames.
            $null = New-Item -ItemType Directory -Path $stage -Force
            $files = Get-SkSkillFiles $RepoRoot $Commit $p.skill
            $items = foreach ($rel in $files.Keys) {
                $out = Join-Path $stage ($rel.Replace('/', '\'))
                $null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out)
                [pscustomobject]@{ Blob = $files[$rel]; Path = $out; Rel = $rel }
            }
            Save-SkGitBlobs $RepoRoot @($items)
            foreach ($item in $items) {
                if ((Get-SkGitBlobId $item.Path) -ne $item.Blob) { throw "BLOB_MISMATCH: $($p.skill)/$($item.Rel)" }
            }
            $rec = [ordered]@{ skill = $p.skill; path = $p.path; archive = $null; installed = $false }
            if (Test-SkLexists $p.path) { [IO.Directory]::Move($p.path, $arch); $rec.archive = $arch }
            $undo.applied.Add($rec)
            [IO.Directory]::Move($stage, $p.path)
            $rec.installed = $true
            $p.archive = $rec.archive
            $check = Compare-SkSkillTree $RepoRoot $Commit $p.skill $p.path
            if ($check.state -ne 'same') { throw "INSTALLED_BYTES_DIFFER: $($p.skill)" }
            $p.version_installed = Get-SkFileSkillVersion $p.path
        }
    } catch {
        $failure = $_
        $problems = Undo-SkPhysicalSync $undo
        if ($problems.Count) { throw "ROLLBACK_FAILED: $($failure.Exception.Message); rollback: $($problems -join '; ')" }
        throw $failure
    }
    $result.status = 'installed'
    $result.skills = @($plan)
    $result
}

function Undo-SkPhysicalSync($Undo) {
    $problems = [Collections.Generic.List[string]]::new()
    for ($i = $Undo.applied.Count - 1; $i -ge 0; $i--) {
        $rec = $Undo.applied[$i]
        try {
            if ($rec.installed -and (Test-SkLexists $rec.path)) {
                $failed = Join-Path $Undo.archive_root "$($rec.skill)-$($Undo.tag)-failed-new"
                [IO.Directory]::Move($rec.path, (Get-SkFreePath $failed))
            }
            if ($rec.archive -and (Test-SkLexists $rec.archive)) { [IO.Directory]::Move($rec.archive, $rec.path) }
        } catch { $problems.Add("$($rec.skill): $($_.Exception.Message)") }
    }
    $Undo.applied.Clear()
    , @($problems)
}

Export-ModuleMember -Function *-Sk*
