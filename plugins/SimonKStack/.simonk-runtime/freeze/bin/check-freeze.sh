#!/usr/bin/env bash
# SimonK adaptation of garrytan/gstack v1.91.9.0 freeze/bin/check-freeze.sh
# Base: the installed gstack 1.91.9 copy (upstream LF bytes sha256
# fa1ee8bf2e7d7d2bb95b3cf81b5bdd65967e9c92c9d9cd2eb90bdd94969c33b4).
# Copyright (c) 2026 Garry Tan. MIT terms and local delta: repository LICENSE.
# SimonK deltas (hub decision D-62 step A2, 2026-10-03). Everything else,
# including the two-line state format written by freeze-state.sh, is upstream:
#   1. Windows paths. Claude Code sends Edit/Write file_path as C:\...\file
#      (measured 2026-10-03). Upstream treated every path not starting with "/"
#      as relative and joined it to the hook cwd, so an edit OUTSIDE the
#      boundary was allowed whenever cwd was inside it. Both the boundary and
#      the payload path are now normalized the same way: C:\ and C:/ become
#      /c/ (cygpath -u, pure-bash fallback without cygpath), the parent
#      directory is resolved physically (cd + pwd -P), Git Bash mount aliases
#      (/tmp versus /c/Users/.../Temp) are folded with cygpath -am, and the
#      comparison is case-insensitive on Windows.
#   2. A path that cannot be judged is denied with a reason, never guessed:
#      relative, drive-relative (C:x) or root-relative (\x) paths, UNC and
#      device paths, a ".." segment, a failed conversion, a parent directory
#      that does not exist yet, a symlink loop, and a missing or non-string
#      file_path. There is no cwd fallback.
#   3. Only an ABSENT state file means "no freeze". A symlink, directory,
#      unreadable file, empty or control-character boundary, or a boundary
#      directory that no longer exists denies (upstream allowed an empty one).
#   4. Every helper function this script calls is checked before use.
# check-freeze.sh — PreToolUse hook for /freeze and /guard (Edit and Write).
# Reads the hook JSON from stdin and prints {} to allow, or a hookSpecificOutput
# with permissionDecision "deny". The decision MUST be nested under
# hookSpecificOutput — Claude Code ignores a top-level permissionDecision.
# Freeze is a DENY-tier hook: everything it cannot read or judge is denied.
set -euo pipefail
unset CDPATH

# Deny-tier backstop: an unexpected non-zero death would otherwise exit with
# no decision JSON, which Claude Code treats as non-blocking — the edit would
# proceed. Every deliberate output sets _FREEZE_DECIDED first.
_FREEZE_DECIDED=""
_freeze_backstop() {
  local rc=$?
  if [ "$rc" -ne 0 ] && [ -z "$_FREEZE_DECIDED" ]; then
    _FREEZE_DECIDED=1
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[freeze] Hook failed unexpectedly (exit %s) - blocked, fail closed. Way out: /unfreeze, or reinstall ~/.claude/skills/freeze."}}\n' "$rc"
    exit 0
  fi
}
trap _freeze_backstop EXIT

# Fixed ASCII text only (no quotes or backslashes in any caller's message):
# used before the JSON encoder in hook-extract.sh is known to be loadable.
_freeze_fail() {
  _FREEZE_DECIDED=1
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[freeze] %s - blocked, fail closed. Way out: /unfreeze, or reinstall ~/.claude/skills/careful and ~/.claude/skills/freeze."}}\n' "$1"
  exit 0
}

INPUT=$(cat)

# Shared JSON helpers (extractor + encoder) live in the sibling careful skill,
# as upstream. A missing/broken/outdated helper must fail CLOSED.
# NOTE: bash treats `.` on a MISSING file as fatal non-interactively — the
# existence check must come first.
_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../careful/bin/hook-extract.sh
_HOOK_HELPER="$_HOOK_DIR/../../careful/bin/hook-extract.sh"
if [ ! -f "$_HOOK_HELPER" ] || ! . "$_HOOK_HELPER" 2>/dev/null; then
  _freeze_fail "Hook helpers unavailable: careful/bin/hook-extract.sh is missing or broken"
fi
for _FN in gstack_hook_extract_field gstack_hook_decision gstack_hook_json_string \
           gstack_hook_log_fire gstack_hook_state_root; do
  command -v "$_FN" >/dev/null 2>&1 || _freeze_fail "Hook helpers out of date (partial upgrade?)"
done

_freeze_allow() {
  _FREEZE_DECIDED=1
  echo '{}'
  exit 0
}
# The reason is JSON-encoded by the shared helper. Never interpolate paths into
# hand-built JSON: a quote or newline would make the deny silently no-op.
_freeze_deny() {
  gstack_hook_decision deny "$1"
  _FREEZE_DECIDED=1
  exit 0
}

# Windows = Git Bash / MSYS / Cygwin. Elsewhere a drive path is just a
# relative name and is denied like any other relative path.
_FREEZE_WIN=0
case "${OSTYPE:-}" in msys*|cygwin*) _FREEZE_WIN=1 ;; esac
_FREEZE_CYGPATH=0
if [ "$_FREEZE_WIN" -eq 1 ] && command -v cygpath >/dev/null 2>&1; then
  _FREEZE_CYGPATH=1
fi

_freeze_trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

# _freeze_to_posix RAW
#   Absolute POSIX (MSYS on Windows) form of RAW in _FZ_POSIX, or a reason in
#   _FZ_WHY and return 1. Never consults the working directory.
_freeze_to_posix() {
  local raw="$1" norm out drive
  _FZ_POSIX=""
  _FZ_WHY=""
  if [ "$_FREEZE_WIN" -eq 1 ]; then norm="${raw//\\//}"; else norm="$raw"; fi
  case "/$norm/" in
    */../*) _FZ_WHY="the path has a '..' segment; use the resolved absolute path"; return 1 ;;
  esac
  if [ "$_FREEZE_WIN" -eq 1 ]; then
    case "$norm" in
      //*) _FZ_WHY="UNC and device paths are not supported"; return 1 ;;
      [A-Za-z]:/*)
        if [ "$_FREEZE_CYGPATH" -eq 1 ]; then
          out="$(cygpath -u -- "$raw" 2>/dev/null)" \
            || { _FZ_WHY="cygpath could not convert the Windows path"; return 1; }
        else
          drive="${norm%%:*}"
          out="/${drive,,}${norm#?:}"
        fi
        ;;
      [A-Za-z]:*) _FZ_WHY="drive-relative path (no separator after the drive letter)"; return 1 ;;
      /*)
        case "$raw" in
          /*) out="$norm" ;;
          *) _FZ_WHY="root-relative path (leading backslash without a drive letter)"; return 1 ;;
        esac
        ;;
      *) _FZ_WHY="relative path; freeze does not guess from the working directory"; return 1 ;;
    esac
    case "$out" in
      //*) _FZ_WHY="the converted path is a UNC path"; return 1 ;;
    esac
  else
    case "$raw" in
      /*) out="$raw" ;;
      *) _FZ_WHY="relative path; freeze does not guess from the working directory"; return 1 ;;
    esac
  fi
  case "$out" in
    /*) ;;
    *) _FZ_WHY="the conversion did not produce an absolute path"; return 1 ;;
  esac
  case "$out" in
    *[[:cntrl:]]*) _FZ_WHY="control characters in the converted path"; return 1 ;;
  esac
  while :; do
    case "$out" in
      *//*) out="${out//\/\//\/}" ;;
      *) break ;;
    esac
  done
  _FZ_POSIX="$out"
}

# _freeze_key POSIX
#   Comparison key in _FZ_KEY: a final symlink is followed (bounded, so the
#   TARGET is judged), the directory is resolved physically, mount aliases are
#   folded with cygpath -am, and the key is lower-cased on Windows. A new file
#   is judged by its parent, which must already exist. Reason in _FZ_WHY on
#   failure; never falls back to an unresolved prefix match.
_freeze_key() {
  local p="$1" dir base tgt i=0
  _FZ_KEY=""
  _FZ_WHY=""
  while [ -L "$p" ] && [ "$i" -lt 40 ]; do
    tgt="$(readlink -- "$p" 2>/dev/null)" || { _FZ_WHY="unreadable symlink"; return 1; }
    [ -n "$tgt" ] || { _FZ_WHY="unreadable symlink"; return 1; }
    case "$tgt" in
      /*) p="$tgt" ;;
      *) p="${p%/*}/$tgt" ;;
    esac
    i=$((i + 1))
  done
  [ ! -L "$p" ] || { _FZ_WHY="symlink chain too long or looping"; return 1; }
  if [ -d "$p" ]; then
    dir="$p"
    base=""
  else
    dir="${p%/*}"
    base="${p##*/}"
    [ -n "$dir" ] || dir="/"
  fi
  dir="$(cd -- "$dir" 2>/dev/null && pwd -P)" \
    || { _FZ_WHY="its parent directory does not exist (create it first, then retry)"; return 1; }
  if [ "$_FREEZE_CYGPATH" -eq 1 ]; then
    dir="$(cygpath -am -- "$dir" 2>/dev/null)" \
      || { _FZ_WHY="cygpath could not canonicalize the directory"; return 1; }
    case "$dir" in
      [A-Za-z]:/*) ;;
      *) _FZ_WHY="the directory is not on a drive letter (UNC is not supported)"; return 1 ;;
    esac
  fi
  if [ -z "$base" ]; then _FZ_KEY="$dir"; else _FZ_KEY="${dir%/}/$base"; fi
  if [ "$_FREEZE_WIN" -eq 1 ]; then _FZ_KEY="${_FZ_KEY,,}"; fi
}

# --- boundary state --------------------------------------------------------
# The writer (freeze-state.sh) and this reader resolve the same root through
# gstack_hook_state_root: ${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}.
STATE_DIR="$(gstack_hook_state_root; printf x)"; STATE_DIR="${STATE_DIR%x}"
FREEZE_FILE="$STATE_DIR/freeze-dir.txt"

# No state file at all: no freeze is active — allow.
if [ ! -e "$FREEZE_FILE" ] && [ ! -L "$FREEZE_FILE" ]; then
  _freeze_allow
fi
if [ ! -f "$FREEZE_FILE" ] || [ ! -r "$FREEZE_FILE" ] || [ -L "$FREEZE_FILE" ]; then
  _freeze_deny "[freeze] Invalid or unreadable boundary state ($FREEZE_FILE). Blocked (fail closed). Re-run /freeze or /unfreeze."
fi

FREEZE_DIR=""
FREEZE_OWNER_LINE=""
{
  IFS= read -r FREEZE_DIR || true
  IFS= read -r FREEZE_OWNER_LINE || true
} < "$FREEZE_FILE"
# freeze-state.sh writes the boundary verbatim plus an owner line; a legacy
# one-line state (older writers, the plugin runtime) is trimmed.
case "$FREEZE_OWNER_LINE" in
  gstack-freeze-v1:*) ;;
  *) FREEZE_DIR="$(_freeze_trim "$FREEZE_DIR")" ;;
esac
# A literal leading ~ never matches absolute tool paths — expand it here.
case "$FREEZE_DIR" in
  "~/"*) FREEZE_DIR="$HOME/${FREEZE_DIR#\~/}" ;;
  "~") FREEZE_DIR="$HOME" ;;
esac
if [ -z "$FREEZE_DIR" ]; then
  _freeze_deny "[freeze] The boundary state is empty ($FREEZE_FILE). Blocked (fail closed). Re-run /freeze or /unfreeze."
fi
case "$FREEZE_DIR" in
  *[[:cntrl:]]*)
    _freeze_deny "[freeze] The boundary state contains control characters ($FREEZE_FILE). Blocked (fail closed). Re-run /freeze or /unfreeze." ;;
esac
if ! _freeze_to_posix "$FREEZE_DIR"; then
  _freeze_deny "[freeze] The saved boundary is not a usable absolute directory ($_FZ_WHY): $FREEZE_DIR. The state was preserved. Re-run /freeze with an absolute directory chosen by the user, or /unfreeze."
fi
FREEZE_POSIX="$_FZ_POSIX"
if [ ! -d "$FREEZE_POSIX" ]; then
  _freeze_deny "[freeze] The boundary directory is unavailable: $FREEZE_DIR. Blocked (fail closed). Re-run /freeze or /unfreeze."
fi
if ! _freeze_key "$FREEZE_POSIX"; then
  _freeze_deny "[freeze] Could not resolve the boundary $FREEZE_DIR ($_FZ_WHY). Blocked (fail closed). Re-run /freeze or /unfreeze."
fi
FREEZE_KEY="$_FZ_KEY"
# Boundary as shown in deny reasons: the native Windows form when cygpath can
# produce it (state written by Git Bash may read /tmp/... for a Temp folder).
FREEZE_SHOWN="$FREEZE_DIR"
_freeze_shown() {
  local w
  if [ "$_FREEZE_CYGPATH" -eq 1 ] && w="$(cygpath -w -- "$FREEZE_POSIX" 2>/dev/null)" && [ -n "$w" ]; then
    FREEZE_SHOWN="$w"
  fi
}

# --- payload ---------------------------------------------------------------
# Strict extraction: a missing, empty, non-string, NUL or control-character
# file_path, invalid JSON, or no python3/node parser all return non-zero.
set +e
FILE_PATH=$(gstack_hook_extract_field "$INPUT" file_path)
EXTRACT_RC=$?
set -e
if [ "$EXTRACT_RC" -ne 0 ] || [ -z "$FILE_PATH" ]; then
  _freeze_shown
  _freeze_deny "[freeze] Could not read a usable file_path from the Edit/Write payload (invalid JSON, missing or non-string file_path, control characters, or no python3/node parser). Blocked (fail closed). Freeze boundary: $FREEZE_SHOWN"
fi
if ! _freeze_to_posix "$FILE_PATH"; then
  _freeze_shown
  _freeze_deny "[freeze] Blocked: $FILE_PATH cannot be checked against the freeze boundary ($FREEZE_SHOWN): $_FZ_WHY. Use an absolute path such as C:\\dir\\file or /c/dir/file."
fi
if ! _freeze_key "$_FZ_POSIX"; then
  _freeze_shown
  _freeze_deny "[freeze] Blocked: $FILE_PATH cannot be checked against the freeze boundary ($FREEZE_SHOWN): $_FZ_WHY."
fi
FILE_KEY="$_FZ_KEY"

# Inside the boundary (or the boundary itself): allow. The trailing / keeps
# /src from matching /src-old.
case "$FILE_KEY" in
  "${FREEZE_KEY%/}/"*|"${FREEZE_KEY%/}")
    _freeze_allow
    ;;
esac

# Outside: log the fire event (pattern name only; respects GSTACK_HOME) and deny.
gstack_hook_log_fire freeze boundary_deny
_freeze_shown
_freeze_deny "[freeze] Blocked: $FILE_PATH is outside the freeze boundary ($FREEZE_SHOWN). Only edits within the frozen directory are allowed."
