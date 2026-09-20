# install-widget.ps1 - build and install AI Usage Widget v2 from the SimonK-stack sources.
# Windows PowerShell 5.1 compatible. ASCII only on purpose (PS 5.1 misreads BOM-less UTF-8).
#
#   install-widget.ps1                 build, verify, install per-user, launch
#   install-widget.ps1 -DryRun         print the plan and the checks, change nothing
#   install-widget.ps1 -Status         report what is installed and running, change nothing
#   install-widget.ps1 -Uninstall      remove the app (refuses while the Claude bridge is installed)
#
# Exit codes: 0 ok, 1 failed step, 2 precondition missing, 3 refused for safety.

[CmdletBinding()]
param(
  [string]$Source = '',
  [switch]$DryRun,
  [switch]$Status,
  [switch]$Uninstall,
  [switch]$SkipVerify,
  [switch]$NoLaunch,
  [switch]$Force
)

$ErrorActionPreference = 'Stop'
$AppName       = 'ai-usage-widget'
$ExeName       = 'ai-usage-widget.exe'
$InstallDir    = Join-Path $env:LOCALAPPDATA ('Programs\' + $AppName)
$InstalledExe  = Join-Path $InstallDir $ExeName
$RunKey        = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$RunValueName  = 'AIUsageWidgetV2'
$UserData      = Join-Path $env:APPDATA 'AIUsageWidgetV2'
$RepoUrl       = 'https://github.com/Simon-YHKim/SimonK-stack.git'
$RepoSubdir    = 'apps\ai-usage-widget'

function Say([string]$text) { Write-Output ('[aiuw] ' + $text) }
function Fail([int]$code, [string]$text) { Write-Output ('[aiuw] FAILED: ' + $text); exit $code }

function Get-WidgetProcesses {
  @(Get-Process -Name 'ai-usage-widget' -ErrorAction SilentlyContinue)
}

function Test-ClaudeBridgeInstalled {
  $settings = Join-Path $env:USERPROFILE '.claude\settings.json'
  if (-not (Test-Path -LiteralPath $settings)) { return $false }
  try {
    $json = Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json
    return ([string]$json.statusLine.command) -match 'aiuw-claude-bridge'
  } catch { return $false }
}

function Show-Status {
  Say ('installed exe : ' + $(if (Test-Path -LiteralPath $InstalledExe) { $InstalledExe } else { '(not installed)' }))
  $procs = Get-WidgetProcesses
  $paths = @($procs | ForEach-Object { $_.Path } | Where-Object { $_ } | Sort-Object -Unique)
  Say ('running       : ' + $procs.Count + ' process(es) ' + ($paths -join '; '))
  $run = (Get-ItemProperty -Path $RunKey -ErrorAction SilentlyContinue).$RunValueName
  Say ('autostart     : ' + $(if ($run) { $run } else { '(off)' }))
  if ($run -and (Test-Path -LiteralPath $InstalledExe) -and ($run -notlike ('*' + $InstalledExe + '*'))) {
    Say 'autostart points at another executable; start the installed app once and it re-registers itself'
  }
  Say ('user data     : ' + $(if (Test-Path -LiteralPath $UserData) { $UserData } else { '(none yet)' }))
  Say ('claude bridge : ' + $(if (Test-ClaudeBridgeInstalled) { 'installed in ~/.claude/settings.json' } else { 'not installed in the default profile' }))
  foreach ($cli in 'claude', 'codex', 'grok', 'agy') {
    $cmd = Get-Command $cli -ErrorAction SilentlyContinue
    Say (('cli {0,-7}: ' -f $cli) + $(if ($cmd) { $cmd.Source } else { '(not on PATH)' }))
  }
}

function Resolve-Source {
  if ($Source -ne '') {
    if (-not (Test-Path -LiteralPath (Join-Path $Source 'package.json'))) { Fail 2 ('-Source has no package.json: ' + $Source) }
    return (Resolve-Path -LiteralPath $Source).Path
  }
  $candidates = @()
  # 1) running from a SimonK-stack checkout: <repo>\skills-src\ai-usage-widget-install\scripts
  $candidates += (Join-Path $PSScriptRoot ('..\..\..\' + $RepoSubdir))
  # 2) an explicit stack root, 3) the usual local clone
  if ($env:SIMONK_STACK_ROOT) { $candidates += (Join-Path $env:SIMONK_STACK_ROOT $RepoSubdir) }
  $candidates += ('E:\Coding Infra\Harrness Eng\SimonK-stack\' + $RepoSubdir)
  foreach ($c in $candidates) {
    if (Test-Path -LiteralPath (Join-Path $c 'package.json')) { return (Resolve-Path -LiteralPath $c).Path }
  }
  # 4) last resort: a shallow clone of the public repository into the widget's own data folder
  $cloneRoot = Join-Path $env:LOCALAPPDATA 'AIUsageWidget\src\SimonK-stack'
  if ($DryRun) { Say ('would clone ' + $RepoUrl + ' -> ' + $cloneRoot); return (Join-Path $cloneRoot $RepoSubdir) }
  if (Test-Path -LiteralPath (Join-Path $cloneRoot '.git')) {
    Say ('updating clone ' + $cloneRoot)
    & git -C $cloneRoot pull --ff-only | Out-Null
  } else {
    Say ('cloning ' + $RepoUrl)
    New-Item -ItemType Directory -Force -Path (Split-Path $cloneRoot) | Out-Null
    & git clone --depth 1 $RepoUrl $cloneRoot | Out-Null
  }
  if ($LASTEXITCODE -ne 0) { Fail 1 'git clone/pull failed' }
  return (Join-Path $cloneRoot $RepoSubdir)
}

function Invoke-Step([string]$label, [scriptblock]$body) {
  Say ('> ' + $label)
  & $body
  if ($LASTEXITCODE -ne 0) { Fail 1 ($label + ' exited with ' + $LASTEXITCODE) }
}

# ---------------------------------------------------------------------------

if ($env:OS -ne 'Windows_NT') { Fail 2 'Windows only' }

if ($Status) { Show-Status; exit 0 }

if ($Uninstall) {
  $uninstaller = Join-Path $InstallDir ('Uninstall ' + $ExeName)
  if (-not (Test-Path -LiteralPath $uninstaller)) { Fail 2 'not installed (no uninstaller found)' }
  if ((Test-ClaudeBridgeInstalled) -and (-not $Force)) {
    Say 'The Claude statusline bridge is still installed in ~/.claude/settings.json.'
    Say 'The uninstaller does not restore it. Open the widget > Accounts > Claude > [Remove from default profile] first,'
    Say 'or re-run with -Force and restore settings.json from its settings.json.aiuw-backup-* copy yourself.'
    exit 3
  }
  if ($DryRun) { Say ('would stop the widget and run: "' + $uninstaller + '" /currentuser /S'); exit 0 }
  Get-WidgetProcesses | Stop-Process -Force -Confirm:$false
  Start-Sleep -Seconds 2
  $p = Start-Process -FilePath $uninstaller -ArgumentList '/currentuser', '/S' -PassThru -Wait
  if ($p.ExitCode -ne 0) { Fail 1 ('uninstaller exited with ' + $p.ExitCode) }
  Say ('uninstalled. User data and signed-in CLI profiles were kept: ' + $UserData + ' and ' + (Join-Path $env:LOCALAPPDATA 'AIUsageWidget'))
  exit 0
}

# --- install ---------------------------------------------------------------

foreach ($tool in 'node', 'pnpm', 'git') {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { Fail 2 ($tool + ' is not on PATH') }
}
Say ('node ' + (& node --version) + ' / pnpm ' + (& pnpm --version))

$src = Resolve-Source
Say ('source: ' + $src)

if ($DryRun) {
  Say 'plan: pnpm install --frozen-lockfile > pnpm verify > stop running widget > pnpm dist > run installer /S > launch > status'
  Show-Status
  exit 0
}

Push-Location -LiteralPath $src
try {
  Invoke-Step 'pnpm install --frozen-lockfile' { & pnpm install --frozen-lockfile '--config.confirmModulesPurge=false' | Select-Object -Last 3 }
  if (-not $SkipVerify) {
    Invoke-Step 'pnpm verify (typecheck + lint + tests)' { & pnpm verify | Select-Object -Last 6 }
  } else {
    Say 'verify skipped on request (-SkipVerify)'
  }
  # The unpacked build and the installed app share the executable name; both must be closed before packaging.
  $running = Get-WidgetProcesses
  if ($running.Count -gt 0) {
    Say ('stopping ' + $running.Count + ' widget process(es)')
    $running | Stop-Process -Force -Confirm:$false
    Start-Sleep -Seconds 2
  }
  Invoke-Step 'pnpm dist (NSIS installer)' { & pnpm dist | Select-String -Pattern 'target=nsis|ERR' | Select-Object -Last 2 }
  $setup = Get-ChildItem -LiteralPath (Join-Path $src 'release') -Filter ($AppName + '-setup-*.exe') | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $setup) { Fail 1 'installer was not produced' }
  Say ('installer: ' + $setup.Name + ' sha256 ' + (Get-FileHash -LiteralPath $setup.FullName -Algorithm SHA256).Hash.Substring(0, 16) + ' (unsigned, per-user)')
  $p = Start-Process -FilePath $setup.FullName -ArgumentList '/S' -PassThru -Wait
  if ($p.ExitCode -ne 0) { Fail 1 ('installer exited with ' + $p.ExitCode) }
} finally {
  Pop-Location
}

if (-not (Test-Path -LiteralPath $InstalledExe)) { Fail 1 ('installed exe not found: ' + $InstalledExe) }

if (-not $NoLaunch) {
  Start-Sleep -Seconds 2
  if ((Get-WidgetProcesses).Count -eq 0) { Start-Process -FilePath $InstalledExe -WorkingDirectory $InstallDir }
  Start-Sleep -Seconds 6
  if ((Get-WidgetProcesses).Count -eq 0) { Fail 1 'the installed widget did not stay running' }
}

Show-Status
Say 'done. First run: widget > Accounts tab > add an account per provider and sign in.'
Say 'Claude numbers need the bridge: Accounts > Claude > [Install in default Claude profile].'
exit 0
