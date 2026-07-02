# agy-pty — headless Antigravity (agy) via ConPTY

**Problem.** `agy -p "<prompt>"` only renders its answer when attached to a real
terminal. When the hub daemon spawns it with redirected stdout (to capture the
reply), agy emits ~0 useful bytes — it has no stdout/log/json output contract.
This silently killed the Antigravity hub seat headless.

**Fix.** `agy-headless.js` spawns agy inside a **node-pty pseudo-terminal
(ConPTY)**, lets it render, strips the TUI chrome, and prints the clean answer to
real stdout. Verified working 2026-06-15 (Node v24.14.1, node-pty prebuild,
agy 1.0.8): 4/5 probe configs returned the answer; single- and multi-word
answers extract cleanly.

## Usage
```bash
node tools/agy-pty/agy-headless.js "<prompt>"
# env: AGY_MODEL, AGY_CWD, AGY_TIMEOUT_MS (default 90000), AGY_TRIES (default 3),
#      AGY_BIN (full path to agy.exe), AGY_RAW_DUMP (debug)
```

## Daemon integration (hub-daemon.ps1 antigravity lane)
Replace the dead gemini spawn:
```powershell
# OLD (line ~138): $env:GEMINI_CLI_TRUST_WORKSPACE='true'; gemini -m $am -p $prompt -y
# NEW:
$env:AGY_CWD = $repo
$env:AGY_MODEL = $am            # e.g. the agy model label, or leave unset for default
$resp = node "$PSScriptRoot\agy-pty\agy-headless.js" $prompt
```
Then `models.json` antigravity `spawn_flags` / CLI ref should point at this
wrapper instead of `gemini -m gemini-3.1-pro-preview` (which dies 2026-06-18).

## Gotchas (learned)
- node-pty on Windows needs the **full agy.exe path** (no PATH resolution) — the
  wrapper resolves via `where agy`.
- Do **NOT** set `conptyInheritCursor:true` — crashes node-pty (`AttachConsole failed`).
- Do **NOT** kill on output-idle — agy goes silent for ~5s while "thinking" before
  printing; an idle-kill truncates to the 104-byte terminal-setup preamble only.
  Rely on the process exiting on its own (agy -p exits after printing).
- First call can flake to an empty render (cold start) → the wrapper retries (AGY_TRIES).
