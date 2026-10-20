<#
.SYNOPSIS
  Install the SimonK runtime into ~/.simonk/runtime.

.DESCRIPTION
  The runtime is the shared tool set (bin scripts, browse/design/pdf binaries,
  Chrome extension) that the SimonK-stack skills derived from garrytan/gstack
  (MIT) call. runtime/RUNTIME.json pins the upstream version.

  Preview by default: prints what would be copied, patched and built, and
  writes nothing. With -Apply it:
    1. copies the runtime parts of -Source (a checkout of the pinned upstream
       version) into -Target, leaving out skill folders, tests, git history
       and other hosts' folders;
    2. rewrites the hard-coded install path ".claude/skills/gstack" to
       ".simonk/runtime" in the copied text files;
    3. rebuilds the compiled tools with bun so they carry the new path;
    4. points the state folder at -StateRoot through user environment
       variables and turns off update checks and auto-upgrade.

  It never deletes or edits -Source and never reads the state folder's
  credential files. Re-running -Apply over an existing -Target needs -Force.

.EXAMPLE
  pwsh -File scripts/windows/install-runtime.ps1            # preview
  pwsh -File scripts/windows/install-runtime.ps1 -Apply     # install
#>
[CmdletBinding()]
param(
  [string]$Source = (Join-Path $HOME '.claude/skills/gstack'),
  [string]$Target = (Join-Path $HOME '.simonk/runtime'),
  [string]$StateRoot = (Join-Path $HOME '.simonk/state'),
  [switch]$Apply,
  [switch]$Force,
  [switch]$SkipBuild,
  [switch]$SkipEnv
)
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '../..')

# Git Bash, not the WSL bash.exe that System32 puts first on PATH (WSL cannot see bun or Windows paths).
function Find-GitBash {
  $git = (Get-Command git -ErrorAction SilentlyContinue).Source
  if ($git) {
    $root = Split-Path -Parent (Split-Path -Parent $git)
    foreach ($c in (Join-Path $root 'bin/bash.exe'), (Join-Path $root 'usr/bin/bash.exe')) { if (Test-Path -LiteralPath $c) { return $c } }
  }
  $fallback = Join-Path $env:ProgramFiles 'Git/bin/bash.exe'
  if (Test-Path -LiteralPath $fallback) { return $fallback }
  return $null
}
$pin = Get-Content (Join-Path $repoRoot 'runtime/RUNTIME.json') -Raw | ConvertFrom-Json

if (-not (Test-Path -LiteralPath (Join-Path $Source 'VERSION'))) { throw "Source has no VERSION file: $Source" }
$version = (Get-Content -LiteralPath (Join-Path $Source 'VERSION') -Raw).Trim()
if ($version -ne $pin.upstream_version) { throw "Source VERSION $version does not match the pinned $($pin.upstream_version)." }

# Top-level entries that are not part of the runtime.
$excludeDirs = @('.git', 'test', '.github', '.agents', '.cursor', '.factory', '.gbrain', '.hermes', '.kiro',
  '.openclaw', '.opencode', '.slate', '.gstack', 'agents', 'agents-digest', 'contrib', 'openclaw', 'supabase', 'claude-code')
$excludeFiles = @('SKILL.md', 'SKILL.md.tmpl', 'CHANGELOG.md', 'CONTRIBUTING.md', 'TODOS.md', 'README.md', 'AGENTS.md',
  'CLAUDE.md', 'conductor.json', '.gitlab-ci.yml', '.gitattributes', '.gitignore', '.osv-scanner.toml', '.env.example',
  'slop-scan.config.json', 'test-setup.ts', 'USING_GBRAIN_WITH_GSTACK.md', 'setup', 'connect-chrome')
# Skill folders (a SKILL.md at the top of the folder) belong to SimonK-stack's skills-src, not the runtime.
# browse and make-pdf are both: their src/ and dist/ are runtime tools, so only their skill files are left out.
$toolSkillDirs = @('browse', 'make-pdf')
$skillDirs = Get-ChildItem -LiteralPath $Source -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') } | Select-Object -ExpandProperty Name
$allExcludedDirs = @($excludeDirs + ($skillDirs | Where-Object { $toolSkillDirs -notcontains $_ }) + 'gstack' | Sort-Object -Unique)
$toolSkillFiles = foreach ($d in $toolSkillDirs) { foreach ($f in 'SKILL.md', 'SKILL.md.tmpl') { Join-Path (Join-Path $Source $d) $f } }

$patchRoots = @('bin', 'lib', 'browse/src', 'browse/scripts', 'design/src', 'make-pdf/src', 'hosts', 'scripts', 'extension')
$textExt = @('', '.sh', '.ts', '.js', '.mjs', '.cjs', '.json', '.md', '.py', '.yaml', '.yml', '.txt', '.html', '.css')

Write-Host "Runtime source : $Source (VERSION $version)"
Write-Host "Runtime target : $Target"
Write-Host "State root     : $StateRoot"
Write-Host ("Excluded       : {0} skill folders, {1} other folders, {2} files" -f $skillDirs.Count, $excludeDirs.Count, $excludeFiles.Count)

if (-not $Apply) {
  Write-Host 'Preview only. Re-run with -Apply to install.'
  return
}

if ((Test-Path -LiteralPath $Target) -and -not $Force) { throw "Target already exists: $Target (use -Force to update it)." }
New-Item -ItemType Directory -Force -Path $Target | Out-Null

# 1. Copy. robocopy exit codes below 8 mean success.
$xd = $allExcludedDirs | ForEach-Object { Join-Path $Source $_ }
$xf = @($excludeFiles | ForEach-Object { Join-Path $Source $_ }) + @($toolSkillFiles)
& robocopy $Source $Target /E /XD @xd /XF @xf /NFL /NDL /NJH /NJS /NP /R:1 /W:1 | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }

# 2. Rewrite the hard-coded install path in text files.
$patched = 0
foreach ($root in $patchRoots) {
  $dir = Join-Path $Target $root
  if (-not (Test-Path -LiteralPath $dir)) { continue }
  Get-ChildItem -LiteralPath $dir -Recurse -File | Where-Object {
    $_.FullName -notmatch '[\\/]node_modules[\\/]' -and $_.FullName -notmatch '[\\/]dist[\\/]' -and
    $_.Length -lt 5MB -and ($textExt -contains $_.Extension.ToLowerInvariant())
  } | ForEach-Object {
    $raw = [System.IO.File]::ReadAllText($_.FullName)
    if ($raw.Contains('.claude/skills/gstack')) {
      [System.IO.File]::WriteAllText($_.FullName, $raw.Replace('.claude/skills/gstack', '.simonk/runtime'), [System.Text.UTF8Encoding]::new($false))
      $patched++
    }
  }
}
Write-Host "Patched install path in $patched files."

# 3. Rebuild the compiled tools so they carry the new path.
if (-not $SkipBuild) {
  $bun = (Get-Command bun -ErrorAction SilentlyContinue).Source
  $bash = Find-GitBash
  if (-not $bun -or -not $bash) { throw 'bun and Git Bash are required to rebuild the runtime tools (or pass -SkipBuild).' }
  # The helper scripts call plain `bun`, so bash needs bun's folder on PATH.
  $env:PATH = (Split-Path -Parent $bun) + [IO.Path]::PathSeparator + $env:PATH
  Push-Location $Target
  try {
    $builds = @(
      @('browse/src/cli.ts', 'browse/dist/browse'),
      @('browse/src/find-browse.ts', 'browse/dist/find-browse'),
      @('design/src/cli.ts', 'design/dist/design'),
      @('make-pdf/src/cli.ts', 'make-pdf/dist/pdf'),
      @('bin/gstack-global-discover.ts', 'bin/gstack-global-discover')
    )
    foreach ($b in $builds) {
      & $bun build --compile $b[0] --outfile $b[1] | Out-Null
      if ($LASTEXITCODE -ne 0) { throw "bun build failed for $($b[0])" }
    }
    & $bash browse/scripts/build-node-server.sh | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'build-node-server.sh failed' }
    & $bash scripts/write-version-files.sh browse/dist/.version design/dist/.version make-pdf/dist/.version | Out-Null
    Get-ChildItem -LiteralPath $Target -Filter '.*.bun-build' -File -ErrorAction SilentlyContinue | Remove-Item -Force
    Set-Content -LiteralPath (Join-Path $Target 'browse/dist/.build-complete') -Value 'complete' -Encoding utf8NoBOM
  } finally { Pop-Location }
}

# 4. State folder and config.
New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
if (-not $SkipEnv) {
  foreach ($name in $pin.state_env) {
    [Environment]::SetEnvironmentVariable($name, $StateRoot, 'User')
    Set-Item -Path "Env:$name" -Value $StateRoot
  }
  Write-Host "Set user environment: $($pin.state_env -join ', ') = $StateRoot (open a new terminal to pick it up)."
}
$bashExe = Find-GitBash
if ($bashExe -and (Test-Path -LiteralPath (Join-Path $Target 'bin/gstack-config'))) {
  foreach ($kv in $pin.config.PSObject.Properties) {
    & $bashExe (Join-Path $Target 'bin/gstack-config') set $kv.Name $kv.Value | Out-Null
  }
}

# Leftover references to the old install path inside the runtime (text files only).
$left = Get-ChildItem -LiteralPath $Target -Recurse -File | Where-Object {
  $_.FullName -notmatch '[\\/]node_modules[\\/]' -and $_.Length -lt 200MB
} | Where-Object { Select-String -LiteralPath $_.FullName -SimpleMatch '.claude/skills/gstack' -Quiet -ErrorAction SilentlyContinue }
Write-Host ("Files still naming .claude/skills/gstack: {0}" -f @($left).Count)
@($left) | Select-Object -First 10 | ForEach-Object { Write-Host "  $($_.FullName.Substring($Target.Length + 1))" }
Write-Host 'Done.'
