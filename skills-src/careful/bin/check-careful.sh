#!/usr/bin/env bash
# SimonK adaptation of garrytan/gstack v1.91.9.0 careful/bin/check-careful.sh
# Upstream commit for v1.91.9.0: 96764e80a641e28141ec8297223768029f5bf483.
# (upstream LF bytes sha256 7b04f0b8f409d4ecf166ef45e72eb95ed7c2f37434bd7125e6b403d0f7bf5d42,
# byte-identical to the earlier pin b9706f3635b6a545f46fae607ae9d6bcbfb69b91).
# Copyright (c) 2026 Garry Tan. MIT terms and local delta: repository LICENSE.
# SimonK deltas (hub decision D-56, 2026-10-03). Everything else is upstream:
#   1. Every INTERNAL failure returns "deny", never "ask" and never silence:
#      EXIT-trap backstop, missing/broken/outdated helper, empty or invalid
#      JSON, no JSON parser, Bash payload without a usable command, pattern
#      matcher error (grep rc>1), unresolvable per-project slug. Only deny was
#      measured to block under bypassPermissions (2026-10-03); ask was not.
#   2. A non-Bash payload is recognised by tool_name. Upstream allowed ANY
#      payload without tool_input.command (and an empty payload), which also
#      let a Bash call whose command could not be read through.
#   3. _careful_match: grep rc>1 is a matcher error, not a clean non-match.
#   4. Per-project slug comes from the vendored bin/gstack-slug.sh (upstream
#      evaluated ../../bin/gstack-slug, absent outside the gstack tree).
#   5. (hub decision D-62 A1, 2026-10-03) The HIGH recursive-delete check also
#      knows Windows/MSYS spellings of a drive root (/c /c/ /c/* /mnt/c C: C:\
#      C:/*) and one-level "everything" globs of root or home (~/* $HOME/*),
#      removes every quote character before classifying (shell quote removal),
#      and covers cmd.exe rd|rmdir|del /s and PowerShell Remove-Item -Recurse
#      launched from the Bash tool against a drive root or home. Same SIMPLE
#      command rule; ambiguous shapes keep their previous tier.
#   6. (hub decision D-62 minimal B) A PowerShell-tool payload (second
#      frontmatter entry, argument "powershell") is checked DENY-ONLY:
#      literal recursive delete of a drive root or home, disk cmdlets and
#      force-push to the default branch deny; everything else allows.
# check-careful.sh — PreToolUse hook for /careful skill
# Reads JSON from stdin, checks Bash command for destructive patterns.
# Two tiers:
#   HIGH   — a tiny set of catastrophic SIMPLE commands returns "deny"
#            (best-effort advisory hard-stop, not a policy boundary).
#   MEDIUM — the destructive families below return "ask" (always overridable).
# The decision MUST be nested under hookSpecificOutput — Claude Code ignores a
# top-level permissionDecision, which silently no-ops the warning.
set -euo pipefail

# --- SimonK: internal failure = deny ---------------------------------------
# Pure printf with fixed ASCII text (no quotes/backslashes in any caller's
# message): the failure path must not depend on the JSON encoder or parser
# that may be the very thing that failed.
_careful_fail() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[careful][HOOK FAILURE] The careful hook itself failed: %s This command was NOT safety-checked, so it is blocked. Way out: fix the hook in ~/.claude/skills/careful/bin, or start a new session without /careful."}}\n' "$1"
  exit 0
}
# Unexpected runtime failure (set -e/-u/pipefail) must not exit without a
# decision: a hook that dies is non-blocking, so the call would just run.
_careful_backstop() {
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    _careful_fail "unexpected script error (exit $rc)."
  fi
}
trap _careful_backstop EXIT

# Read stdin (JSON with tool_input)
INPUT=$(cat)

# Shared JSON helpers (extractor + encoder) — one copy for careful AND freeze.
# See hook-extract.sh for the drift history that motivated the shared file.
_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=careful/bin/hook-extract.sh
# bash treats `.` on a MISSING file as fatal non-interactively — the existence
# check must come first. A partial install must DENY, never fall silent.
_HOOK_HELPER="$_HOOK_DIR/hook-extract.sh"
if [ ! -f "$_HOOK_HELPER" ] || ! . "$_HOOK_HELPER" 2>/dev/null; then
  _careful_fail "hook-extract.sh is missing or broken (partial install?)."
fi
# A helper from an older install sources fine but lacks the functions this
# script needs; calling one would exit 127 mid-run.
for _FN in gstack_hook_extract_tool_name gstack_hook_extract_field gstack_hook_decision gstack_hook_log_fire gstack_hook_state_root; do
  command -v "$_FN" >/dev/null 2>&1 || _careful_fail "hook-extract.sh is out of date (no $_FN)."
done

# Empty input is not a non-Bash payload; it is an unreadable one.
if [ -z "$INPUT" ]; then
  _careful_fail "the hook received an empty payload."
fi

# Identify the tool. Invalid JSON, a non-object payload, or no python3/node
# parser all land here. Fail closed — a hook that gates destructive commands
# must not allow-by-default on unreadable input.
set +e
TOOL_NAME=$(gstack_hook_extract_tool_name "$INPUT")
TOOL_RC=$?
set -e
if [ "$TOOL_RC" -ne 0 ]; then
  _careful_fail "could not parse the tool payload (invalid JSON or no python3/node parser)."
fi

# SimonK (D-62 minimal B): two frontmatter entries run this script. The Bash
# matcher passes no argument; the PowerShell matcher passes "powershell". An
# absent tool_name means the tool of the entry that ran us. Any other argument
# is a wiring error, so fail closed. A tool other than Bash or PowerShell is
# outside this hook's scope — allow.
case "${1:-}" in
  '') _HOOK_TOOL=bash ;;
  powershell) _HOOK_TOOL=powershell ;;
  *) _careful_fail "unknown hook mode argument (expected none or powershell)." ;;
esac
_TOOL_LC=$(printf '%s' "$TOOL_NAME" | tr '[:upper:]' '[:lower:]')
[ -n "$_TOOL_LC" ] || _TOOL_LC="$_HOOK_TOOL"
case "$_TOOL_LC" in
  bash) _TOOL_LABEL=Bash ;;
  powershell) _TOOL_LABEL=PowerShell ;;
  *) echo '{}'; exit 0 ;;
esac

# Extract the "command" field value from tool_input with a real JSON parser.
#
# The previous extractor was
#   grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"'
# whose [^"]* stops at the first escaped quote in the JSON string value. Any
# destructive command preceded by a quoted argument was therefore truncated
# away before the pattern checks ever ran:
#
#   git commit -m "wip" && rm -rf /   ->  CMD='git commit -m \'   -> allowed
#   bash -c "rm -rf /"                ->  CMD='bash -c \'         -> allowed
#   echo "x"; rm -rf ~                ->  CMD='echo \'            -> allowed
#
# Parse the payload properly instead, and fail CLOSED when it cannot be parsed.
set +e
CMD=$(gstack_hook_extract_field "$INPUT" command)
EXTRACT_RC=$?
set -e

# A Bash/PowerShell call whose command is missing, empty, non-string or carries NUL.
if [ "$EXTRACT_RC" -ne 0 ] || [ -z "$CMD" ]; then
  _careful_fail "the $_TOOL_LABEL payload has no usable tool_input.command (missing, empty, non-string or NUL)."
fi

# A matcher error is unknown, not a clean non-match. Calls run in this shell
# (not a pipeline or subshell), so the failure decision exits the hook itself.
_careful_match() {
  local rc=0
  grep "$@" || rc=$?
  if [ "$rc" -gt 1 ]; then
    _careful_fail "the pattern matcher (grep) errored with exit $rc."
  fi
  return "$rc"
}

# Log a hook fire event (pattern name only, never command content).
# Shared helper respects GSTACK_HOME, so tests never write real analytics.
_careful_log_fire() { gstack_hook_log_fire careful "$1"; }

# Normalize: lowercase for case-insensitive SQL matching
CMD_LOWER=$(printf '%s' "$CMD" | tr '[:upper:]' '[:lower:]')

# --- Shared HIGH-tier helpers (SimonK, hub decision D-62) -------------------
# None of these call an external program except through _careful_match (whose
# error path exits with a deny itself) or a `|| true`-guarded git probe: they
# run as `if` conditions, where errexit is suspended, so an unguarded failure
# inside them would silently read as "no match".

# Is $1 a root-class delete target? $1 has every quote character removed
# already. $2 is the shell that performs the delete:
#   sh  — rm run by bash (case-sensitive, / separators, MSYS drive spellings)
#   win — cmd.exe / PowerShell launched from the Bash tool ($1 lowercased;
#         / or \ separators; MSYS spellings still apply, Git Bash converts them)
#   ps  — the PowerShell tool itself ($1 lowercased; no MSYS spellings)
# Root class = the filesystem root, a drive root, or the home directory, each
# optionally followed by ONE level of "everything" glob (*  .*  *.*). Home is
# spelled the way the deleting shell spells it: bash ~ $HOME ${HOME}; cmd and
# PowerShell add %USERPROFILE% and $env:USERPROFILE. Deeper globs, relative
# paths (. .. *), literal profile paths (/c/Users/<name>) and other variables
# are NOT root class: they are ambiguous, so they keep their previous tier.
# Brackets instead of backslash escapes keep the EREs portable across regcomp
# implementations.
_careful_root_target() {
  local t="$1" g='([*]|[.][*]|[*][.][*])' sep='/' msys=1
  local home='(~|[$]HOME|[$][{]HOME[}])'
  if [ "$2" = win ] || [ "$2" = ps ]; then
    sep='/\\'
    home='(~|[$]home|[$][{]home[}]|[$]env:userprofile|[$][{]env:userprofile[}]|%userprofile%)'
  fi
  if [ "$2" = ps ]; then msys=0; fi
  local re_root='^['"$sep"']+'"$g"'?$'                          # / // /* /.*
  local re_msys='^/((mnt|cygdrive)/)?[a-zA-Z](/+'"$g"'?)?$'     # /c /c/ /c/* /mnt/c
  local re_drive='^[a-zA-Z]:([/\\]+'"$g"'?)?$'                  # C: C:/ C:\ C:\*
  local re_home='^'"$home"'(['"$sep"']+'"$g"'?)?$'              # ~ ~/* $HOME/* ${HOME}
  if [[ $t =~ $re_root || $t =~ $re_drive || $t =~ $re_home ]]; then return 0; fi
  [ "$msys" -eq 1 ] && [[ $t =~ $re_msys ]]
}

# cmd.exe / PowerShell recursive delete. $1 = ONE lowercased simple command,
# $2 = win (launched from the Bash tool) or ps (the PowerShell tool itself).
# Returns 0 only when the command is
#   cmd[.exe] [switches] /c (rd|rmdir|del|erase) ... /s ... <targets>
#   powershell|pwsh[.exe] [host options] -c|-Command (Remove-Item|ri|rm|del|
#     rd|rmdir|erase) ... -Recurse ... <targets>
#   (ps only) Remove-Item|ri|rm|del|rd|rmdir|erase ... -Recurse|/s ... <targets>
# and EVERY target is root class (same rule as rm). Anything else in the
# argument list (a second command after cmd's &, -Include *.log, a subfolder)
# counts as a non-root target, so the call keeps its previous tier. -WhatIf is
# a dry run and never HIGH. Encoded commands, variables, pipes and splatting
# are out of reach of string matching.
_careful_win_delete_root() {
  local tok base kind="" stage=lead recurse=0 root=0 safe=0 skipnext=0 bs='\' mode="$2"
  local re_cmdflag='^[-/]c(o(m(m(a(n(d)?)?)?)?)?)?$'
  local re_recurse='^-r(e(c(u(r(s(e)?)?)?)?)?)?(:[$]true)?$'
  set -f
  for tok in $1; do
    tok="${tok//\"/}"; tok="${tok//\'/}"
    case "$stage" in
      lead)
        # PowerShell call / dot-source operator in front of the command name.
        case "$mode:$tok" in 'ps:&'|'ps:.') continue ;; esac
        # basename, either separator: C:\Windows\System32\cmd.exe -> cmd.exe
        base=${tok##*/}; base=${base##*"$bs"}
        case "$mode:$base" in
          *:cmd|*:cmd.exe) kind=cmd; stage=cmdsw ;;
          *:powershell|*:powershell.exe|*:pwsh|*:pwsh.exe) kind=ps; stage=psopt ;;
          ps:remove-item|ps:ri|ps:rm|ps:del|ps:rd|ps:rmdir|ps:erase) kind=ps; stage=args ;;
          *) break ;;
        esac ;;
      cmdsw)  # cmd's own switches; /c or /k (MSYS spelling //c) runs the rest
        case "$tok" in
          /c|//c|/k|//k) stage=verb ;;
          /?|//?|/?:*|//?:*) : ;;
          *) break ;;
        esac ;;
      psopt)  # host options (-NoProfile, -ExecutionPolicy Bypass) until -Command
        if [[ $tok =~ $re_cmdflag ]]; then stage=verb; fi ;;
      verb)
        case "$kind:$tok" in
          cmd:rd|cmd:rmdir|cmd:del|cmd:erase) stage=args ;;
          ps:remove-item|ps:ri|ps:rm|ps:del|ps:rd|ps:rmdir|ps:erase) stage=args ;;
          *) break ;;
        esac ;;
      args)
        if [ "$skipnext" -eq 1 ]; then skipnext=0; continue; fi
        case "$kind:$tok" in
          # cmd's /s; in PowerShell `rmdir /s /q C:\` is the same intent.
          cmd:/s|cmd://s|ps:/s|ps://s) recurse=1 ;;
          cmd:/?|cmd://?|cmd:/?:*|cmd://?:*|ps:/?|ps://?) : ;;
          ps:-whatif|'ps:-whatif:$true') safe=1 ;;
          ps:-erroraction|ps:-ea|ps:-warningaction|ps:-wa) skipnext=1 ;;
          ps:-path:*|ps:-literalpath:*|ps:-lp:*)
            if _careful_root_target "${tok#*:}" "$mode"; then root=1; else safe=1; fi ;;
          ps:-*) if [[ $tok =~ $re_recurse ]]; then recurse=1; fi ;;
          *:[0-9]'>'*|*:'>'*|*:'*>'*|*:'<'*|*:'&') : ;;
          *) if _careful_root_target "$tok" "$mode"; then root=1; else safe=1; fi ;;
        esac ;;
    esac
  done
  set +f
  [ "$stage" = args ] && [ "$recurse" -eq 1 ] && [ "$root" -eq 1 ] && [ "$safe" -eq 0 ]
}

# Force-push to the repo's default branch (the shared history everyone pulls).
# $1 = ONE simple command (original case: branch names are case-sensitive).
# Force is carried by -f/--force OR by git's plus-refspec syntax (+main,
# +HEAD:main) which needs no flag at all. --force-with-lease never matches.
# Sets _DEFAULT_BRANCH for the deny message.
_careful_push_targets_default() {
  local cmd="$1" has_force=0 hit=0 tok ref current
  _DEFAULT_BRANCH=""
  _careful_match -qE '^[[:space:]]*git[[:space:]]+push([[:space:]]|$)' <<< "$cmd" 2>/dev/null || return 1
  if _careful_match -qE '(^|[[:space:]])(-f|--force)($|[[:space:]])' <<< "$cmd" 2>/dev/null; then
    has_force=1
  elif _careful_match -qE '(^|[[:space:]])\+[^[:space:]]' <<< "$cmd" 2>/dev/null; then
    has_force=1
  fi
  [ "$has_force" -eq 1 ] || return 1
  # Full branch path (slashed defaults like release/2.0 stay intact) and
  # FIXED-STRING token comparison — never interpolate a branch name into
  # an ERE (metacharacters would over/under-match).
  _DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|^refs/remotes/origin/||' || true)
  # Conductor worktrees often lack the origin/HEAD symbolic ref — without a
  # fallback the HIGH tier would be silently inert in the primary deploy
  # environment. Probe the two conventional defaults.
  if [ -z "$_DEFAULT_BRANCH" ]; then
    if git show-ref --verify -q refs/remotes/origin/main 2>/dev/null; then
      _DEFAULT_BRANCH="main"
    elif git show-ref --verify -q refs/remotes/origin/master 2>/dev/null; then
      _DEFAULT_BRANCH="master"
    fi
  fi
  [ -n "$_DEFAULT_BRANCH" ] || return 1
  set -f
  for tok in $cmd; do
    # Strip one layer of surrounding quotes: `git push -f origin "main"`
    # must not dodge the deny just because the ref is quoted.
    tok="${tok#\"}"; tok="${tok%\"}"; tok="${tok#\'}"; tok="${tok%\'}"
    case "$tok" in git|push|sudo|-*) continue ;; esac
    ref="${tok#+}"            # +main -> main
    ref="${ref##*:}"          # HEAD:main / src:main -> main
    if [ "$ref" = "$_DEFAULT_BRANCH" ]; then
      hit=1
      break
    fi
  done
  set +f
  if [ "$hit" -eq 0 ] && _careful_match -qE '^[[:space:]]*git[[:space:]]+push([[:space:]]+(-f|--force))*[[:space:]]*$' <<< "$cmd" 2>/dev/null; then
    # Bare `git push --force` (force flags only, no remote/ref): targets
    # the current branch's upstream — the default branch only when ON it.
    current=$(git branch --show-current 2>/dev/null || true)
    if [ -n "$current" ] && [ "$current" = "$_DEFAULT_BRANCH" ]; then hit=1; fi
  fi
  [ "$hit" -eq 1 ]
}

# PowerShell disk destroyers. $1 = ONE lowercased simple command. The cmdlet
# must be the command name (Get-Help Format-Volume does not match); -WhatIf
# is a dry run.
_careful_ps_disk() {
  local tok first="" base whatif=0 bs='\'
  set -f
  for tok in $1; do
    tok="${tok//\"/}"; tok="${tok//\'/}"
    if [ -z "$first" ]; then
      case "$tok" in '&'|'.') continue ;; esac
      first="$tok"
      continue
    fi
    case "$tok" in -whatif|'-whatif:$true') whatif=1 ;; esac
  done
  set +f
  base=${first##*/}; base=${base##*"$bs"}   # Storage\Format-Volume -> format-volume
  case "$base" in
    format-volume|clear-disk|initialize-disk|remove-partition) [ "$whatif" -eq 0 ] ;;
    *) return 1 ;;
  esac
}

# Split a PowerShell command into simple commands, one per line (pure bash):
# backtick line continuations are joined; ; | || && newlines and the block
# delimiters { } ( ) separate; a comma (array of paths) becomes a space. A
# single & (call operator, 2>&1) does not separate. Result in _PS_SPLIT.
_careful_ps_split() {
  local s="$1" nl=$'\n'
  s=${s//$'\r'/}
  s=${s//\`$nl/ }
  s=${s//&&/$nl}
  s=${s//;/$nl}; s=${s//|/$nl}
  s=${s//\{/$nl}; s=${s//\}/$nl}; s=${s//\(/$nl}; s=${s//\)/$nl}
  s=${s//,/ }
  _PS_SPLIT="$s"
}

# --- PowerShell tool: deny-only (SimonK, hub decision D-62 minimal B) --------
# PowerShell carries ~80% of this machine's commands, so this branch never
# asks: a handful of literal catastrophic shapes deny, everything else allows.
# Each simple command (see _careful_ps_split) is checked on its own:
#   - recursive delete of a drive root or home (Remove-Item & aliases with
#     -Recurse, cmd /c rd|rmdir|del /s, nested powershell|pwsh -Command);
#   - Format-Volume, Clear-Disk, Initialize-Disk, Remove-Partition;
#   - force-push to the default branch, only when the whole command is ONE
#     simple command (a Set-Location earlier would change which repo it is).
# Gaps (string matching cannot see them): variables other than HOME and
# USERPROFILE, splatting, -EncodedCommand, Invoke-Expression, Start-Process,
# pipeline input (gci C:\ | Remove-Item -Recurse), here-strings.
if [ "$_TOOL_LC" = powershell ]; then
  # ${name} -> $name, so ${env:USERPROFILE} survives the { } split. Top level
  # on purpose: a sed/tr failure here hits the EXIT backstop (deny).
  _PS_NORM=$(printf '%s' "$CMD" | sed -E 's/[$][{]([^}]*)[}]/$\1/g')
  _PS_LOW=$(printf '%s' "$_PS_NORM" | tr '[:upper:]' '[:lower:]')
  _careful_ps_split "$_PS_NORM"; _PS_SEGS="$_PS_SPLIT"
  _careful_ps_split "$_PS_LOW"; _PS_LSEGS="$_PS_SPLIT"
  _PS_N=0
  while IFS= read -r _SEG; do
    case "$_SEG" in *[![:space:]]*) _PS_N=$((_PS_N + 1)) ;; esac
  done <<< "$_PS_LSEGS"
  _PS_HIT=""
  while IFS= read -r _SEG <&3 && IFS= read -r _LSEG <&4; do
    case "$_LSEG" in *[![:space:]]*) : ;; *) continue ;; esac
    if _careful_ps_disk "$_LSEG"; then _PS_HIT=disk; break; fi
    if _careful_win_delete_root "$_LSEG" ps; then _PS_HIT=delete; break; fi
    if [ "$_PS_N" -eq 1 ] && _careful_push_targets_default "$_SEG"; then _PS_HIT=push; break; fi
  done 3<<< "$_PS_SEGS" 4<<< "$_PS_LSEGS"
  case "$_PS_HIT" in
    disk)
      _careful_log_fire "ps_high_disk"
      gstack_hook_decision deny "[careful][HIGH] PowerShell: Format-Volume, Clear-Disk, Initialize-Disk and Remove-Partition are blocked while /careful is active. If you truly mean it, end the /careful session first." ;;
    delete)
      _careful_log_fire "ps_high_delete_root"
      gstack_hook_decision deny "[careful][HIGH] PowerShell: recursive delete of a drive root or the home directory (or all of its direct contents) is blocked while /careful is active. If you truly mean it, end the /careful session first." ;;
    push)
      _careful_log_fire "ps_high_force_push_default"
      gstack_hook_decision deny "[careful][HIGH] Force-push to the default branch ($_DEFAULT_BRANCH) is blocked while /careful is active. Use --force-with-lease on a feature branch, or end the /careful session if you truly mean it." ;;
    *) echo '{}' ;;
  esac
  exit 0
fi

# Everything below is the Bash tool.

# --- Shell-obfuscation tripwire ---
# Every check below inspects the command as a STRING, but bash executes what the
# string MEANS after expansion. ${IFS} holds the default field separator and
# contains no literal whitespace, so
#
#   rm${IFS}-rf${IFS}/
#
# matches none of the `rm\s+` patterns while executing as a full recursive
# delete. The same holds for a command assembled by a base64 decode piped to a
# shell. Rather than try to out-parse bash, treat these splitting/decoding
# primitives as a reason to ask: they are vanishingly rare in commands a human
# actually means to run unattended.
if _careful_match -qE '\$\{IFS\}|\$IFS|\$\(echo[^)]*base64[^)]*\)|base64[[:space:]]+(-d|--decode)[^|]*\|[[:space:]]*(sh|bash)' <<< "$CMD" 2>/dev/null; then
  gstack_hook_decision ask "[careful] Shell obfuscation detected (IFS word-splitting or base64-to-shell). Read the command carefully before approving."
  exit 0
fi

# --- HIGH tier: hard deny (best-effort advisory hard-stop, NOT a policy boundary) ---
# Only SIMPLE commands are eligible: string matching cannot resolve what a
# compound command does (`cd X && git push --force` — whose cwd? which repo?),
# so anything containing ; && || | or a newline falls through to the MEDIUM ask
# families below — conservative failure = ask, never guess.
# --force-with-lease is deliberately NOT matched here (it is the safe variant).
# curl|sh stays MEDIUM/allow territory: hard-denying it would block legitimate
# installer flows, including gstack's own setup pattern.
_IS_SIMPLE=1
case "$CMD" in
  *';'*|*'&&'*|*'||'*|*'|'*|*$'\n'*) _IS_SIMPLE=0 ;;
esac
if [ "$_IS_SIMPLE" -eq 1 ]; then
  # Recursive delete aimed at the filesystem root, a drive root or the whole
  # home directory (or every direct entry of one of them).
  # Tokenized: options (long or short, any position — --no-preserve-root may
  # trail the target) are skipped; EVERY non-option token must be a root-class
  # target (see _careful_root_target), and a recursive flag must be present.
  # noglob is forced around word-splitting so a literal /* token never expands.
  if _careful_match -qE '^[[:space:]]*(sudo[[:space:]]+)?rm[[:space:]]' <<< "$CMD" 2>/dev/null \
    && _careful_match -qE '(^|[[:space:]])(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)([[:space:]]|$)' <<< "$CMD" 2>/dev/null; then
    _ROOT_TARGETS=0
    _SAFE_TARGETS=0
    set -f
    for _TOK in $CMD; do
      # SimonK: remove EVERY quote character (shell quote removal), not just
      # one surrounding layer: rm -rf "/" is rm -rf /, "$HOME"/* is $HOME/*.
      # Word splitting still ignores quotes, so "E:/Coding Infra" stays two
      # non-root tokens (string matching, not a shell parser).
      _TOK="${_TOK//\"/}"; _TOK="${_TOK//\'/}"
      case "$_TOK" in
        # Skip non-target decoration: options, `--`, redirections (2>/dev/null
        # is the most common suffix on agent-generated commands), backgrounding.
        sudo|rm|-*|--|[0-9]'>'*|'>'*|'<'*|'&') continue ;;
      esac
      if _careful_root_target "$_TOK" sh; then _ROOT_TARGETS=1; else _SAFE_TARGETS=1; fi
    done
    set +f
    if [ "$_ROOT_TARGETS" -eq 1 ] && [ "$_SAFE_TARGETS" -eq 0 ]; then
      _careful_log_fire "high_rm_root"
      gstack_hook_decision deny "[careful][HIGH] Recursive delete of a filesystem or drive root, or of the home directory (or all of its direct contents), is blocked while /careful is active. If you truly mean it, end the /careful session first."
      exit 0
    fi
  fi
  if _careful_win_delete_root "$CMD_LOWER" win; then
    _careful_log_fire "high_win_delete_root"
    gstack_hook_decision deny "[careful][HIGH] Recursive cmd.exe/PowerShell delete of a drive root or the home directory is blocked while /careful is active. If you truly mean it, end the /careful session first."
    exit 0
  fi
  if _careful_push_targets_default "$CMD"; then
    _careful_log_fire "high_force_push_default"
    gstack_hook_decision deny "[careful][HIGH] Force-push to the default branch ($_DEFAULT_BRANCH) is blocked while /careful is active. Use --force-with-lease on a feature branch, or end the /careful session if you truly mean it."
    exit 0
  fi
fi

# --- Check for safe exceptions (one standalone rm of build artifacts) ---
# Match the complete command. Parsing only the last rm is unsafe because shell
# syntax or comments can hide an earlier destructive command, for example:
#   rm -rf / # rm -rf node_modules
# Unknown syntax fails closed and falls through to the destructive checks.
# Two hardenings on top of the anchored shape (#2039 wave):
#   - flag cluster accepts capital -R (BSD/macOS recursive), so a single
#     `rm -Rf node_modules` stays allowed instead of prompting;
#   - target tokens exclude `(` and backtick, so command substitution that
#     ENDS in a whitelisted suffix (`rm -rf $(./wipe-all)/node_modules`)
#     cannot ride the whitelist. Plain $VAR expansion (no parenthesis) is
#     still allowed.
#   - multi-line commands never ride the whitelist: grep matches the anchored
#     shape against EACH line, so `rm -rf /\nrm -rf node_modules` would be
#     allowed by its second line. With the JSON-parser extraction the \n in
#     the payload is a real newline (the old grep extractor kept it as two
#     literal characters, which broke the anchored match by accident).
case "$CMD" in
  *$'\n'*) : ;; # multi-line: fall through to the destructive checks
  *)
    if _careful_match -qE '^[[:space:]]*rm[[:space:]]+(-[a-zA-Z]*[rR][a-zA-Z]*[[:space:]]+|--recursive[[:space:]]+)(([^[:space:];&|#(`]*/)?(node_modules|\.next|dist|__pycache__|\.cache|build|\.turbo|coverage)[[:space:]]*)+$' <<< "$CMD" 2>/dev/null; then
      echo '{}'
      exit 0
    fi
    ;;
esac

# --- Destructive pattern checks (MEDIUM tier — always overridable) ---
WARN=""
PATTERN=""

# rm -rf / rm -r / rm -R / rm --recursive (capital -R is BSD/macOS recursive)
if _careful_match -qE 'rm\s+(-[a-zA-Z]*[rR]|--recursive)' <<< "$CMD" 2>/dev/null; then
  WARN="Destructive: recursive delete (rm -r). This permanently removes files."
  PATTERN="rm_recursive"
fi

# DROP TABLE / DROP DATABASE
if [ -z "$WARN" ] && _careful_match -qE 'drop\s+(table|database)' <<< "$CMD_LOWER" 2>/dev/null; then
  WARN="Destructive: SQL DROP detected. This permanently deletes database objects."
  PATTERN="drop_table"
fi

# TRUNCATE
if [ -z "$WARN" ] && _careful_match -qE '\btruncate\b' <<< "$CMD_LOWER" 2>/dev/null; then
  WARN="Destructive: SQL TRUNCATE detected. This deletes all rows from a table."
  PATTERN="truncate"
fi

# git push --force / git push -f / plus-refspec force (git push origin +ref)
if [ -z "$WARN" ] && _careful_match -qE 'git\s+push\s' <<< "$CMD" 2>/dev/null \
  && _careful_match -qE '(-f\b|--force|(^|[[:space:]])\+[^[:space:]])' <<< "$CMD" 2>/dev/null; then
  WARN="Destructive: git force-push rewrites remote history. Other contributors may lose work."
  PATTERN="git_force_push"
fi

# git reset --hard
if [ -z "$WARN" ] && _careful_match -qE 'git\s+reset\s+--hard' <<< "$CMD" 2>/dev/null; then
  WARN="Destructive: git reset --hard discards all uncommitted changes."
  PATTERN="git_reset_hard"
fi

# git checkout . / git restore .
if [ -z "$WARN" ] && _careful_match -qE 'git\s+(checkout|restore)\s+\.' <<< "$CMD" 2>/dev/null; then
  WARN="Destructive: discards all uncommitted changes in the working tree."
  PATTERN="git_discard"
fi

# kubectl delete
if [ -z "$WARN" ] && _careful_match -qE 'kubectl\s+delete' <<< "$CMD" 2>/dev/null; then
  WARN="Destructive: kubectl delete removes Kubernetes resources. May impact production."
  PATTERN="kubectl_delete"
fi

# docker rm -f / docker system prune
if [ -z "$WARN" ] && _careful_match -qE 'docker\s+(rm\s+-f|system\s+prune)' <<< "$CMD" 2>/dev/null; then
  WARN="Destructive: Docker force-remove or prune. May delete running containers or cached images."
  PATTERN="docker_destructive"
fi

# --- Additive project patterns ---
# Config can only ADD warn rules, never remove or weaken a baseline family:
# these files are consulted AFTER the hardcoded checks and only when none of
# them matched, so no file content can suppress a baseline warning. One POSIX
# ERE per line; blank lines and #-comments skipped; an invalid regex is
# skipped (never fatal — the hook must not break on a typo in config).
if [ -z "$WARN" ]; then
  # Same state root the writers use — see gstack_hook_state_root in
  # hook-extract.sh (SimonK: ${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}).
  _GSTACK_HOME_DIR="$(gstack_hook_state_root; printf x)"; _GSTACK_HOME_DIR="${_GSTACK_HOME_DIR%x}"
  _PATTERN_FILES="$_GSTACK_HOME_DIR/careful-patterns.txt"
  # Short-circuit: resolving the project slug costs a subprocess + git call on
  # EVERY Bash command while /careful is active — only pay it when some
  # per-project pattern file actually exists anywhere.
  _ANY_PROJ_PAT=$(find "$_GSTACK_HOME_DIR/projects" -maxdepth 2 -name careful-patterns.txt -print -quit 2>/dev/null || true)
  if [ -n "$_ANY_PROJ_PAT" ]; then
    # SimonK: vendored helper, and its output is parsed, not eval'd. A rule the
    # user configured but the hook cannot locate is a hook failure (deny),
    # not a silent skip.
    _SLUG_HELPER="$_HOOK_DIR/gstack-slug.sh"
    [ -f "$_SLUG_HELPER" ] || _careful_fail "gstack-slug.sh is missing, so per-project careful patterns cannot be applied."
    _SLUG_RC=0
    _SLUG_OUT=$(bash "$_SLUG_HELPER" 2>/dev/null) || _SLUG_RC=$?
    # gstack-slug prints exactly one sanitized SLUG= line; accept only that shape.
    SLUG=$(printf '%s\n' "$_SLUG_OUT" | sed -n 's/^SLUG=\([a-zA-Z0-9._-]*\)$/\1/p')
    case "$_SLUG_RC:$SLUG" in
      0:|0:.|0:..|[1-9]*) _careful_fail "gstack-slug.sh could not resolve the project slug for per-project careful patterns." ;;
    esac
    _PATTERN_FILES="$_PATTERN_FILES
$_GSTACK_HOME_DIR/projects/$SLUG/careful-patterns.txt"
  fi
  while IFS= read -r _PF; do
    [ -f "$_PF" ] || continue
    while IFS= read -r _PAT || [ -n "$_PAT" ]; do
      case "$_PAT" in ''|'#'*) continue ;; esac
      _PAT_RC=0
      printf '' | grep -qE -- "$_PAT" 2>/dev/null || _PAT_RC=$?
      [ "$_PAT_RC" -eq 2 ] && continue # invalid ERE — skip the line
      if _careful_match -qE -- "$_PAT" <<< "$CMD" 2>/dev/null; then
        WARN="Project rule matched: $_PAT"
        PATTERN="project_rule"
        break
      fi
    done < "$_PF"
    [ -n "$WARN" ] && break
  done <<EOF_PATTERN_FILES
$_PATTERN_FILES
EOF_PATTERN_FILES
fi

# --- Output ---
if [ -n "$WARN" ]; then
  _careful_log_fire "$PATTERN"
  gstack_hook_decision ask "[careful] $WARN"
else
  echo '{}'
fi
