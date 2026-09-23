#!/usr/bin/env bash
# SimonK adaptation of garrytan/gstack@b9706f3635b6a545f46fae607ae9d6bcbfb69b91.
# Copyright (c) 2026 Garry Tan. MIT terms and local delta: repository LICENSE.
# hook-extract.sh — SHARED JSON helpers for gstack PreToolUse hooks.
# Sourced (never executed) by careful/bin/check-careful.sh and
# freeze/bin/check-freeze.sh via a path relative to each hook script.
#
# ONE copy on purpose. These two hooks previously carried separate extractor
# copies; the escaped-quote truncation bug got fixed in careful's copy while
# freeze silently kept the broken one. Any future parsing fix lands here and
# reaches both hooks by construction.

# gstack_hook_extract_field PAYLOAD FIELD
#   Prints a required nonempty string tool_input.FIELD. Missing/wrong-type
#   fields and NUL are invalid; file paths additionally reject control chars.
#   These hooks are bound to specific tool types.
#   Returns 1 when no parser is available or input is invalid — the CALLER decides the
#   polarity for that case (careful asks, freeze denies).
#
#   python3 is tried first because it ships with macOS and most Linux distros
#   and is reliably on PATH in a hook environment; node is the fallback.
gstack_hook_extract_field() {
  _ghef_payload="$1"
  _ghef_field="$2"
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "$_ghef_payload" | python3 -c 'import sys,json
field = sys.argv[1]
d = json.loads(sys.stdin.read())
c = d.get("tool_input", {}).get(field, "")
if not isinstance(c, str) or not c or "\0" in c: sys.exit(1)
if field == "file_path" and any(ord(ch) < 32 or ord(ch) == 127 for ch in c): sys.exit(1)
sys.stdout.write(c)' "$_ghef_field" 2>/dev/null && return 0
  fi
  if command -v node >/dev/null 2>&1; then
    printf '%s' "$_ghef_payload" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const j=JSON.parse(s);const f=process.argv[1];const c=j&&j.tool_input&&j.tool_input[f];if(typeof c!=="string"||!c||c.includes("\0")||(f==="file_path"&&/[\x00-\x1f\x7f]/.test(c)))process.exit(3);process.stdout.write(c)}catch(e){process.exit(3)}})' "$_ghef_field" 2>/dev/null && return 0
  fi
  return 1
}

# gstack_hook_json_string TEXT
#   Prints TEXT as a JSON string literal (surrounding quotes included),
#   encoding quotes, backslashes, control characters and newlines. Never build
#   hook JSON with printf/sed interpolation: a path containing a quote or a
#   newline produces malformed JSON, and Claude Code silently ignores the
#   whole decision — a deny that no-ops exactly when it matters.
gstack_hook_json_string() {
  _ghjs_text="$1"
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "$_ghjs_text" | python3 -c 'import sys,json; sys.stdout.write(json.dumps(sys.stdin.read()))' 2>/dev/null && return 0
  fi
  if command -v node >/dev/null 2>&1; then
    printf '%s' "$_ghjs_text" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>process.stdout.write(JSON.stringify(s)))' 2>/dev/null && return 0
  fi
  # Last-resort fallback (no parser on PATH): strip to a safe charset so the
  # envelope stays valid JSON even if the message loses characters.
  printf '"%s"' "$(printf '%s' "$_ghjs_text" | tr -cd 'a-zA-Z0-9 ._/:@=+-' )"
}

# gstack_hook_decision DECISION REASON
#   Emits the full PreToolUse hookSpecificOutput envelope with REASON safely
#   JSON-encoded. DECISION is "ask" or "deny". The decision MUST be nested
#   under hookSpecificOutput — Claude Code ignores a top-level
#   permissionDecision, which silently no-ops the block.
gstack_hook_decision() {
  _ghd_decision="$1"
  _ghd_reason="$2"
  _ghd_encoded=$(gstack_hook_json_string "$_ghd_reason")
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"%s","permissionDecisionReason":%s}}\n' "$_ghd_decision" "$_ghd_encoded"
}

# gstack_hook_state_root
#   SimonK writers currently use ${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}.
#   Match that expression exactly; upstream GSTACK_HOME / plugin-name logic
#   silently misses a boundary written by the current SimonK skills.
#   This fixes reader/writer parity WITHIN one state root, not state sharing
#   between Core and Stack or session lifecycle/ownership. Those remain open.
#   No trailing newline, so the caller's sentinel preserves the full root.
gstack_hook_state_root() {
  printf '%s' "${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}"
}

# gstack_hook_log_fire SKILL PATTERN
#   Append a hook_fire analytics record (pattern name only, never command
#   content). Respects GSTACK_HOME so tests never pollute the operator's real
#   analytics file. Deliberately NOT gstack_hook_state_root: every other
#   analytics writer and reader (gstack-skill-start, gstack-retro-metrics,
#   gstack-analytics) uses this two-step chain, and the usage log must stay one
#   file. Best-effort: failures never affect the hook decision.
gstack_hook_log_fire() {
  _ghlf_dir="${GSTACK_HOME:-$HOME/.gstack}/analytics"
  mkdir -p "$_ghlf_dir" 2>/dev/null || true
  # Fields are JSON-encoded (a repo basename can carry quotes/backslashes) —
  # same rule this file states for decisions: never raw-interpolate into JSON.
  _ghlf_repo=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")
  printf '{"event":"hook_fire","skill":%s,"pattern":%s,"ts":"%s","repo":%s}\n' \
    "$(gstack_hook_json_string "$1")" \
    "$(gstack_hook_json_string "$2")" \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "$(gstack_hook_json_string "$_ghlf_repo")" >> "$_ghlf_dir/skill-usage.jsonl" 2>/dev/null || true
}
