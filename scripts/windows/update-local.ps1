# One command from GitHub main to an installed, verified SimonK-stack user home on Windows.
# Default: preview. It writes nothing except `git fetch` refreshing remote-tracking refs.
# -Apply: build (or reuse) the candidate for main, swap the eight /vibe junctions and the
# Codex config line, replace physical skill copies whose bytes differ from main, verify
# (selftests, config, versions) and roll everything back if verification fails.
# Prints one JSON report. Exit 0 = preview/current/installed, 2 = blocked or rolled back,
# 3 = rollback incomplete (inspect the archive paths in the report).
# Use PowerShell 7: pwsh -NoProfile -NonInteractive -File scripts/windows/update-local.ps1 [-Apply]
[CmdletBinding(PositionalBinding = $false)]
param(
    [string] $RepoRoot,
    [string] $Ref = 'origin/main',
    [string] $ReleasesDir,
    [string] $UserHome,
    [string] $CodexHome,
    [string] $PluginPins,
    [string] $Tag,
    [string[]] $PhysicalSkills = @('ai-debate', 'careful', 'freeze', 'guard', 'unfreeze'),
    [double] $MinFreeMemoryGB = 3,
    [switch] $NoFetch,
    [switch] $Selftest,
    [switch] $Apply
)
$ErrorActionPreference = 'Stop'
$stage = 'start'
$exitCode = 2
$lock = $null
$report = [ordered]@{ status = 'blocked'; mode = $(if ($Apply) { 'apply' } else { 'preview' }); kst = $null }
# Skills whose candidate copies the eight junctions expose.
$linkedSkills = @('vibe', 'vibe-bot', 'model-router', 'simonk', 'multi-terminal-dispatcher', 'qa')

function Get-UpdateVerification([string] $Repo, [string] $Commit, [string] $UserHomeDir, [string] $CodexDir,
                                [string[]] $Physical, [bool] $RunSelftest) {
    $now = Get-SkInstalledCandidate $UserHomeDir
    $problems = [Collections.Generic.List[string]]::new()
    $v = [ordered]@{ ok = $false; installed_tag = $now.tag; codex_config = 'no-codex'; versions = [ordered]@{}
        physical = [ordered]@{}; selftest = 'skipped'; problems = @() }
    if ($now.state -ne 'junction') { $problems.Add("vibe link is $($now.state)") }
    $codexPresent = Test-Path -LiteralPath $CodexDir -PathType Container
    if ($codexPresent) {
        $cfg = Get-SkCodexConfigState $CodexDir $now.target
        $v.codex_config = $cfg
        if (-not $cfg.matches_junction) { $problems.Add('codex /vibe config line does not match the Claude vibe junction') }
    }
    foreach ($spec in Get-SkJunctionSpecs $UserHomeDir $CodexDir) {
        if ($spec.Side -eq 'codex' -and -not $codexPresent) { continue }
        $main = Get-SkGitSkillVersion $Repo $Commit $spec.Skill
        $inst = Get-SkFileSkillVersion $spec.Path
        $v.versions[$spec.Name] = "$inst (main $main)"
        if ($inst -ne $main) { $problems.Add("$($spec.Name) version $inst, main $main") }
    }
    foreach ($name in $Physical) {
        $c = Compare-SkSkillTree $Repo $Commit $name (Join-Path $UserHomeDir ".claude\skills\$name")
        $v.physical[$name] = "$($c.state) $(Get-SkFileSkillVersion $c.path)".Trim()
        if ($c.state -notin @('same', 'not-in-main', 'no-install')) { $problems.Add("physical $name is $($c.state)") }
    }
    if ($RunSelftest) {
        $vibeTest = Invoke-SkSelftest (Join-Path $UserHomeDir '.claude\skills\vibe\scripts\selftest.py')
        $botTest = Invoke-SkSelftest (Join-Path $UserHomeDir '.claude\skills\vibe-bot\scripts\selftest.py')
        $v.selftest = [ordered]@{ vibe = "$($vibeTest.pass)/$($vibeTest.fail) rc=$($vibeTest.rc)"
            vibe_bot = "$($botTest.pass)/$($botTest.fail) rc=$($botTest.rc)" }
        if (-not $vibeTest.ok) { $problems.Add('vibe selftest failed') }
        if (-not $botTest.ok) { $problems.Add('vibe-bot selftest failed') }
    }
    $v.problems = @($problems)
    $v.ok = ($problems.Count -eq 0)
    $v
}

try {
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'POWERSHELL_7_REQUIRED: run with pwsh -NoProfile -File' }
    Import-Module (Join-Path $PSScriptRoot 'SimonKLocalInstall.psm1') -Force
    $report.kst = (Get-SkKstNow).ToString('yyyy-MM-dd HH:mm:ss')
    $stage = 'discover'
    $repo = Resolve-SkRepoRoot $RepoRoot
    $userHomeDir = Resolve-SkUserHome $UserHome
    $codexDir = if ($CodexHome) { [IO.Path]::GetFullPath($CodexHome).TrimEnd('\') } else { Join-Path $userHomeDir '.codex' }
    $codexPresent = Test-Path -LiteralPath $codexDir -PathType Container
    $physical = @($PhysicalSkills | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($Apply) { $lock = Enter-SkInstallLock }

    # 1. Resolve main.
    $stage = 'fetch'
    if (-not $NoFetch) { $null = Invoke-SkGit $repo @('fetch', '-q', 'origin') }
    $sha = Resolve-SkCommit $repo $Ref
    $report.main = [ordered]@{ ref = $Ref; sha = $sha; vibe = (Get-SkGitSkillVersion $repo $sha 'vibe')
        vibe_bot = (Get-SkGitSkillVersion $repo $sha 'vibe-bot') }
    $report.repo = $repo

    # 2. Installed candidate from the ~/.claude/skills/vibe junction.
    $stage = 'installed'
    $installed = Get-SkInstalledCandidate $userHomeDir
    $releases = Resolve-SkReleasesDir $ReleasesDir $installed
    $report.installed = [ordered]@{ state = $installed.state; tag = $installed.tag; main = $installed.main
        releases_dir = $releases }

    # 3. Is it current? Same commit, or no candidate input changed, or only skills that
    #    no junction exposes changed while the linked bytes already equal main.
    $stage = 'decide'
    $linked = @(foreach ($spec in Get-SkJunctionSpecs $userHomeDir $codexDir) {
        if ($spec.Side -eq 'codex' -and -not $codexPresent) { continue }
        (Compare-SkSkillTree $repo $sha $spec.Skill $spec.Path).state
    })
    $linkedSame = @($linked | Where-Object { $_ -eq 'same' }).Count
    $junction = [ordered]@{ action = 'none'; reason = ''; linked_bytes_equal_main = "$linkedSame/$($linked.Count)"
        changed_inputs = 0; changed_input_sample = @() }
    if ($installed.state -eq 'junction') {
        if ($installed.main -eq $sha) {
            $junction.reason = 'same_commit'
        } elseif (-not $installed.main) {
            $junction.action = 'update'; $junction.reason = 'installed_receipts_missing'
        } else {
            $changes = Get-SkCandidateInputChanges $repo $installed.main $sha
            if ($null -eq $changes) {
                $junction.action = 'update'; $junction.reason = 'installed_commit_unknown'
            } else {
                $junction.changed_inputs = $changes.Count
                $junction.changed_input_sample = @($changes | Select-Object -First 10)
                $touching = @($changes | Where-Object {
                    -not ($_ -match '^skills-src/([^/]+)/' -and $Matches[1] -notin $linkedSkills) })
                if ($changes.Count -eq 0) {
                    $junction.reason = 'candidate_inputs_unchanged'
                } elseif ($touching.Count -eq 0 -and $linkedSame -eq $linked.Count) {
                    $junction.reason = 'linked_skills_unchanged'
                } else {
                    $junction.action = 'update'; $junction.reason = 'candidate_inputs_changed'
                }
            }
        }
    } elseif ($installed.state -in @('absent', 'directory')) {
        $junction.action = 'first-install'; $junction.reason = "vibe is $($installed.state)"
    } else {
        throw "TOPOLOGY_CHANGED: ~/.claude/skills/vibe is $($installed.state) $($installed.target)"
    }
    $report.junctions = $junction

    $archiveTag = (Get-SkKstNow).ToString('yyMMdd-HHmm') + '-' + $sha.Substring(0, 7)
    $physPlan = Invoke-SkPhysicalSync -RepoRoot $repo -Commit $sha -Skills $physical -UserHome $userHomeDir -ArchiveTag $archiveTag
    $physChanges = @($physPlan.skills | Where-Object { $_.action -ne 'none' })
    $report.physical = @($physPlan.skills | ForEach-Object {
        [ordered]@{ skill = $_.skill; state = $_.state; action = $_.action; installed = $_.version_installed; main = $_.version_main } })
    $report.run_guard = Test-SkVibeRunGuard $userHomeDir
    $report.agy = Get-SkAgyLinks $userHomeDir

    # Candidate plan when the junctions must move.
    $candidate = [ordered]@{ action = 'none'; tag = $installed.tag }
    $reuse = $null
    if ($junction.action -ne 'none') {
        $reuse = Find-SkCandidateForCommit $releases $sha
        if ($reuse) {
            $candidate = [ordered]@{ action = 'reuse'; tag = $reuse.tag }
        } else {
            $newTag = if ($Tag) { $Tag } else { New-SkCandidateTag $repo $sha }
            $candidate = [ordered]@{ action = 'build'; tag = $newTag
                memory = [ordered]@{ free_gb = (Get-SkFreeMemoryGB); min_gb = $MinFreeMemoryGB }; plugin_pins = $null }
            if (-not $Apply) {
                try {
                    $inputsJson = (Invoke-SkGit $repo @('show', "${sha}:distribution/plugin-inputs.v1.json")).Out -join "`n"
                    $candidate.plugin_pins = (Find-SkPluginPins $PluginPins $releases $inputsJson).path
                } catch { $candidate.plugin_pins = "blocked: $($_.Exception.Message)" }
            }
        }
    }
    $report.candidate = $candidate

    $nothing = ($junction.action -eq 'none' -and $physChanges.Count -eq 0)
    if ($nothing -or -not $Apply) {
        $stage = 'check'
        $report.verify = Get-UpdateVerification $repo $sha $userHomeDir $codexDir $physical ([bool] $Selftest)
        if ($nothing) {
            $report.status = 'current'
            $report.message = "already current: installed $($installed.tag) matches main $($sha.Substring(0, 7)) ($($junction.reason))"
            $exitCode = if ($report.verify.ok) { 0 } else { 2 }
        } else {
            $would = [Collections.Generic.List[string]]::new()
            if ($candidate.action -eq 'reuse') { $would.Add("reuse candidate $($candidate.tag) (re-verify 4 receipts)") }
            if ($candidate.action -eq 'build') {
                $would.Add("build candidate $($candidate.tag) from $($sha.Substring(0, 7))")
                $free = $candidate.memory.free_gb
                if ($MinFreeMemoryGB -gt 0 -and ($null -eq $free -or $free -lt $MinFreeMemoryGB)) {
                    $would.Add("BLOCKED now: LOW_MEMORY ($free GB free, need $MinFreeMemoryGB GB)")
                }
                if ([string] $candidate.plugin_pins -like 'blocked: *') {
                    $would.Add('BLOCKED now: ' + ([string] $candidate.plugin_pins).Substring('blocked: '.Length))
                }
            }
            if ($junction.action -ne 'none') {
                $would.Add("switch $($linked.Count) junctions and the Codex /vibe line from $($installed.tag) to $($candidate.tag)")
                if ($report.run_guard.blocked) { $would.Add("BLOCKED now: VIBE_RUN_OPEN ($($report.run_guard.reason))") }
            }
            foreach ($p in $physChanges) { $would.Add("replace physical $($p.skill) ($($p.state): $($p.version_installed) -> $($p.version_main))") }
            $would.Add('verify: vibe + vibe-bot selftests, Codex config line, versions; roll back on failure')
            $report.status = 'preview'
            $report.would = @($would)
            $exitCode = 0
        }
    } else {
        $swap = $null
        $physApplied = $null
        if ($junction.action -ne 'none') {
            $stage = 'run-guard'
            if ($report.run_guard.blocked) { throw "VIBE_RUN_OPEN: $($report.run_guard.reason); close it with run_state.py complete first" }
            $stage = 'candidate'
            if ($reuse) {
                $srcScripts = Join-Path $releases "$($reuse.tag)-src\scripts"
                if (-not (Test-Path -LiteralPath $srcScripts -PathType Container)) { $srcScripts = Join-Path $repo 'scripts' }
                $check = Test-SkCandidatePackages $reuse.candidate $reuse.receipts $srcScripts
                if (-not $check.ok) { throw "CANDIDATE_INVALID: $($reuse.tag) failed $($check.failed -join ', ')" }
                $candidate.verified = $true
            } else {
                Assert-SkFreeMemory $MinFreeMemoryGB
                $inputsJson = (Invoke-SkGit $repo @('show', "${sha}:distribution/plugin-inputs.v1.json")).Out -join "`n"
                $pins = Find-SkPluginPins $PluginPins $releases $inputsJson
                $candidate.plugin_pins = $pins.path
                $built = Invoke-SkBuildCandidate -RepoRoot $repo -Commit $sha -Tag $candidate.tag -ReleasesDir $releases -PluginPins $pins.path -Apply
                $candidate.receipts = $built.receipts
            }
            $stage = 'junctions'
            $swap = Invoke-SkJunctionSwap -Tag $candidate.tag -ReleasesDir $releases -UserHome $userHomeDir -CodexHome $codexDir `
                -Decision "update-local $($sha.Substring(0, 7))" -Apply
            $report.junctions.archive = $swap.archive
            $report.junctions.config = $swap.config.action
        }
        try {
            if ($physChanges.Count) {
                $stage = 'physical'
                $physApplied = Invoke-SkPhysicalSync -RepoRoot $repo -Commit $sha -Skills @($physChanges | ForEach-Object { $_.skill }) `
                    -UserHome $userHomeDir -ArchiveTag $archiveTag -Apply
                $report.physical_archives = @($physApplied.skills | ForEach-Object { $_.archive } | Where-Object { $_ })
            }
            $stage = 'verify'
            $report.verify = Get-UpdateVerification $repo $sha $userHomeDir $codexDir $physical $true
            if (-not $report.verify.ok) { throw "VERIFY_FAILED: $($report.verify.problems -join '; ')" }
        } catch {
            # Leave the previous, verified install in place.
            $failure = $_.Exception.Message
            $problems = @()
            if ($physApplied -and $physApplied.undo) { $problems += Undo-SkPhysicalSync $physApplied.undo }
            if ($swap -and $swap.undo) { $problems += Undo-SkJunctionSwap $swap.undo }
            if ($problems.Count -or $failure -like 'ROLLBACK_FAILED:*') {
                throw "ROLLBACK_FAILED: $failure; rollback: $($problems -join '; ')"
            }
            throw "ROLLED_BACK: $failure"
        }
        $report.status = 'installed'
        $report.message = "installed $($candidate.tag) for main $($sha.Substring(0, 7))"
        $exitCode = 0
    }
} catch {
    $message = $_.Exception.Message
    $code = if ($message -match '^([A-Z][A-Z0-9_]+):') { $Matches[1] } else { 'UNEXPECTED' }
    $report.status = switch ($code) { 'ROLLED_BACK' { 'rolled-back' } 'ROLLBACK_FAILED' { 'rollback-failed' } default { 'blocked' } }
    $report.error = $code
    $report.detail = $message
    $report.stage = $stage
    $exitCode = if ($code -eq 'ROLLBACK_FAILED') { 3 } else { 2 }
} finally {
    if ($lock) { Exit-SkInstallLock $lock }
}
[Console]::Out.WriteLine(($report | ConvertTo-Json -Depth 12))
exit $exitCode
