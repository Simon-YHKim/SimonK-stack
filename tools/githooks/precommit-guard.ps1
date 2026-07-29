# precommit-guard.ps1 -- git-LAYER secret/encoding scan (audit C1 defense-in-depth).
# ASCII-only. commit.ps1's scan is WRAPPER-only: a plain `git commit` (a human, or a CLI that
# shells git directly) bypasses it. This runs at the git pre-commit hook so the scan fires on
# EVERY commit path. It is SUPPLEMENTARY: commit.ps1 stays the fail-CLOSED primary.
#
# CONTRACT (critical): exits 7 ONLY on a CONFIRMED staged secret/encoding violation. Exits 0 for
# everything else INCLUDING its own errors (fail-OPEN). The hook blocks only on exit 7, so a bug
# here can never halt the hub's autonomous commit stream -- worst case it stops catching.
try {
  $root = (git rev-parse --show-toplevel 2>$null)
  if (-not $root) { exit 0 }
  $staged = @(git diff --cached --name-only --diff-filter=ACM 2>$null | Where-Object { $_ })
  if ($staged.Count -eq 0) { exit 0 }
  # tight, length-bounded patterns (mirror commit.ps1) so placeholders like sk-xxx do not trip.
  $secretPatterns = @(
    'sk-[A-Za-z0-9_-]{20,}',
    'AKIA[0-9A-Z]{16}',
    '(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}',
    'github_pat_[A-Za-z0-9_]{22,}',
    'xox[baprs]-[A-Za-z0-9-]{10,}',
    '-----BEGIN [A-Z ]*PRIVATE KEY-----',
    'AIza[0-9A-Za-z_-]{35}',
    'eyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}'
  )
  $textExt = @('.md', '.json', '.ps1', '.sh', '.txt', '.yml', '.yaml', '.js', '.ts', '.html', '.env')
  $bad = @()
  foreach ($rel in $staged) {
    $abs = Join-Path $root $rel
    if (-not (Test-Path -LiteralPath $abs)) { continue }
    $ext = [System.IO.Path]::GetExtension($rel).ToLowerInvariant()
    if ($textExt -notcontains $ext) { continue }
    $txt = [System.IO.File]::ReadAllText($abs)
    foreach ($p in $secretPatterns) { if ($txt -match $p) { $bad += "[SECRET] ${rel}: matches a credential pattern"; break } }
    if ($txt.IndexOf([char]0xFFFD) -ge 0) { $bad += "[ENC] ${rel}: U+FFFD replacement char (cp949/mojibake corruption)" }
  }
  if ($bad.Count -gt 0) {
    Write-Host ""
    foreach ($b in $bad) { Write-Host "[pre-commit] $b" -ForegroundColor Red }
    exit 7
  }
  exit 0
} catch { exit 0 }
