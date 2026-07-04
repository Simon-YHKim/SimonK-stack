<#
.SYNOPSIS
  자동 트리거 래퍼 — 스케줄 작업 HubBranchDrain이 호출.
  미머지 브랜치 적체를 주기적으로 드레인(이미-머지/stale/backup 자동 폐기)하고,
  살아있는 REVIEW 잔여분을 사람이 읽을 요약으로 남긴다.
  CONTROL.md state가 running이 아닐 때(paused/draining)는 폐기를 건너뛴다(분류만).
#>
[CmdletBinding()]
param(
  [string]$Hub = "E:\Coding Infra\AI Infra\Communication"
)
$ErrorActionPreference = "Continue"
$ts = (Get-Date -Format 'yyyy-MM-dd / HH:mm:ss')
$log = Join-Path $Hub "tools\drain-cron.log"
$drain = Join-Path $Hub "tools\drain-branches.ps1"

# CONTROL 세마포어 존중: running일 때만 실제 폐기
$state = "unknown"
$ctl = Join-Path $Hub "CONTROL.md"
if (Test-Path $ctl) {
  $m = Select-String -Path $ctl -Pattern '^state:\s*(\w+)' | Select-Object -First 1
  if ($m) { $state = $m.Matches[0].Groups[1].Value }
}

$mode = if ($state -eq 'running') { '-Execute' } else { '' }
"[$ts KST] HubBranchDrain start (CONTROL state=$state, mode=$mode)" | Add-Content $log

$argList = @('-NoProfile','-File', $drain)
if ($mode) { $argList += $mode }
# 진짜 pwsh를 먼저 찾는다 — 현재 호스트 전파 방식은 PS5.1(powershell.exe)로 호출되면
# 한글 리터럴이 많은 드레인 엔진을 cp949로 파싱해 조용히 깨뜨렸다(2026-07-03 감사).
$pwshExe = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $pwshExe) { $pwshExe = (Get-Process -Id $PID).Path }
if (-not $pwshExe -or -not (Test-Path $pwshExe)) { $pwshExe = Join-Path $PSHOME 'pwsh.exe' }
if (-not (Test-Path $pwshExe)) { $pwshExe = 'pwsh' }
$out = & $pwshExe @argList 2>&1 | Out-String
$out | Add-Content $log

# 사람이 읽을 최신 요약 (open-reports가 픽업) — 실패/스킵도 표면화
$summaryLines = $out -split "`n" | Where-Object { $_ -match 'deleted|FAILED|SKIP|DROP  :|REVIEW:|완료:' }
$md  = @()
$md += "# Branch Drain — 최신 실행 ($ts KST)"
$md += ''
$md += "CONTROL state: **$state** (running일 때만 폐기)"
$md += ''
$md += '```'
$md += $summaryLines
$md += '```'
$md += ''
$md += '전체 로그: `tools/drain-cron.log` · 원장/복원: `Output/branch-drain-*`'
$md -join "`n" | Set-Content (Join-Path $Hub "Output\branch-drain-latest.md") -Encoding UTF8

"[$ts KST] HubBranchDrain done" | Add-Content $log
