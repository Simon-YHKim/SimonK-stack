# commit.ps1 -- 허브 커밋 헬퍼 (AI별 기여자 표기)
# 목적: 공유 .git의 author가 전부 "AI Hub"로 뭉개지는 문제 해결.
#       각 AI가 자기 정체성으로 커밋해 git log/blame에 기여가 드러나게 한다.
#
# 사용:
#   powershell tools/commit.ps1 -As codex -m "docs(comm): gate ..." -Files "agents/codex/STATUS.md","agents/codex/outbox/x.md"
#   powershell tools/commit.ps1 -As claude -m "feat(comm): ..."   # -Files 생략 시 이미 stage된 것만 커밋
#
# 규칙(PROTOCOL §10.5): 자기 파일만 명시 stage. `git add -A`/`git add .` 금지.
#   -Files 를 주면 그 경로들만 stage 후 커밋. 안 주면 현재 staged 인덱스 그대로 커밋.

param(
  [Parameter(Mandatory=$true)][ValidateSet("claude","codex","antigravity","grok")][string]$As,
  [Parameter(Mandatory=$true)][string]$Message,
  [string[]]$Files = @(),
  [Alias("SkipGuard")][switch]$Force
)

$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$identities = @{
  claude      = @{ name = "Claude";      email = "claude@2nd-b.ai" }
  codex       = @{ name = "Codex";       email = "codex@2nd-b.ai" }
  antigravity = @{ name = "Antigravity"; email = "antigravity@2nd-b.ai" }
  grok        = @{ name = "Grok";        email = "grok@2nd-b.ai" }
}
$id = $identities[$As]

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

# ----------------------------------------------------------------------------
# BRANCH GUARD (2026-07-03): the hub is a SINGLE-BRANCH repo (master). A spawned
# CLI once ran `git checkout -b codex/...` in this shared tree; every seat's
# commits then landed off-master for a day and HubBackup (which pushes master)
# silently backed up nothing. Refuse to commit anywhere but master. -Force does
# NOT bypass this. Repair: git checkout master; git merge --ff-only <branch>.
# ----------------------------------------------------------------------------
$curBranch = (git rev-parse --abbrev-ref HEAD 2>$null)
if ($curBranch -and $curBranch -ne 'master') {
  Write-Host "[commit] BRANCH GUARD: hub HEAD is on '$curBranch' but must be 'master' (PROTOCOL 5)." -ForegroundColor Red
  Write-Host "  Never create/switch branches in the hub repo (worktrees are for 2nd-B only)." -ForegroundColor Yellow
  Write-Host "  Repair: git checkout master; git merge --ff-only $curBranch; git branch -d $curBranch; then retry." -ForegroundColor Yellow
  exit 1
}

# Concurrent-writer safety: the hub .git index is shared by Claude + the codex/grok/AG
# daemons. Retry git ops that fail on a transient index.lock (commit.ps1 had none, so
# colliding autonomous commits silently failed).
function Invoke-GitRetry {
  param([Parameter(Mandatory=$true)][string[]]$GitArgs, [int]$Retries = 8)
  for ($i = 0; $i -lt $Retries; $i++) {
    $out = & git @GitArgs 2>&1
    if ($LASTEXITCODE -eq 0) { return $true }
    if ("$out" -match 'index\.lock|another git process|Unable to create') {
      Start-Sleep -Milliseconds (400 + $i * 350)
      continue
    }
    Write-Host ("[commit] git failed: " + (("$out" -split "`n")[0])) -ForegroundColor Yellow
    return $false
  }
  Write-Host "[commit] aborted: hub index.lock persisted after $Retries retries (another AI mid-commit?)." -ForegroundColor Yellow
  return $false
}

# Cross-process mutex: genuinely serialize index-touching ops across the codex/grok/AG
# daemon processes + Claude's own loop. Retry handles transient locks; the mutex prevents
# the race itself. Times out to retry-only behavior after 20s rather than block forever.
$hubMutex = New-Object System.Threading.Mutex($false, "Global\hub-git-commit")
try { [void]$hubMutex.WaitOne(20000) } catch [System.Threading.AbandonedMutexException] { }  # prior holder died -> we own it

if ($Files.Count -gt 0) {
  foreach ($f in $Files) {
    if (-not (Invoke-GitRetry @('add','--',$f))) {
      try { $hubMutex.ReleaseMutex() } catch {}
      Write-Host "[commit] abort: failed to stage '$f' (fail closed - partial staging would commit a wrong set)" -ForegroundColor Red
      exit 1
    }
  }
}

# ----------------------------------------------------------------------------
# LANE GUARD (single-writer §1): a non-Claude agent may only commit files under
# its own agents/<As>/ dir. Shared files (BOARD/PROTOCOL/CONTROL/DECISIONS, other
# agents' dirs, tools/, repo root) are Claude-only. Blocks the recurring case of a
# daemon marking shared state directly (e.g. AG editing BOARD.md). Always on.
# ----------------------------------------------------------------------------
if ($As -ne "claude") {
  # --no-renames (2026-07-04): with rename detection ON, a staged `git mv <root-file>
  # agents/<As>/x` lists only the destination path, so moving a Claude-only file into
  # the agent's own lane slipped past the guard while deleting the root file. Force
  # renames to surface as D(old)+A(new) so the off-lane D is caught.
  $stagedAll = git diff --cached --no-renames --name-only --diff-filter=ACMRD
  if ($LASTEXITCODE -ne 0) {
    try { $hubMutex.ReleaseMutex() } catch {}
    Write-Host "[commit] abort: staged-file enumeration failed - lane guard cannot verify (fail closed)" -ForegroundColor Red
    exit 1
  }
  $offlane = @($stagedAll | Where-Object { $_ -and ($_ -notmatch "^agents/$As/") })
  if ($offlane.Count -gt 0) {
    try { $hubMutex.ReleaseMutex() } catch {}
    Write-Host "[commit] LANE GUARD: '$As' may only commit under agents/$As/ (single-writer Sec.1)." -ForegroundColor Red
    foreach ($f in $offlane) { Write-Host "  off-lane: $f" -ForegroundColor Red }
    Write-Host "  Shared files are Claude-only. Unstage them; report status in your own STATUS.md/outbox instead." -ForegroundColor Yellow
    exit 1
  }
}

# ----------------------------------------------------------------------------
# CONVENTIONAL COMMITS (PROTOCOL Sec.5, 2026-07-04): daemon lanes occasionally emit
# non-conforming subjects (e.g. AG "QA: verify ..."). Do not hard-fail an autonomous
# lane over a message prefix - rewrite it to a conforming chore(<seat>) subject instead.
# ----------------------------------------------------------------------------
if ($Message -notmatch '^(feat|fix|chore|docs|test|refactor|style|perf|ci|build|revert|merge)(\(|!|:)') {
  $Message = "chore(" + $As + "): " + $Message
  Write-Host "[commit] message auto-prefixed to Conventional Commits: $Message" -ForegroundColor Yellow
}

# ----------------------------------------------------------------------------
# PRE-COMMIT GUARD (recurrence prevention for incidents #2 and #3)
#   #2  cp949 / U+FFFD corruption -- a file saved via Out-File default cp949
#       (or otherwise mojibaked) silently lands in git and breaks all readers.
#   #3  unbounded STATUS bloat   -- agents/*/STATUS.md grows without bound and
#       eventually wrecks the hub (must stay small; rotate to a gitignored log).
# Default ON. Bypass for legitimately large/binary-ish files with -Force.
# ----------------------------------------------------------------------------
$SizeLimitBytes = 256 * 1024   # 256 KB threshold for committed .md files
$StatusLimitBytes = 64 * 1024  # O-15 #2: tighter cap for STATUS.md (rotate old detail to a gitignored *.log)
$TextExtForEnc  = @(".md", ".json", ".ps1", ".sh")
# SECRET GUARD (2026-07-03, BACKLOG last guard piece): block staged text that looks like a
# real credential. PROTOCOL 7: secrets go by path/reference only, never inline. Patterns are
# deliberately tight (length-bounded) to avoid flagging placeholders like sk-xxx.
$SecretExt = @(".md", ".json", ".ps1", ".sh", ".txt", ".yml", ".yaml", ".js", ".ts", ".html")
$SecretPatterns = [ordered]@{
  'openai/anthropic-style key' = 'sk-[A-Za-z0-9_-]{20,}'
  'aws access key'             = 'AKIA[0-9A-Z]{16}'
  'github token'               = '(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,}'
  'slack token'                = 'xox[baprs]-[A-Za-z0-9-]{10,}'
  'private key block'          = '-----BEGIN [A-Z ]*PRIVATE KEY-----'
  'google api key'             = 'AIza[0-9A-Za-z_-]{35}'
  'jwt (3-part)'               = 'eyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}'
}

function Get-StagedFiles {
  # Files actually about to be committed = current staged index.
  $out = git diff --cached --name-only --diff-filter=ACMR
  if (-not $out) { return @() }
  return @($out | Where-Object { $_ -and $_.Trim() -ne "" })
}

function Test-FileEncoding([string]$path) {
  # Returns the offending reason string, or $null if clean.
  # (a) explicit U+FFFD replacement-char byte sequence EF BF BD
  # (b) strict UTF-8 decode failure (throws on invalid bytes)
  $bytes = [System.IO.File]::ReadAllBytes($path)
  for ($i = 0; $i -le $bytes.Length - 3; $i++) {
    if ($bytes[$i] -eq 0xEF -and $bytes[$i+1] -eq 0xBF -and $bytes[$i+2] -eq 0xBD) {
      return "U+FFFD replacement char (EF BF BD) at byte offset $i"
    }
  }
  try {
    $strict = [System.Text.UTF8Encoding]::new($false, $true)  # throwOnInvalidBytes = true
    [void]$strict.GetString($bytes)
  } catch {
    return "not valid UTF-8 (strict decode failed: $($_.Exception.Message))"
  }
  return $null
}

if (-not $Force) {
  $staged = Get-StagedFiles
  if ($LASTEXITCODE -ne 0) {
    try { $hubMutex.ReleaseMutex() } catch {}
    Write-Host "[commit] abort: staged-file enumeration failed - encoding/size guard cannot verify (fail closed)" -ForegroundColor Red
    exit 1
  }
  if ($staged.Count -gt 0) {
    $problems = @()
    foreach ($rel in $staged) {
      $abs = Join-Path $root $rel
      if (-not (Test-Path -LiteralPath $abs)) { continue }  # deletes etc.
      $ext = [System.IO.Path]::GetExtension($rel).ToLowerInvariant()

      # (a) ENCODING guard for text-ish files
      if ($TextExtForEnc -contains $ext) {
        $reason = Test-FileEncoding $abs
        if ($reason) {
          $problems += "  [ENC]  ${rel}: $reason"
        }
      }

      # (b) SIZE guard for committed .md files -- STATUS.md capped tighter (O-15 #2)
      if ($ext -eq ".md") {
        $len = (Get-Item -LiteralPath $abs).Length
        $isStatus = [System.IO.Path]::GetFileName($rel) -ieq "STATUS.md"
        $cap = if ($isStatus) { $StatusLimitBytes } else { $SizeLimitBytes }
        if ($len -gt $cap) {
          $kb = [math]::Round($len / 1KB, 1)
          $extra = if ($isStatus) { " (STATUS cap -- rotate old detail to a gitignored *.log)" } else { "" }
          $problems += "  [SIZE] ${rel}: ${kb} KB exceeds $([int]($cap/1KB)) KB$extra"
        }
      }

      # (c) SECRET guard for text files (PROTOCOL 7: no plaintext credentials in the hub)
      if ($SecretExt -contains $ext) {
        try {
          $txt = [System.IO.File]::ReadAllText($abs)
          foreach ($sp in $SecretPatterns.GetEnumerator()) {
            if ($txt -match $sp.Value) {
              $problems += "  [SECRET] ${rel}: matches '$($sp.Key)' pattern"
              break
            }
          }
        } catch {}
      }
    }

    if ($problems.Count -gt 0) {
      Write-Host ""
      Write-Host "[commit] PRE-COMMIT GUARD 차단 -- 커밋을 중단합니다." -ForegroundColor Red
      foreach ($p in $problems) { Write-Host $p -ForegroundColor Red }
      Write-Host ""
      Write-Host "조치:" -ForegroundColor Yellow
      Write-Host "  [ENC]  cp949/Out-File 손상 가능성. 해당 파일을 Edit/Write로 UTF-8(no BOM) 재저장하세요." -ForegroundColor Yellow
      Write-Host "  [SIZE] STATUS.md 등은 작게 유지. 내용을 잘라내거나 .gitignore된 *.log 로 회전하세요." -ForegroundColor Yellow
      Write-Host "  [SECRET] real key/token = NEVER commit. Remove it and reference by path (PROTOCOL 7); rotate the key if exposed. Use -Force ONLY for a confirmed false positive." -ForegroundColor Yellow
      Write-Host "  정당한 대용량/예외 파일이면 -Force (별칭 -SkipGuard) 로 가드를 건너뛸 수 있습니다." -ForegroundColor Yellow
      exit 1
    }
  }
} else {
  Write-Host "[commit] PRE-COMMIT GUARD 건너뜀 (-Force)." -ForegroundColor DarkYellow
}

# author + committer 둘 다 해당 AI로 박는다 (git log/blame/contributors에 드러남)
$ok = Invoke-GitRetry @('-c', "user.name=$($id.name)", '-c', "user.email=$($id.email)", 'commit', '-m', $Message)
try { $hubMutex.ReleaseMutex() } catch {}
if ($ok) {
  Write-Host "[commit] committed as ${As}: $Message" -ForegroundColor Green
} else {
  Write-Host "[commit] failed. Check staged files, conflicts, and git status." -ForegroundColor Yellow
  exit 1
}
