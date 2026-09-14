# AI Usage Widget - Claude Code statusLine bridge (PowerShell 5.1 fallback when node is missing).
# Same behaviour and record format as aiuw-claude-bridge.cjs: stores only rate_limits
# (five_hour / seven_day) and the model id/name, then runs a recorded wrapped
# statusLine command with the same stdin, or prints nothing.
param(
  [string]$Key = '',
  [string]$Out = '',
  [string]$Shell = 'auto'
)

$ErrorActionPreference = 'Stop'
$Marker = 'aiuw-claude-bridge'
$RecordVersion = 1
$MaxFileBytes = 256KB
$WrapTimeoutMs = 30000
$Utf8 = New-Object System.Text.UTF8Encoding($false)

function Get-NormalizedConfigDir([string]$Dir) {
  $full = [System.IO.Path]::GetFullPath($Dir).Replace('/', '\')
  if ($full.Length -gt 3) { $full = $full.TrimEnd('\') }
  return $full.ToLowerInvariant()
}

function Get-BridgeKey([string]$ConfigDir) {
  if ([string]::IsNullOrEmpty($ConfigDir)) { $text = '~/.claude default' } else { $text = Get-NormalizedConfigDir $ConfigDir }
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try { $bytes = $sha.ComputeHash($Utf8.GetBytes($text)) } finally { $sha.Dispose() }
  return (-join ($bytes | ForEach-Object { $_.ToString('x2') })).Substring(0, 16)
}

function Get-FiniteNumber($Value) {
  if ($null -eq $Value) { return $null }
  if ($Value -is [int] -or $Value -is [long] -or $Value -is [double] -or $Value -is [decimal]) {
    $d = [double]$Value
    if ([double]::IsNaN($d) -or [double]::IsInfinity($d)) { return $null }
    return $d
  }
  return $null
}

function Get-Prop($Object, [string]$Name) {
  if ($null -eq $Object -or -not ($Object -is [System.Management.Automation.PSCustomObject])) { return $null }
  $prop = $Object.PSObject.Properties[$Name]
  if ($null -eq $prop) { return $null }
  return $prop.Value
}

function Read-JsonFile([string]$Path) {
  try {
    $info = New-Object System.IO.FileInfo($Path)
    if (-not $info.Exists -or $info.Length -gt $MaxFileBytes) { return $null }
    return ([System.IO.File]::ReadAllText($Path, $Utf8) | ConvertFrom-Json)
  } catch {
    return $null
  }
}

function Write-FileAtomic([string]$Path, [string]$Text) {
  $tmp = "$Path.$PID.$([DateTime]::UtcNow.Ticks).tmp"
  try {
    [System.IO.File]::WriteAllText($tmp, $Text, $Utf8)
    if ([System.IO.File]::Exists($Path)) { [System.IO.File]::Replace($tmp, $Path, $null) } else { [System.IO.File]::Move($tmp, $Path) }
  } catch {
    if ([System.IO.File]::Exists($tmp)) { [System.IO.File]::Delete($tmp) }
    throw
  }
}

function Get-ShortString($Value) {
  if ($Value -is [string] -and $Value.Length -gt 0 -and $Value.Length -le 100) { return $Value }
  return $null
}

function Save-Reading([byte[]]$InputBytes) {
  $data = $null
  try { $data = ($Utf8.GetString($InputBytes) | ConvertFrom-Json) } catch { $data = $null }
  $recordPath = [System.IO.Path]::Combine($Out, "$Key.json")
  $previous = Read-JsonFile $recordPath
  $prevWindows = $null
  if ($null -ne $previous -and (Get-Prop $previous 'v') -eq $RecordVersion -and (Get-Prop $previous 'configDirHash') -eq $Key) {
    $prevWindows = Get-Prop $previous 'rate_limits'
  } else {
    $previous = $null
  }
  $now = [long][DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $rateLimits = Get-Prop $data 'rate_limits'
  $windows = [ordered]@{}
  $updated = $false
  foreach ($name in @('five_hour', 'seven_day')) {
    $incoming = Get-Prop $rateLimits $name
    if ($null -ne $incoming) {
      $used = Get-FiniteNumber (Get-Prop $incoming 'used_percentage')
      $resets = Get-FiniteNumber (Get-Prop $incoming 'resets_at')
      if ($null -ne $used -or $null -ne $resets) {
        $windows[$name] = [ordered]@{ used_percentage = $used; resets_at = $resets; captured_at = $now }
        $updated = $true
        continue
      }
    }
    $prev = Get-Prop $prevWindows $name
    if ($null -eq $prev) { continue }
    $prevResets = Get-FiniteNumber (Get-Prop $prev 'resets_at')
    $expired = ($null -ne $prevResets) -and (($prevResets * 1000) -le $now)
    if ($null -eq $rateLimits -or $expired) {
      $windows[$name] = [ordered]@{
        used_percentage = Get-FiniteNumber (Get-Prop $prev 'used_percentage')
        resets_at = $prevResets
        captured_at = Get-FiniteNumber (Get-Prop $prev 'captured_at')
      }
    }
  }
  $capturedAt = $null
  if ($updated) { $capturedAt = $now } elseif ($null -ne $previous) { $capturedAt = Get-FiniteNumber (Get-Prop $previous 'capturedAt') }
  $record = [ordered]@{
    v = $RecordVersion
    configDirHash = $Key
    seenAt = $now
    capturedAt = $capturedAt
    rate_limits = $windows
    runtime = 'powershell'
  }
  $model = Get-Prop $data 'model'
  if ($null -ne $model) {
    $m = [ordered]@{}
    $id = Get-ShortString (Get-Prop $model 'id')
    $display = Get-ShortString (Get-Prop $model 'display_name')
    if ($null -ne $id) { $m['id'] = $id }
    if ($null -ne $display) { $m['display_name'] = $display }
    if ($m.Count -gt 0) { $record['model'] = $m }
  }
  [System.IO.Directory]::CreateDirectory($Out) | Out-Null
  Write-FileAtomic $recordPath ($record | ConvertTo-Json -Depth 6 -Compress)
}

function Get-WrappedCommand {
  $wrap = Read-JsonFile ([System.IO.Path]::Combine($Out, "$Key.wrap.json"))
  if ($null -eq $wrap -or (Get-Prop $wrap 'v') -ne $RecordVersion) { return $null }
  $previous = Get-Prop $wrap 'previous'
  if ((Get-Prop $previous 'present') -ne $true) { return $null }
  $command = Get-Prop (Get-Prop $previous 'value') 'command'
  if (-not ($command -is [string]) -or $command.Trim().Length -eq 0 -or $command.Contains($Marker)) { return $null }
  return $command
}

function Find-GitBash {
  $candidates = New-Object System.Collections.Generic.List[string]
  if ($env:CLAUDE_CODE_GIT_BASH_PATH) { $candidates.Add($env:CLAUDE_CODE_GIT_BASH_PATH) }
  foreach ($rawDir in ($env:PATH -split ';')) {
    $dir = $rawDir.Trim().Trim('"')
    if (-not $dir -or -not [System.IO.Path]::IsPathRooted($dir)) { continue }
    if (-not [System.IO.File]::Exists([System.IO.Path]::Combine($dir, 'git.exe'))) { continue }
    $parent = [System.IO.Path]::GetDirectoryName($dir)
    $candidates.Add([System.IO.Path]::Combine($parent, 'bin', 'bash.exe'))
    $grand = [System.IO.Path]::GetDirectoryName($parent)
    if ($grand) { $candidates.Add([System.IO.Path]::Combine($grand, 'bin', 'bash.exe')) }
  }
  if ($env:ProgramFiles) { $candidates.Add([System.IO.Path]::Combine($env:ProgramFiles, 'Git', 'bin', 'bash.exe')) }
  if (${env:ProgramFiles(x86)}) { $candidates.Add([System.IO.Path]::Combine(${env:ProgramFiles(x86)}, 'Git', 'bin', 'bash.exe')) }
  foreach ($candidate in $candidates) {
    if ([System.IO.File]::Exists($candidate)) { return $candidate }
  }
  return $null
}

# CommandLineToArgvW-compatible quoting (.NET Framework has no ArgumentList).
function ConvertTo-ArgString([string[]]$Arguments) {
  $parts = foreach ($arg in $Arguments) {
    if ($arg.Length -gt 0 -and $arg -notmatch '[\s"]') { $arg; continue }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('"')
    $slashes = 0
    foreach ($ch in $arg.ToCharArray()) {
      if ($ch -eq [char]'\') { $slashes++; continue }
      if ($ch -eq [char]'"') { [void]$sb.Append([char]'\', $slashes * 2 + 1) } elseif ($slashes -gt 0) { [void]$sb.Append([char]'\', $slashes) }
      $slashes = 0
      [void]$sb.Append($ch)
    }
    if ($slashes -gt 0) { [void]$sb.Append([char]'\', $slashes * 2) }
    [void]$sb.Append('"')
    $sb.ToString()
  }
  return ($parts -join ' ')
}

function Invoke-Wrapped([byte[]]$InputBytes) {
  $command = $null
  try { $command = Get-WrappedCommand } catch { $command = $null }
  if ($null -eq $command) { return 0 }
  $bash = $null
  if ($Shell -ne 'powershell') { $bash = Find-GitBash }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  if ($null -ne $bash) {
    $psi.FileName = $bash
    $psi.Arguments = ConvertTo-ArgString @('-c', $command)
  } elseif ($Shell -eq 'bash') {
    return 0
  } else {
    $root = $env:SystemRoot
    if (-not $root) { $root = 'C:\Windows' }
    $psi.FileName = [System.IO.Path]::Combine($root, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($command))
    $psi.Arguments = ConvertTo-ArgString @('-NoProfile', '-NonInteractive', '-EncodedCommand', $encoded)
  }
  $psi.UseShellExecute = $false
  $psi.RedirectStandardInput = $true
  $psi.CreateNoWindow = $true
  $process = [System.Diagnostics.Process]::Start($psi)
  try {
    $process.StandardInput.BaseStream.Write($InputBytes, 0, $InputBytes.Length)
    $process.StandardInput.Close()
  } catch {
    # The wrapped command may exit without reading stdin.
  }
  if (-not $process.WaitForExit($WrapTimeoutMs)) {
    try { $process.Kill() } catch { }
    return 1
  }
  return $process.ExitCode
}

$exitCode = 0
try {
  if (-not $Key) { $Key = Get-BridgeKey $env:CLAUDE_CONFIG_DIR }
  if (-not $Out -and $env:LOCALAPPDATA) { $Out = [System.IO.Path]::Combine($env:LOCALAPPDATA, 'AIUsageWidget', 'bridge', 'claude') }
  if ($Key -cmatch '^[0-9a-f]{16}$' -and $Out -and [System.IO.Path]::IsPathRooted($Out)) {
    $stdin = [Console]::OpenStandardInput()
    $buffer = New-Object System.IO.MemoryStream
    $stdin.CopyTo($buffer)
    $inputBytes = $buffer.ToArray()
    try { Save-Reading $inputBytes } catch { }
    $exitCode = Invoke-Wrapped $inputBytes
  }
} catch {
  $exitCode = 0
}
exit $exitCode
