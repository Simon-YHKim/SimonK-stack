<#
.SYNOPSIS
  미머지 원격 브랜치 적체(branch sprawl)를 분류·드레인하는 엔진.
  병렬 triage의 "결정적(deterministic) 1단계" — 낡고 대체된 브랜치를 자동 폐기하고,
  살아있는 소수(behind 적거나 ahead 큰 것)는 REVIEW로 남겨 Claude/머지 큐로 넘긴다.

.DESCRIPTION
  순수 ref 기반(fetch + rev-list + push --delete)으로만 동작 — checkout/working-tree 변경 없음.
  따라서 dirty/behind 상태의 공유 클론에서도 안전하게 돌릴 수 있다.
  삭제(-Execute) 전에 **항상** 복구 원장 CSV + 복원 스크립트를 먼저 쓴다.

  분류 규칙:
    DROP   = (behind > BehindThreshold AND ahead < AheadKeep)  또는  이름이 *-backup-* / *-backup
    REVIEW = 그 외 전부 (behind 작음 = 최신, 또는 ahead 큼 = 작업량 많음 → 함부로 안 버림)
  REVIEW 집합은 Claude의 framework-aware 최종 패스 + 직렬 머지 큐로 넘긴다 (이 스크립트는 안 지움).

.PARAMETER Execute
  실제 origin 브랜치 삭제 수행. 미지정 시 DRY-RUN(분류·원장만 출력).

.PARAMETER BehindThreshold
  이 값보다 많이 뒤처진(behind) 브랜치는 폐기 후보. 기본 150.

.PARAMETER AheadKeep
  ahead가 이 값 이상이면 작업량이 커서 behind 무관하게 REVIEW로 보존. 기본 8.

.EXAMPLE
  pwsh drain-branches.ps1                 # DRY: 분류표 + 원장만
  pwsh drain-branches.ps1 -Execute        # 폐기 실행 (원장 먼저 기록)
#>
[CmdletBinding()]
param(
  [switch]$Execute,
  [int]$BehindThreshold = 150,
  [int]$AheadKeep = 8,
  [string]$Repo = "E:\2ndB",
  [string]$LedgerDir = "E:\Coding Infra\AI Infra\Communication\Output"
)

$ErrorActionPreference = "Stop"
Set-Location $Repo

# 0) 보호 브랜치 — 절대 건드리지 않음
$Protected = @('main','master','gh-pages','HEAD')

Write-Host "== fetch --all --prune ==" -ForegroundColor Cyan
git fetch --all --prune --quiet

# 1) 미머지 원격 브랜치 열거
$raw = git for-each-ref refs/remotes/origin --format='%(refname:short)' --no-merged origin/main
$branches = $raw | Where-Object {
  $name = ($_ -replace '^origin/','')
  $name -and ($Protected -notcontains $name)
}

$rows = foreach ($ref in $branches) {
  $name   = $ref -replace '^origin/',''
  $sha    = (git rev-parse $ref).Trim()
  $ahead  = [int](git rev-list --count "origin/main..$ref")
  $behind = [int](git rev-list --count "$ref..origin/main")
  $date   = (git log -1 --format='%cs' $ref).Trim()
  $author = (git log -1 --format='%an' $ref).Trim()

  # cherry: 이 브랜치의 커밋들이 patch-id 기준으로 이미 main에 있는지. '+' = 미머지, '-' = 이미 머지됨.
  $cherry = git cherry origin/main $ref 2>$null
  $notInMain = @($cherry | Where-Object { $_ -match '^\+' }).Count
  $allMerged = ($ahead -gt 0) -and ($notInMain -eq 0)   # 모든 패치가 이미 main에 → stale ref

  $isBackup = $name -match '-backup(-|$)'
  $drop = $allMerged -or $isBackup -or (($behind -gt $BehindThreshold) -and ($ahead -lt $AheadKeep))
  $reason = if ($allMerged) { "already-in-main: all $ahead patch(es) merged by patch-id (stale ref)" }
            elseif ($isBackup) { "backup-branch" }
            elseif ($drop) { "stale: ${behind} behind > $BehindThreshold, only $ahead ahead" }
            else { "live: $behind behind / $ahead ahead, $notInMain not-in-main -> review" }

  [pscustomobject]@{
    Class   = if ($drop) { 'DROP' } else { 'REVIEW' }
    Name    = $name
    Ahead   = $ahead
    Behind  = $behind
    Date    = $date
    Author  = $author
    Sha     = $sha
    Reason  = $reason
  }
}

$drop   = @($rows | Where-Object Class -eq 'DROP'   | Sort-Object Behind -Descending)
$review = @($rows | Where-Object Class -eq 'REVIEW' | Sort-Object Behind)

# 2) 원장 + 복원 스크립트 (삭제 여부와 무관하게 항상 기록)
if (-not (Test-Path $LedgerDir)) { New-Item -ItemType Directory -Path $LedgerDir -Force | Out-Null }
$stamp     = (Get-Date -Format 'yyyyMMdd-HHmmss')
$ledgerCsv = Join-Path $LedgerDir "branch-drain-ledger-$stamp.csv"
$restorePs = Join-Path $LedgerDir "branch-drain-restore-$stamp.ps1"

$rows | Sort-Object Class, Behind -Descending | Export-Csv -Path $ledgerCsv -NoTypeInformation -Encoding UTF8

$restoreLines = @(
  "# 복원 스크립트 — $stamp 드레인으로 삭제된 브랜치를 origin에 되살린다 (SHA가 GC 전이어야 함).",
  "# 사용: pwsh `"$restorePs`"",
  "Set-Location `"$Repo`""
)
foreach ($d in $drop) {
  $restoreLines += "git push origin $($d.Sha):refs/heads/$($d.Name)   # was $($d.Behind) behind / $($d.Ahead) ahead, $($d.Date)"
}
$restoreLines | Set-Content -Path $restorePs -Encoding UTF8

# 3) 출력
Write-Host ""
Write-Host "== 분류 결과 ==" -ForegroundColor Cyan
Write-Host ("  DROP  : {0}" -f $drop.Count)   -ForegroundColor Yellow
Write-Host ("  REVIEW: {0}" -f $review.Count) -ForegroundColor Green
Write-Host ("  원장  : $ledgerCsv")
Write-Host ("  복원  : $restorePs")
Write-Host ""
Write-Host "== REVIEW (살아있음 — Claude 머지 큐로) ==" -ForegroundColor Green
$review | Format-Table Name, Ahead, Behind, Date, Author -AutoSize | Out-String | Write-Host

if ($Execute) {
  Write-Host "== 폐기 실행 (origin --delete) ==" -ForegroundColor Red
  $ok = 0; $fail = 0; $skip = 0
  foreach ($d in $drop) {
    # 2차 가드(방어 심층): 분류 단계에서 빠졌더라도 보호 브랜치는 절대 삭제 금지.
    # gh-pages(라이브 사이트)/main 등이 enumeration 필터를 우회해도 여기서 차단.
    if ($Protected -contains $d.Name) {
      $skip++; Write-Host "  ! SKIP protected $($d.Name)" -ForegroundColor Yellow; continue
    }
    try {
      $res = git push origin --delete $d.Name 2>&1
      if ($LASTEXITCODE -eq 0) { $ok++; Write-Host "  - deleted $($d.Name)" }
      else {
        $fail++; Write-Host "  ! FAILED  $($d.Name): $res" -ForegroundColor Red
        "FAILED $($d.Name): $res" | Add-Content $ledgerCsv.Replace('.csv','-failures.log')
      }
    } catch { $fail++; Write-Host "  ! ERROR   $($d.Name): $_" -ForegroundColor Red }
  }
  Write-Host ("== 완료: deleted=$ok failed=$fail skipped=$skip. 복원은 $restorePs ==") -ForegroundColor Cyan
} else {
  Write-Host "== DRY-RUN: 삭제 안 함. 실제 폐기는 -Execute. 아래 DROP 후보 ==" -ForegroundColor Yellow
  $drop | Format-Table Name, Ahead, Behind, Date, Reason -AutoSize | Out-String | Write-Host
}

# 머지 큐가 소비할 수 있게 REVIEW 목록을 JSON으로도 남김
$reviewJson = Join-Path $LedgerDir "branch-review-queue-$stamp.json"
$review | ConvertTo-Json -Depth 4 | Set-Content -Path $reviewJson -Encoding UTF8
Write-Host "REVIEW 큐: $reviewJson"
