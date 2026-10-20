<#
.SYNOPSIS
  Install the SimonK runtime into ~/.simonk/runtime (Windows wrapper).

.DESCRIPTION
  Thin wrapper over scripts/install_runtime.py, which does the work on every
  platform: it takes the pinned upstream commit's files from git objects,
  rewrites the install path, rebuilds the compiled tools with bun in a staging
  folder, swaps it in, turns off update checks and auto-upgrade, and points the
  state folder at ~/.simonk/state. Preview by default.

.EXAMPLE
  pwsh -File scripts/windows/install-runtime.ps1                 # preview
  pwsh -File scripts/windows/install-runtime.ps1 -Apply          # install
  pwsh -File scripts/windows/install-runtime.ps1 -Apply -Force   # replace an existing runtime
  pwsh -File scripts/windows/install-runtime.ps1 -Apply -Clone   # build from a fresh clone of the pin
#>
[CmdletBinding()]
param(
  [string]$Source,
  [switch]$Clone,
  [switch]$Apply,
  [switch]$Force,
  [switch]$SkipBuild,
  [switch]$SkipConfig,
  [switch]$SkipEnv
)
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot '../install_runtime.py'
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { throw 'python is required (scripts/install_runtime.py).' }
$argv = @('-B', $script)
if ($Source) { $argv += @('--source', $Source) }
if ($Clone) { $argv += '--clone' }
if ($Apply) { $argv += '--apply' }
if ($Force) { $argv += '--force' }
if ($SkipBuild) { $argv += '--skip-build' }
if ($SkipConfig) { $argv += '--skip-config' }
if ($SkipEnv) { $argv += '--skip-env' }
& $python @argv
exit $LASTEXITCODE
