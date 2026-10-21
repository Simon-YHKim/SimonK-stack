#!/usr/bin/env bash
# Vendored from garrytan/gstack v1.91.9.0 freeze/bin/freeze-state.sh, unchanged
# except for this leading attribution block and the code between the
# "# >>> SimonK delta" and "# <<< SimonK delta" markers (hub D-119, 2026-10-21:
# retire a boundary left under the old $HOME/.gstack home default). Source: the installed gstack 1.91.9
# copy (upstream LF bytes sha256
# ee14660e8dd6fedb1e6673fccffa9ff1740047955ef5b59d58d246ad1dccebf5).
# Copyright (c) 2026 Garry Tan. MIT terms: repository LICENSE.
# SimonK use (hub decision D-62, 2026-10-03): the one state writer for /freeze,
# /guard and /unfreeze. "set DIR" resolves DIR with cd + pwd -P and atomically
# writes "<dir>" plus a "gstack-freeze-v1:<owner>" line under a mkdir mutex;
# "clear" removes the state. A held mutex exits 1 with FREEZE_BUSY on stderr
# and changes nothing. It sources ../../careful/bin/hook-extract.sh for the
# state root ${CLAUDE_PLUGIN_DATA:-$HOME/.simonk/state}, the same root
# check-freeze.sh reads.
set -euo pipefail

_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$_here/../../careful/bin/hook-extract.sh"
STATE_DIR="$(gstack_hook_state_root; printf x)"; STATE_DIR="${STATE_DIR%x}"
mkdir -p "$STATE_DIR"
STATE_DIR="$(cd "$STATE_DIR" && pwd -P && printf x)"; STATE_DIR="${STATE_DIR%$'\nx'}"
state="$STATE_DIR/freeze-dir.txt"
mutex="$STATE_DIR/.freeze-mutation.lock"
action="${1:-}"
case "$action" in acquire|set|release|clear) ;; *) echo 'Usage: freeze-state.sh acquire|set DIRECTORY | release OWNER | clear' >&2; exit 2 ;; esac

if ! mkdir "$mutex" 2>/dev/null; then
  echo 'FREEZE_BUSY: another writer or an interrupted mutation owns the state lock. Retry after it finishes; if abandoned, inspect it with the user before recovery. No boundary changed.' >&2
  exit 1
fi
temp=""
finish() {
  local rc=$?
  [ -z "$temp" ] || rm -f -- "$temp"
  rmdir "$mutex"
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [ "$action" = acquire ] && { [ -e "$state" ] || [ -L "$state" ]; }; then
  echo 'FREEZE_PRESERVED: an existing boundary belongs to the user or another run. Do not release it; use /freeze to re-establish an ambiguous legacy boundary with the user.'
  exit 0
fi
if [ -L "$state" ] || { [ -e "$state" ] && [ ! -f "$state" ]; }; then
  echo 'FREEZE_PRESERVED: unexpected state type; inspect it with the user before recovery.' >&2
  exit 1
fi
# >>> SimonK delta (hub D-119, 2026-10-21): legacy $HOME/.gstack boundary.
# check-freeze.sh still honors a boundary left under the old home default while
# this root holds none, so acquire preserves it and clear retires it first.
legacy=""
if legacy="$(gstack_hook_legacy_freeze_file)"; then
  legacy_dir="$(cd "$(dirname -- "$legacy")" && pwd -P && printf x)"; legacy_dir="${legacy_dir%$'\nx'}"
  [ "$legacy_dir" != "$STATE_DIR" ] || legacy=""
else
  legacy=""
fi
if [ -n "$legacy" ]; then
  if [ "$action" = acquire ]; then
    echo 'FREEZE_PRESERVED: a boundary from the old ~/.gstack location is still active. Do not release it; use /freeze to re-establish it with the user or /unfreeze to clear it.'
    exit 0
  fi
  if [ "$action" != release ] && { [ -L "$legacy" ] || [ ! -f "$legacy" ]; }; then
    echo 'FREEZE_PRESERVED: unexpected state type in the old ~/.gstack location; inspect it with the user before recovery.' >&2
    exit 1
  fi
  [ "$action" != clear ] || rm -f -- "$legacy"
fi
# <<< SimonK delta
case "$action" in
  acquire|set)
    boundary="$(cd -- "${2:?Directory required}" && pwd -P && printf x)"; boundary="${boundary%$'\nx'}"
    case "$boundary" in *$'\n'*|*$'\r'*) echo 'FREEZE_ERROR: boundary must fit on one line.' >&2; exit 2 ;; esac
    owner="$(od -An -N16 -tx1 /dev/urandom | tr -d '[:space:]')"
    [ "${#owner}" -eq 32 ] || exit 1
    temp="$(mktemp "$STATE_DIR/.freeze-write.XXXXXX")"
    printf '%s\ngstack-freeze-v1:%s\n' "$boundary" "$owner" > "$temp"
    mv -f -- "$temp" "$state"
    temp=""
    printf 'FREEZE_OWNER=%s\nFREEZE_DIR=%s\n' "$owner" "$boundary"
    ;;
  release)
    owner="${2:?Owner required}"
    case "$owner" in ''|*[!a-f0-9]*) echo 'FREEZE_ERROR: invalid owner token.' >&2; exit 2 ;; esac
    [ "${#owner}" -eq 32 ] || exit 2
    if [ -f "$state" ] && [ "$(sed -n '2p' "$state")" = "gstack-freeze-v1:$owner" ]; then
      rm -- "$state"
      echo 'FREEZE_RELEASED: investigation-owned boundary removed.'
    else
      echo 'FREEZE_PRESERVED: no matching owner; existing or replacement state was left untouched.'
    fi
    ;;
  clear)
    rm -f -- "$state"
    echo 'FREEZE_CLEARED: user-requested edit boundary removal completed.'
    ;;
esac
# >>> SimonK delta (hub D-119): a successful set replaces the legacy boundary,
# so it cannot resurface after a later clear or release.
if [ -n "$legacy" ] && [ "$action" = set ]; then
  rm -f -- "$legacy" || echo 'FREEZE_NOTE: the old ~/.gstack boundary could not be removed; the new boundary takes precedence.' >&2
fi
# <<< SimonK delta
