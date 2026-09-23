#!/usr/bin/env bash
# SimonK adaptation of garrytan/gstack@b9706f3635b6a545f46fae607ae9d6bcbfb69b91.
# Copyright (c) 2026 Garry Tan. MIT terms and local delta: repository LICENSE.
# check-freeze.sh — PreToolUse hook for /freeze skill
# Reads JSON from stdin, checks if file_path is within the freeze boundary.
# Returns a PreToolUse hookSpecificOutput with permissionDecision "deny" to block,
# or {} to allow. The decision MUST be nested under hookSpecificOutput — Claude
# Code ignores a top-level permissionDecision, which silently no-ops the block.
#
# Polarity: freeze is a DENY-tier hook, so an unreadable payload DENIES
# (fail closed). A required file_path that is absent/invalid also denies.
# This is the opposite edge-handling from careful's ask-tier
# and intentionally so: /guard runs both, and a boundary that fails open is
# not a boundary.
set -euo pipefail

# Deny-tier backstop: any unexpected non-zero death (a failing pipeline under
# set -e, a deleted cwd, EACCES) would otherwise exit with no decision JSON,
# which Claude Code treats as non-blocking — the edit proceeds. Every
# deliberate output below sets _FREEZE_DECIDED first so a late failure after
# a decision never prints a second JSON object.
_FREEZE_DECIDED=""
_freeze_backstop() {
  local rc=$?
  if [ "$rc" -ne 0 ] && [ -z "$_FREEZE_DECIDED" ]; then
    _FREEZE_DECIDED=1
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[freeze] Hook failed unexpectedly (exit %s) - blocked, fail closed. Re-run ./setup or /unfreeze."}}\n' "$rc"
    exit 0
  fi
}
trap _freeze_backstop EXIT

# Read stdin
INPUT=$(cat)

# Shared JSON helpers (extractor + encoder) — one copy for careful AND freeze.
# freeze previously carried its own grep-first extractor which truncated at
# escaped quotes and failed OPEN; the shared file kills that drift class.
_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=careful/bin/hook-extract.sh
# Freeze is deny-tier: if its own helpers are missing/broken (partial install,
# mid-upgrade state), the boundary must fail CLOSED — inline JSON, since the
# encoder we would normally use lives in the file that just failed to load.
# NOTE: bash treats `.` on a MISSING file as fatal in non-interactive shells
# (an if-guard cannot catch it) — the existence check must come first.
_HOOK_HELPER="$_HOOK_DIR/../../careful/bin/hook-extract.sh"
if [ ! -f "$_HOOK_HELPER" ] || ! . "$_HOOK_HELPER" 2>/dev/null; then
  _FREEZE_DECIDED=1
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[freeze] Hook helpers unavailable (broken install?) - blocked, fail closed. Reinstall gstack or run /unfreeze."}}\n'
  exit 0
fi

# Locate the state file using the CURRENT SimonK writer expression, not the
# newer upstream gstack-paths contract. See hook-extract.sh and LICENSE.
# A helper from an older install that lacks the function must fail CLOSED
# (the existence check above only proves the file sourced), never exit 127
# with no JSON — Claude Code treats that as non-blocking.
if ! command -v gstack_hook_state_root >/dev/null 2>&1; then
  _FREEZE_DECIDED=1
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[freeze] Hook helpers out of date (partial upgrade?) - blocked, fail closed. Re-run ./setup or /unfreeze."}}\n'
  exit 0
fi
STATE_DIR="$(gstack_hook_state_root; printf x)"; STATE_DIR="${STATE_DIR%x}"
FREEZE_FILE="$STATE_DIR/freeze-dir.txt"

# If no freeze file exists, allow everything (not yet configured)
if [ ! -e "$FREEZE_FILE" ] && [ ! -L "$FREEZE_FILE" ]; then
  _FREEZE_DECIDED=1
  echo '{}'
  exit 0
fi

if [ ! -f "$FREEZE_FILE" ] || [ ! -r "$FREEZE_FILE" ] || [ -L "$FREEZE_FILE" ]; then
  gstack_hook_decision deny "[freeze] Invalid or unreadable boundary state. Blocked (fail closed)."
  _FREEZE_DECIDED=1
  exit 0
fi

# First line, trimmed of LEADING/TRAILING whitespace only. The previous
# `tr -d '[:space:]'` deleted INTERNAL spaces too, so a boundary like
# "~/My Project/src" could never match anything — every edit denied (or the
# mangled path accidentally allowed the wrong tree).
FREEZE_DIR=$(head -n 1 "$FREEZE_FILE" 2>/dev/null | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
# A literal leading ~ in the state file never matches absolute tool paths
# (tilde is not expanded from variables) — expand it here.
case "$FREEZE_DIR" in
  "~/"*) FREEZE_DIR="$HOME/${FREEZE_DIR#\~/}" ;;
  "~") FREEZE_DIR="$HOME" ;;
esac

# A present but malformed boundary is not an inactive freeze. Current writers
# resolve an existing absolute POSIX directory using cd + pwd (Git Bash here).
case "$FREEZE_DIR" in
  /*) ;;
  *) gstack_hook_decision deny "[freeze] Invalid boundary state. Re-run /freeze or /unfreeze."
     _FREEZE_DECIDED=1; exit 0 ;;
esac
if [ ! -d "$FREEZE_DIR" ]; then
  gstack_hook_decision deny "[freeze] Boundary directory is unavailable. Blocked (fail closed)."
  _FREEZE_DECIDED=1
  exit 0
fi

# Extract file_path from tool_input with the shared real-JSON parser.
set +e
FILE_PATH=$(gstack_hook_extract_field "$INPUT" file_path)
EXTRACT_RC=$?
set -e

# Unparseable payload (or no parser available): DENY. A boundary hook that
# allows what it cannot read is not a boundary.
if [ "$EXTRACT_RC" -ne 0 ]; then
  gstack_hook_decision deny "[freeze] Could not parse the tool payload to check the freeze boundary. Blocked (fail closed). Freeze boundary: $FREEZE_DIR"
  _FREEZE_DECIDED=1
  exit 0
fi

# Defense against an incompatible older extractor: required file_path missing.
if [ -z "$FILE_PATH" ]; then
  gstack_hook_decision deny "[freeze] Missing file_path in Edit/Write payload. Blocked (fail closed)."
  _FREEZE_DECIDED=1
  exit 0
fi

# Resolve file_path to absolute if it isn't already
case "$FILE_PATH" in
  /*) ;; # already absolute
  *)
    FILE_PATH="$(pwd)/$FILE_PATH"
    ;;
esac

# Normalize: remove double slashes and trailing slash
FILE_PATH=$(printf '%s' "$FILE_PATH" | sed 's|/\+|/|g;s|/$||')

# Resolve symlinks and .. sequences (POSIX-portable, works on macOS).
# The FULL path is resolved, including the FINAL component: the previous
# version resolved only the parent directory, so an in-boundary symlink
# pointing at an out-of-boundary target sailed through the check while the
# actual write landed outside the boundary. A final component that is a
# symlink is followed (bounded, cycle-safe) so the TARGET gets checked; a
# final component that does not exist yet (new file) has nothing to follow
# and parent resolution is the correct behavior.
_resolve_path() {
  local _p="$1" _dir _base _tgt _i=0
  while [ -L "$_p" ] && [ "$_i" -lt 40 ]; do
    _tgt=$(readlink "$_p" 2>/dev/null) || return 1
    case "$_tgt" in
      /*) _p="$_tgt" ;;
      *) _p="$(dirname "$_p")/$_tgt" ;;
    esac
    _i=$((_i + 1))
  done
  [ ! -L "$_p" ] || return 1
  if [ -d "$_p" ]; then
    _dir="$_p"
    _base=""
  else
    _dir="$(dirname "$_p")"
    _base="$(basename "$_p")"
  fi
  # Never prefix-check an unresolved path containing missing/../.. parents.
  # Conservative contract: a new file needs an existing resolvable parent.
  _dir="$(cd "$_dir" 2>/dev/null && pwd -P)" || return 1
  # Git Bash can expose the same directory as /tmp/... and /c/...; compare
  # canonical drive paths after physical resolution, not different mounts.
  if command -v cygpath >/dev/null 2>&1; then
    _dir="$(cygpath -am "$_dir")" || return 1
  fi
  if [ -z "$_base" ]; then
    printf '%s' "$_dir"
  else
    printf '%s/%s' "${_dir%/}" "$_base"
  fi
}
FILE_PATH=$(_resolve_path "$FILE_PATH")
FREEZE_DIR=$(_resolve_path "$FREEZE_DIR")

# Check: does the file path start with the freeze directory?
case "$FILE_PATH" in
  "${FREEZE_DIR%/}/"*|"${FREEZE_DIR}")
    # Inside freeze boundary — allow
    _FREEZE_DECIDED=1
    echo '{}'
    ;;
  *)
    # Outside freeze boundary — deny
    # Log hook fire event (shared helper respects GSTACK_HOME)
    gstack_hook_log_fire freeze boundary_deny

    # The reason is JSON-encoded by the shared helper. Never interpolate paths
    # into hand-built JSON: a path containing a quote or newline produced
    # malformed JSON here, and the deny silently no-oped.
    gstack_hook_decision deny "[freeze] Blocked: $FILE_PATH is outside the freeze boundary ($FREEZE_DIR). Only edits within the frozen directory are allowed."
    _FREEZE_DECIDED=1
    ;;
esac
