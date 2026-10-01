# Vendor seats — invocation, readiness, $0 guard

One seat per vendor. `scripts/debate.py seats` checks readiness with no model call; `call`
re-checks right before spawning and never spawns a seat that is not READY (UNKNOWN only with
`--accept-unknown`). Paid fallback is the failure this file guards against.

## Contents

- Shared rules — workdir, env scrub, process control, lock, shims, exit codes, meta
- Claude (anthropic) — in-session seat, headless UNKNOWN
- Codex (openai)
- Grok (xai)
- Gemini (google, Antigravity CLI `agy`) — command-line limit, zero-turn probe
- Absence handling — attendance, catch-up, judge choice, interject cards
- Test hooks

| Seat | Display | Default model · effort | Prompt channel |
|---|---|---|---|
| anthropic | Claude | claude-opus-5-5 · max | in-session subagent + `submit` when Claude orchestrates; else stdin to `claude -p` (UNKNOWN by default) |
| openai | Codex | gpt-6.1-sol · xhigh | stdin (`-`); answer read from the `-o` file |
| xai | Grok | grok-4.7 · xhigh | `--prompt-file` (UTF-8 `.txt`) |
| google | Gemini via `agy` | gemini-3.1-pro-high | argv after `--print`; the command line is kept at or under 32000 UTF-16 units |

## Shared rules

- cwd is a fresh, empty `<state>/work/<id>/<round>-<vendor>/`, outside the debate folder, so no relative path reaches the round files or the P-label map. Codex refuses a workdir with a `.git` ancestor.
- Child env drops every billing switch, matched case-insensitively. It adds `NO_COLOR=1`. Auth homes such as `CODEX_HOME` and `GROK_HOME` stay. Dropped names:
  - suffixes `*_API_KEY`, `*_AUTH_TOKEN`, `*_ACCESS_TOKEN`, `*_BASE_URL`;
  - prefixes `CLAUDE_CODE_USE_*`, `ANTHROPIC_*`, `OPENAI_*`, `XAI_*`, `GROK_CODE_*`, `GATEWAY_*`, `GOOGLE_GENAI_USE_*`, `AWS_*`, `AZURE_OPENAI_*`;
  - exact names `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`.
- Process control:
  - Timeout kills the whole process tree (Windows `taskkill /T /F /PID`, POSIX process-group SIGKILL).
  - On Windows the child also runs in a Job Object with `KILL_ON_JOB_CLOSE`, so it dies with a killed runner. On Linux the direct child gets `PR_SET_PDEATHSIG`.
- One call per (round, vendor) at a time.
  - `<round>/<vendor>.lock` holds the runner pid, and meta shows `running` with `pid` and `child_pid`. A second `call` while that pid lives exits 2.
  - A lock whose pid is dead (or reused) is stale and the call may be retried.
- `.cmd`/`.bat` shims:
  - Gemini (prompt in argv) and orca (card text in argv) never run through one. A shim that names a native `.exe` is followed to it.
  - Otherwise the Gemini seat is UNKNOWN with `shim refused`: `call` exits 4 (failed) and `judge-pick` skips it. `deliver --send` writes `deliver.json` with status failed and exits 4.
  - The Codex npm shim is followed to the vendored `codex.exe` the same way.
- Exit codes: 0 ok · 3 absent (readiness or quota) · 4 failed · 2 usage error or refusal. Quota wording inside a successful answer is content, not a failure.
- `AI_DEBATE_MAX_USED` (default 95; non-finite or <= 0 falls back to 95; capped at 100) is the spent threshold for Codex, Grok and the Claude bridge.
- Every `meta.json` keeps:
  - the redacted argv, model, effort, rc, times, status, reason, session id and workdir;
  - prompt truncation, `cmdline_chars` and the input fingerprint (`inputs`).
- `call` rebuilds the prompt from current answers on every run.
- `submit`:
  - accepts only the orchestrator's vendor;
  - refuses (exit 2, "re-run prompt") when the answers behind its prompt changed;
  - requires a UTF-8 answer file with no NUL.

## Claude (anthropic)

- Claude orchestrates: `call` refuses. Run an in-session subagent on `rounds/<round>/anthropic.prompt.md`, then `submit --file`. Interactive usage is exempt from headless metering.
- Another vendor orchestrates:
  - Invocation: `claude --safe-mode --strict-mcp-config --tools "" --permission-prompts none --no-session-persistence --model M --effort E --output-format json -p "Follow only the task supplied via standard input."`, with the prompt on stdin.
  - Reads `{type: "result", is_error, result, session_id}`.
- Readiness: in-session is READY. Otherwise the CLI must exist, and the seat is **UNKNOWN**, never READY.
  - Headless `claude -p` draws the separate headless credit, which no local file shows. `call` needs `--accept-unknown`, and `judge-pick` skips the seat without it.
  - It is ABSENT when the newest AI Usage Widget bridge shows `five_hour` or `seven_day` `used_percentage >= AI_DEBATE_MAX_USED` with a future `resets_at`.
  - Bridge location: `%LOCALAPPDATA%/AIUsageWidget/bridge/claude/<hash>.json`, newest `capturedAt`; `*.wrap.json` and `default-profile.json` are ignored.
  - A missing bridge, or one captured more than 6h ago, stays UNKNOWN.
- $0 caution: accept the UNKNOWN headless seat only when Simon allows that credit. Prefer the in-session seat.
- Failure: `is_error: true` is failed, or absent when it carries a usage-limit message.

## Codex (openai)

- Invocation: `codex exec --ephemeral --ignore-user-config --skip-git-repo-check --sandbox read-only -C <work> -m M -c model_reasoning_effort="E" -o <round>/openai.last.txt -`.
  - `--ignore-user-config` drops the user's `service_tier="priority"`, full-access sandbox and MCP servers.
- Readiness evidence: the 3 newest `$CODEX_HOME/sessions/**/rollout-*.jsonl` by mtime, last 4 MB of each (files reach ~900 MB). The latest `event_msg` / `token_count` `rate_limits` gives `primary`/`secondary` `used_percent`, `resets_at` and `credits.has_credits`.
  - `resets_at` passed → READY ("window reset since snapshot").
  - used ≥ threshold → ABSENT until reset; with `has_credits` the reason adds "further calls would bill purchased credits".
  - no record → UNKNOWN.
- $0 guard: a spent Codex window silently bills purchased credits, so ABSENT never spawns.
- Failure → absent: "usage limit", HTTP 402 or 429, "rate limit"/`rate_limit_exceeded`, "quota" or "add credits".
- Other non-zero exits are failed. The session id comes from `session id: <uuid>`.

## Grok (xai)

- Invocation: `grok --no-auto-update --cwd <work> --prompt-file <prompt.txt> --verbatim --output-format plain --session-id <uuid4> --model M --reasoning-effort E --max-turns 1 --no-subagents --disable-web-search --tools "" --disallowed-tools Agent --deny MCPTool --sandbox read-only`. Never pass `-p` together with `--single`.
- Readiness evidence: last `billing: fetched credits config` line in `~/.grok/logs/unified.jsonl` (last 4 MB): `ctx.config.creditUsagePercent`, `currentPeriod.end`, `onDemandCap`, `prepaidBalance`.
  - period end passed → READY.
  - percent ≥ threshold → ABSENT "HTTP 402 expected until <end KST>"; a non-zero on-demand cap or prepaid balance adds a billing warning.
  - no line → UNKNOWN.
- Failure: `API error (status 402 Payment Required): Grok Build usage balance exhausted` or a 429 / rate-limit line → absent.

## Gemini (google, Antigravity CLI `agy`)

- Invocation: `agy --print <prompt> --model M --mode plan --sandbox --output-format json --print-timeout <timeout-30>s` with `AGY_CLI_DISABLE_AUTO_UPDATE=1` and `NO_COLOR=1`.
  - Do not add `--disable-slash-commands` (it voids `--mode plan`). Meta stores the prompt argv as `<prompt:N chars>`.
- Command-line limit:
  - The 24000-char prompt cap alone does not fit Windows: quotes double when quoted. Before spawning, `call` measures `subprocess.list2cmdline(argv)` in UTF-16 units.
  - Above 32000 it rebuilds the prompt with a smaller cap, which truncates the evidence and positions with markers. If the prompt cannot shrink to fit, the call fails with a clear reason.
- Readiness: zero-turn probe `agy -p /usage --output-format json --print-timeout 40s` (no model call, ~9 s, 60 s timeout, private temp folder per probe).
  - The probe must report `num_turns: 0`.
  - `command.data.groups[name="Gemini Models"]` must hold both the `weekly` and the `5h` bucket.
  - agy omits `remaining_fraction` when it is 0 (Go `omitempty`), so a bucket without the field counts as spent.
  - Minimum fraction > 0 → READY; 0 → ABSENT until the latest exhausted `reset_time`.
  - A missing bucket, `num_turns != 0`, a probe failure or `--no-probe` → UNKNOWN.
- Answer: `response` of the JSON envelope; `conversation_id` is the session id.
- Failure:
  - exit 3 with a stderr line starting `AGY_ERROR:` → failed;
  - `status` other than `SUCCESS` → failed;
  - `--print-timeout` expiry (exit 0 plus a stderr warning) → failed "partial", with the text kept in `.partial.md`.

## Absence handling

- A seat that is not READY: `call` writes `meta {status: "absent", reason}` and exits 3 without spawning.
- Attendance = vendors with an ok r1. 4/4 plus a valid judge → FINAL; 2-3 → PROVISIONAL with a catch-up duty in the record; fewer than 2 → INVALID, which cannot gate a §35 decision.
  - A valid judge answer has a `VERDICT:` line (`CALL:` in interject) and saw as many positions as attended.
  - Once the judge answered, `r1` and `r2` are closed.
- `catchup` lists PROVISIONAL debates whose absent vendor is READY again, with the exact `prompt --round catchup` and `call` (or `submit`) commands, then `record --amend`.
  - The returning vendor answers ACCEPT or OBJECT.
  - Present r1 vendors plus catch-up ACCEPT vendors reaching 4 (no OBJECT, nothing unreadable, valid judge) promotes the debate to FINAL with `via: catch-up`.
  - An OBJECT sets `blocked`. A first line that is neither ACCEPT nor OBJECT is listed in `unresolved` and blocks FINAL.
- Judge: `judge-pick` walks a rotation seeded by the debate id.
  - It skips the orchestrator, the interject `--subject-vendor`, vendors that hit quota in this debate, shimmed seats, and UNKNOWN seats unless `--accept-unknown`.
  - None left → the orchestrator's vendor in a fresh session, marked `same-vendor`.
  - The judge prompt says one anonymized position may come from the judge's own vendor; meta records `judge_wrote_position` and `positions_count`.
- Interject cards go out only with both `deliver --orca-terminal HANDLE` and `--send`; otherwise `deliver` prints the orca command as a dry run. Control and bidi characters are stripped from the card and the argv text.

## Test hooks

- `AI_DEBATE_CMD_<VENDOR>` and `AI_DEBATE_CMD_ORCA`: JSON argv prefix; `[]` means absent.
- `AI_DEBATE_CODEX_SESSIONS`, `AI_DEBATE_GROK_LOG`, `AI_DEBATE_CLAUDE_BRIDGE`: evidence locations.
- `AI_DEBATE_HOME`: state root.
- `AI_DEBATE_NOW` (ISO-8601) is honoured only when `AI_DEBATE_TEST=1`.
- Tests use fake CLIs only; no vendor is called.
