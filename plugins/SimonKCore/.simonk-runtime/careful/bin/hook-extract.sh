#!/usr/bin/env bash
# SimonK adaptation of garrytan/gstack v1.91.9.0 careful/bin/hook-extract.sh
# Upstream commit for v1.91.9.0: 96764e80a641e28141ec8297223768029f5bf483.
# (upstream LF bytes sha256 5be66386d4945f27ba52ac3df720a8f84755634de1713eacbd239376050106c9,
# byte-identical to the earlier pin b9706f3635b6a545f46fae607ae9d6bcbfb69b91).
# Copyright (c) 2026 Garry Tan. MIT terms and local delta: repository LICENSE.
# SimonK deltas (everything else is upstream):
#   - gstack_hook_extract_field is STRICT: missing/empty/wrong-type field or NUL
#     returns 1 (upstream printed "" and returned 0). freeze relies on this.
#   - gstack_hook_extract_tool_name (new, additive): lets careful tell a non-Bash
#     payload from a Bash payload whose command is missing.
#   - gstack_hook_state_root uses the SimonK writer expression
#     ${CLAUDE_PLUGIN_DATA:-$HOME/.gstack} (shared with freeze).
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
#   polarity for that case (careful denies, freeze denies).
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

# gstack_hook_extract_tool_name PAYLOAD   (SimonK addition)
#   Prints the top-level tool_name ("" when absent or null). Returns 1 when no
#   parser is available, the payload is not a JSON object, or tool_name is not
#   a string. Upstream careful treated "no command field" as "not a Bash call"
#   and allowed it; that also let a Bash payload WITHOUT a command through.
#   tool_name is what actually identifies the tool.
gstack_hook_extract_tool_name() {
  _ghtn_payload="$1"
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "$_ghtn_payload" | python3 -c 'import sys,json
d = json.loads(sys.stdin.read())
if not isinstance(d, dict): sys.exit(1)
t = d.get("tool_name")
if t is None: t = ""
if not isinstance(t, str) or "\0" in t: sys.exit(1)
sys.stdout.write(t)' 2>/dev/null && return 0
  fi
  if command -v node >/dev/null 2>&1; then
    printf '%s' "$_ghtn_payload" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const j=JSON.parse(s);if(j===null||typeof j!=="object"||Array.isArray(j))process.exit(3);let t=j.tool_name;if(t===undefined||t===null)t="";if(typeof t!=="string"||t.includes("\0"))process.exit(3);process.stdout.write(t)}catch(e){process.exit(3)}})' 2>/dev/null && return 0
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
