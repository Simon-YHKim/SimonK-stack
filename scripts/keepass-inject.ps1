# keepass-inject.ps1 — KeePassXC vault에서 API key를 PowerShell 환경변수로 자동 inject
#
# Sourced 또는 직접 호출:
#   . scripts/keepass-inject.ps1                       # dot-source (함수만 로드)
#   Invoke-KeepassInject                               # 모든 known entry inject (master password 1회 prompt)
#   Invoke-KeepassInject -Entry "Zotero API Key"       # 특정 entry만
#
# 사용 가이드:
#   1. 사용자가 PowerShell session 시작 시 1회 호출
#   2. master password 1회 prompt → 모든 known entry inject
#   3. 그 session 안에서 모든 env var 자동 사용 (Claude Code · simonK · zotero-mcp 등)
#
# 보안:
#   - master password는 *현재 session* 메모리만 (file/registry/env에 저장 X)
#   - keepassxc-cli stdin pipe 통해 1회 사용 후 즉시 release
#   - 환경변수는 *current process scope* (자식 process 상속, 새 session에는 X)
#
# Default vault: E:\Coding Infra\암호.kdbx
# Override: $env:SIMONK_KEEPASS_VAULT

[CmdletBinding()]
param(
    [string] $Entry = '',
    [string] $VaultPath = ''
)

function Get-SimonKeepassVault {
    if ($VaultPath) { return $VaultPath }
    if ($env:SIMONK_KEEPASS_VAULT) { return $env:SIMONK_KEEPASS_VAULT }
    return 'E:\Coding Infra\암호.kdbx'
}

function Test-KeepassXcCli {
    return [bool](Get-Command keepassxc-cli -ErrorAction SilentlyContinue)
}

# Known entry → env var 매핑
$script:KeepassEntries = @{
    'Zotero API Key' = @('ZOTERO_API_KEY')
    'Anthropic API Key' = @('ANTHROPIC_API_KEY')
    'OpenAI API Key' = @('OPENAI_API_KEY')
    'Gemini API Key' = @('GEMINI_API_KEY', 'GOOGLE_API_KEY')
    'GitHub PAT' = @('GH_TOKEN', 'GITHUB_TOKEN')
}

function Invoke-KeepassInject {
    [CmdletBinding()]
    param(
        [string] $Entry = '',
        [SecureString] $MasterPassword = $null,
        [switch] $Silent = $false
    )

    $vault = Get-SimonKeepassVault

    if (-not (Test-KeepassXcCli)) {
        if (-not $Silent) { Write-Host '[keepass] keepassxc-cli not found in PATH' -ForegroundColor Red }
        return $false
    }
    if (-not (Test-Path $vault)) {
        if (-not $Silent) { Write-Host ('[keepass] vault not found: ' + $vault) -ForegroundColor Red }
        return $false
    }

    # Master password 입력 (1회만)
    if (-not $MasterPassword) {
        $MasterPassword = Read-Host -Prompt ('[keepass] master password for ' + (Split-Path -Leaf $vault)) -AsSecureString
    }
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($MasterPassword)
    $plainPass = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)

    # 처리할 entry 결정
    $entriesToProcess = if ($Entry) { @($Entry) } else { $script:KeepassEntries.Keys }

    $injected = 0
    foreach ($e in $entriesToProcess) {
        if (-not $script:KeepassEntries.ContainsKey($e)) {
            if (-not $Silent) { Write-Host ('[keepass] unknown entry: ' + $e) -ForegroundColor Yellow }
            continue
        }
        $envVars = $script:KeepassEntries[$e]
        try {
            $value = $plainPass | & keepassxc-cli show $vault $e -a Password -q 2>$null
            if ($LASTEXITCODE -eq 0 -and $value) {
                $value = $value.Trim()
                foreach ($v in $envVars) {
                    Set-Item -Path "env:$v" -Value $value
                }
                if (-not $Silent) {
                    $masked = if ($value.Length -gt 14) { $value.Substring(0,8) + '...' + $value.Substring($value.Length-4) } else { '<short>' }
                    Write-Host ('[keepass] inject ' + ($envVars -join ',') + ' = ' + $masked) -ForegroundColor Green
                }
                $injected++
            }
        } catch {}
    }

    # release master password
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    Remove-Variable plainPass, MasterPassword -ErrorAction SilentlyContinue

    if (-not $Silent) { Write-Host ('[keepass] ' + $injected + ' entries injected to current session') -ForegroundColor Cyan }
    return ($injected -gt 0)
}

# Export-friendly alias
Set-Alias -Name keepass-inject -Value Invoke-KeepassInject -Scope Global -Force -ErrorAction SilentlyContinue
