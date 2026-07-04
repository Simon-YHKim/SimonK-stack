<#
.SYNOPSIS
  허브 off-machine 백업 — 커밋된 히스토리를 private 원격(comm-hub)에 푸시.
  감사(ai-hub-audit) P1 'remote/백업 없는 단일디스크 SPOF' 대응. 예약작업 HubBackup이 호출.
.NOTES
  커밋된 히스토리만 백업한다(워킹트리 미커밋분은 각 에이전트가 커밋해야 잡힘).
  원격이 SPOF 1차 방어선. 파괴적 op 없음(push만).
#>
[CmdletBinding()]
param([string]$Hub = "E:\Coding Infra\AI Infra\Communication")
$ErrorActionPreference = "Continue"
$ts = (Get-Date -Format 'yyyy-MM-dd / HH:mm:ss')
$log = Join-Path $Hub "tools\hub-backup.log"
Set-Location $Hub

# 원격이 없으면(클론 이동 등) 기록만 하고 종료
$hasRemote = (git remote 2>$null) -contains 'origin'
if (-not $hasRemote) {
  "[$ts KST] HubBackup SKIP: origin 원격 미설정 (git remote add origin <private-url> 필요)" | Add-Content $log
  return
}

$push = (git push origin master 2>&1 | Out-String).Trim()
$localHead  = (git rev-parse --short HEAD 2>$null)
$remoteHead = ((git ls-remote origin master 2>$null) -split '\s')[0]
$synced = $remoteHead -and ($remoteHead -like "$((git rev-parse HEAD))*")
"[$ts KST] HubBackup push (local=$localHead, synced=$synced): $push" | Add-Content $log
