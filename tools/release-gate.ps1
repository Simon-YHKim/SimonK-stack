# release-gate.ps1 -- independent pre-merge release-readiness gate (PROTOCOL §8/§11.1, BACKLOG #3)
#
# Purpose: break the closed self-certifying loop where Claude authors -> verifies -> decides
#   -> is the only online-git actor, with NO author-independent GO/NO-GO. Prevents the
#   #222-class accident (verify FAIL but merged anyway -> main broken -> #223 recovery).
#
# Invariant preserved: online-git stays Claude-only (PROTOCOL §11). This gate does NOT push.
#   It returns a binding GO/NO-GO verdict AND records the current origin/main SHA as an explicit
#   rollback target BEFORE any merge, so a bad merge has a one-command revert path.
#
# Checks (all must pass for GO):
#   1. repo exists and is a git work tree
#   2. working tree is clean (no uncommitted churn that would make the verify meaningless)
#   3. `npm run verify` exits 0 (real gate, run against the committed HEAD)
#   4. records rollback SHA (current origin/main) and the HEAD being gated
#
# Usage:
#   powershell tools/release-gate.ps1                 # gate the default 2nd-B repo, human output
#   powershell tools/release-gate.ps1 -Json           # machine-readable verdict
#   powershell tools/release-gate.ps1 -Repo "E:\2ndB" -VerifyCmd "npm run verify"
#   powershell tools/release-gate.ps1 -SkipVerify     # SHA/clean checks only (fast pre-flight)
#
# Exit code: 0 = GO, 1 = NO-GO. Log: tools/release-gate.log (append-only, gitignored).

param(
  [string]$Repo = "E:\2ndB",
  [string]$VerifyCmd = "npm run verify",
  [switch]$SkipVerify,
  [switch]$Json
)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$logPath = Join-Path $PSScriptRoot "release-gate.log"
$now = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

$result = [ordered]@{
  ts          = $now
  repo        = $Repo
  verdict     = "NO-GO"
  reasons     = @()
  head        = $null
  rollback    = $null   # origin/main SHA to revert to if this merge goes bad
  clean       = $false
  verify      = "skipped"
}

function Fail([string]$why) {
  $result.reasons += $why
}

if (-not (Test-Path -LiteralPath $Repo)) {
  Fail "repo path not found: $Repo"
} else {
  Push-Location $Repo
  try {
    $inside = (& git rev-parse --is-inside-work-tree 2>$null)
    if ($LASTEXITCODE -ne 0 -or "$inside".Trim() -ne "true") {
      Fail "not a git work tree: $Repo"
    } else {
      $result.head = (& git rev-parse --short HEAD 2>$null | Out-String).Trim()

      # rollback target = current origin/main (the thing a bad merge would clobber)
      $rb = (& git rev-parse --short origin/main 2>$null | Out-String).Trim()
      if (-not $rb) { $rb = (& git rev-parse --short main 2>$null | Out-String).Trim() }
      $result.rollback = $rb
      if (-not $rb) { Fail "could not resolve rollback SHA (origin/main and main both missing)" }

      # working tree must be clean -- a dirty tree makes the verify lie about HEAD
      $porcelain = (& git status --porcelain 2>$null | Out-String).Trim()
      if ($porcelain) {
        Fail "working tree not clean (uncommitted changes -> verify would not reflect the merge target)"
        $result.clean = $false
      } else {
        $result.clean = $true
      }

      if (-not $SkipVerify) {
        Write-Host "[release-gate] running: $VerifyCmd  (in $Repo)" -ForegroundColor Cyan
        & cmd /c $VerifyCmd
        $code = $LASTEXITCODE
        if ($code -eq 0) {
          $result.verify = "pass"
        } else {
          $result.verify = "fail(exit $code)"
          Fail "verify failed (exit $code)"
        }
      }
    }
  } finally {
    Pop-Location
  }
}

if ($result.reasons.Count -eq 0) { $result.verdict = "GO" }

# append-only log line
$line = "[$now] $($result.verdict) repo=$Repo head=$($result.head) rollback=$($result.rollback) clean=$($result.clean) verify=$($result.verify)"
if ($result.reasons.Count -gt 0) { $line += " reasons=" + ($result.reasons -join "; ") }
Add-Content -LiteralPath $logPath -Value $line -Encoding utf8

if ($Json) {
  $result.reasons = @($result.reasons)
  $result | ConvertTo-Json -Compress
} else {
  $color = if ($result.verdict -eq "GO") { "Green" } else { "Red" }
  Write-Host ""
  Write-Host "[release-gate] $($result.verdict)" -ForegroundColor $color
  Write-Host "  HEAD gated : $($result.head)"
  Write-Host "  rollback to: $($result.rollback)   (git reset --hard $($result.rollback) on bad merge)"
  Write-Host "  tree clean : $($result.clean)"
  Write-Host "  verify     : $($result.verify)"
  if ($result.reasons.Count -gt 0) {
    Write-Host "  NO-GO reasons:" -ForegroundColor Yellow
    foreach ($r in $result.reasons) { Write-Host "    - $r" -ForegroundColor Yellow }
  }
}

if ($result.verdict -eq "GO") { exit 0 } else { exit 1 }
