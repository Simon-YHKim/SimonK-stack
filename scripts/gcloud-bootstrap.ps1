# gcloud-bootstrap.ps1 — gcloud 자동 인증 진단 + ADC + project 자동 설정
#
# Sourced 또는 직접 호출:
#   . scripts/gcloud-bootstrap.ps1                    # dot-source (함수만 로드)
#   . scripts/gcloud-bootstrap.ps1 -Auto              # 자동 진단 + 안내
#   . scripts/gcloud-bootstrap.ps1 -Auto -Silent      # 자동 (silent, 인증 OK 시 출력 없음)
#
# 동작:
#   1. gcloud CLI 존재 확인 (없으면 silent skip — 다른 환경에서도 작동)
#   2. gcloud auth list 자동 체크
#      - 인증 없음 → 콘솔에 1줄 안내 (자동 browser 호출 X — noise 방지)
#      - 인증 있음 → 활성 계정 출력 (silent 아닌 경우)
#   3. ADC (Application Default Credentials) 자동 verify
#      - 없으면 안내
#      - 있으면 GOOGLE_APPLICATION_CREDENTIALS 환경변수 자동 set
#   4. 활성 project 확인
#      - simonk-personal 유령 prj면 eject-button 자동 되돌림 (safe default)
#   5. Claude Code session에 inject — env vars (GOOGLE_CLOUD_PROJECT 등)
#
# 안전:
#   - 비밀번호 절대 저장 X (OAuth refresh token만 gcloud 표준 위치)
#   - 사용자 인터랙션 1회 OAuth만 (이후 영구)

[CmdletBinding()]
param(
    [switch] $Auto = $false,
    [switch] $Silent = $false
)

function Test-GcloudInstalled {
    return [bool](Get-Command gcloud -ErrorAction SilentlyContinue)
}

function Get-GcloudActiveAccount {
    try {
        $accounts = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
        if ($accounts) { return ($accounts -split "`n")[0] }
    } catch {}
    return $null
}

function Get-GcloudActiveProject {
    try {
        $p = gcloud config get-value project 2>$null
        if ($p -and $p -ne '(unset)') { return $p.Trim() }
    } catch {}
    return $null
}

function Test-GcloudAdcExists {
    $adcPath = "$env:APPDATA\gcloud\application_default_credentials.json"
    return (Test-Path $adcPath)
}

function Get-GcloudAdcPath {
    return "$env:APPDATA\gcloud\application_default_credentials.json"
}

function Get-GcloudUserProjects {
    try {
        $projects = gcloud projects list --format="value(projectId)" 2>$null
        if ($projects) { return ($projects -split "`n") | Where-Object { $_.Trim() } }
    } catch {}
    return @()
}

function Invoke-GcloudBootstrap {
    [CmdletBinding()]
    param(
        [switch] $Silent = $false
    )

    if (-not (Test-GcloudInstalled)) {
        if (-not $Silent) { Write-Host '[gcloud-bootstrap] gcloud CLI not installed — skip' -ForegroundColor DarkGray }
        return $false
    }

    # 1. Auth check
    $account = Get-GcloudActiveAccount
    if (-not $account) {
        Write-Host '[gcloud-bootstrap] Google 인증 필요 — 다음 1회만:' -ForegroundColor Yellow
        Write-Host '  gcloud auth login                            # 1회 brwoser OAuth (사용자가 Google에서 로그인 + 권한 승인)' -ForegroundColor Cyan
        Write-Host '  gcloud auth application-default login        # ADC (Python 라이브러리용)' -ForegroundColor Cyan
        return $false
    }
    if (-not $Silent) { Write-Host ('[gcloud-bootstrap] auth: ' + $account) -ForegroundColor Green }

    # 2. Active project — simonk-personal 유령 자동 fix
    $project = Get-GcloudActiveProject
    $userProjects = Get-GcloudUserProjects
    if ($project -and ($userProjects -notcontains $project)) {
        Write-Host ('[gcloud-bootstrap] active project ' + $project + ' 는 실존 X (quota 초과 등) — eject-button 자동 되돌림') -ForegroundColor Yellow
        if ($userProjects -contains 'eject-button') {
            gcloud config set project eject-button 2>&1 | Out-Null
            $project = 'eject-button'
        } elseif ($userProjects.Count -gt 0) {
            $fallback = $userProjects[0]
            gcloud config set project $fallback 2>&1 | Out-Null
            $project = $fallback
            Write-Host ('  → fallback: ' + $fallback) -ForegroundColor Cyan
        }
    }
    if ($project) {
        if (-not $Silent) { Write-Host ('[gcloud-bootstrap] project: ' + $project) -ForegroundColor Green }
        $env:GOOGLE_CLOUD_PROJECT = $project
        $env:GCLOUD_PROJECT = $project
    }

    # 3. ADC check + inject
    if (Test-GcloudAdcExists) {
        $adcPath = Get-GcloudAdcPath
        $env:GOOGLE_APPLICATION_CREDENTIALS = $adcPath
        if (-not $Silent) { Write-Host ('[gcloud-bootstrap] ADC: ' + $adcPath) -ForegroundColor Green }
    } else {
        Write-Host '[gcloud-bootstrap] ADC 없음 — Python 라이브러리 (BigQuery / Vertex AI 등) 사용 시 1회만:' -ForegroundColor Yellow
        Write-Host '  gcloud auth application-default login' -ForegroundColor Cyan
    }

    return $true
}

# -Auto flag면 즉시 실행
if ($Auto) {
    Invoke-GcloudBootstrap -Silent:$Silent | Out-Null
}
