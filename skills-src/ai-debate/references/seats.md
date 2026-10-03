# Vendor seats — invocation, readiness, $0 guard

One seat per vendor. `scripts/debate.py seats` checks readiness with no model call; `call`
re-checks right before spawning and never spawns a seat that is not READY (UNKNOWN only with
`--accept-unknown`). Paid fallback is the failure this file guards against.

## Contents

- Shared rules — workdir, env scrub, process control, lock, shims, exit codes, meta
- Host and host-session proof — any CLI hosts; another vendor's live session answers its own seat
- Claude (anthropic) — headless UNKNOWN
- Codex (openai)
- Grok (xai)
- Gemini (google, Antigravity CLI `agy`) — command-line limit, zero-turn probe
- Absence handling — attendance, catch-up, judge choice, interject cards
- Interject scan sources — Codex, Claude Code, Grok CLI, agy
- Test hooks

| Seat | Display | Default model · effort | Prompt channel |
|---|---|---|---|
| anthropic | Claude | claude-opus-5-5 · max | stdin to `claude -p` (UNKNOWN by default) |
| openai | Codex | gpt-6.1-sol · xhigh | stdin (`-`); answer read from the `-o` file |
| xai | Grok | grok-4.7 · xhigh | `--prompt-file` (UTF-8 `.txt`) |
| google | Gemini via `agy` | gemini-3.1-pro-high (effort = model-name suffix) | argv after `--print`; the command line is kept at or under 32000 UTF-16 units |

Whichever vendor hosts (`--orchestrator`) answers its own seat in-session and registers it with `submit`;
that seat is never spawned. `--model` and `--effort` pass through to `call`; for agy the effort
replaces the model-name suffix (`--effort low` → `gemini-3.1-pro-low`) and no `--effort` flag is sent.

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
  - accepts the orchestrator's vendor, or another vendor with a proven `--host-session` (next section);
  - refuses (exit 2, "re-run prompt") when the answers behind its prompt changed;
  - refuses (exit 2) a session id that already answered another vendor's seat in this debate, including the host's `--session` label;
  - requires a UTF-8 answer file with no NUL;
  - records `model` as given by `--model`, else `미신고` (`model_declared: false`), in meta and in the record line;
  - for Codex and Grok (host seat or host session) re-reads the quota evidence first: spent → meta `absent`, exit 3, nothing registered.
- Every prompt carries `- 입력 지문: <sha256>` in its seat card, and `prompt` prints it as `inputs_sha256`. It hashes the debate id, round, vendor and the answers the prompt quotes, so even an r1 prompt has its own value. Prompts written before this salt existed fail `submit` with "re-run prompt"; run `prompt` again.

## Host and host-session proof

- `seats`, `new` and `catchup` require `--orchestrator` (Claude Code `anthropic`, Codex `openai`, Grok CLI `xai`, agy `google`); without it they print that table and exit 2. Stored debates keep their orchestrator.
- Host markers (env the host CLI exports to its shells): Claude Code `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT` (seen in this environment); Codex `CODEX_THREAD_ID`, `CODEX_SANDBOX` (a local note of a live `codex exec` env capture, 0.147.0; both names are in codex.exe 0.155.0). Grok and agy exports are unconfirmed: `GROK_*`, `ANTIGRAVITY_*`, `AGY_*` names are recorded without values and decide nothing.
  - `new` stores `host_env {vendors, values, other_names}` and `orchestrator_override` in `agenda.json`.
  - When the markers name exactly one vendor and it is not `--orchestrator`, `new` and `catchup` exit 2 unless `--orchestrator-override` (inherited markers). Markers of two vendors (nested CLIs) are ambiguous and only recorded.
  - A plain `submit` (no `--host-session`) of the stored host's seat from a shell whose markers name another vendor exits 2, unless the debate was opened with the override.
- The host's vendor seat is READY `in-session (host vendor)`: no spawn, `call` exits 2. `judge-pick` falls back to it as `same-vendor`, `in_session: true` (a fresh subagent where the host has one).
  - Codex and Grok hosts spend their own subscription in-session, so the row carries their quota evidence (`evidence`, `quota`). Spent → ABSENT, `host_over_quota: true`, reason "WARNING the host is over quota", short `호스트 쿼터 …`. Claude and agy host rows are not gated.
- `submit --vendor V --host-session ID` (V not the host, or the host proving its own session) is accepted only when every check below passes; each one fails closed (exit 2):

| Vendor | Transcript | Root override |
|---|---|---|
| anthropic | `~/.claude/projects/*/<ID>.jsonl` | `AI_DEBATE_CLAUDE_PROJECTS` (else `CLAUDE_CONFIG_DIR`/projects) |
| openai | `~/.codex/sessions/**/rollout-<time>-<ID>.jsonl` (exact UUID) | `AI_DEBATE_CODEX_SESSIONS` (else `CODEX_HOME`/sessions) |
| xai | `~/.grok/sessions/*/<ID>/updates.jsonl` | `AI_DEBATE_GROK_SESSIONS` (else `GROK_HOME`/sessions) |
| google | `~/.gemini/antigravity-cli/brain/<ID>/.system_generated/logs/transcript.jsonl` | `AI_DEBATE_AGY_BRAIN` |

  1. ID is 8-128 of `A-Z a-z 0-9 . _ -` (alphanumeric first); a Codex ID is the whole rollout UUID and the file name must end with `-<ID>.jsonl`.
  2. Live: the transcript was written within the last 30 minutes (at most 5 minutes in the future).
  3. Interactive, by positive evidence only. Values were confirmed on this PC's own transcripts (bounded reads, 2026-10-02): Claude (all) `cli` 170 · `sdk-cli` 58 · `claude-desktop` 4 · none 2; Codex (`CODEX_HOME` rollouts, last 30 days) `cli` 165 · `vscode` 6 · `exec` 60 · `{subagent}` 815; Grok (all) 16 without `session_kind` · 16 `headless`.
     - Claude: the first record carrying `entrypoint`, read line by line within 2000 lines / 4 MB, is `cli` or `claude-desktop`. `sdk-*` (`claude -p`), an unconfirmed value (e.g. `claude-vscode`), an empty file or no entrypoint is refused.
     - Codex: the first line is `session_meta` with `source` `cli` or `vscode` and `thread_source` not `subagent`. `exec`, `mcp`, `{subagent}` or a missing source is refused.
     - Grok: `summary.json` is readable and has no `session_kind`. A missing summary, `headless` or any other value is refused.
     - agy: `history.jsonl` next to `brain` lists the conversation id (`history_listed: true`); a one-shot `agy --print` run is not listed.
  4. Bound to this answer: the session's own record holds this prompt's input fingerprint (it ran `prompt` or read the prompt file) or the answer's first 200 characters (whitespace-normalized, at least 40). Searched: the transcript's last 16 MB; for Claude also the newest 64 files under `<projects>/*/<ID>/` (subagents, tool-results), 2 MB each, 48 MB in all. JSON strings are decoded, and JSON-encoded strings inside them are unwrapped once.
- Meta keeps `cli: in-session`, `host_session`, `session_id`, `host_vendor` and `host_session_evidence {vendor, path, modified_at, age_min, interactive, bound_by, bound_in}` (+ `history_listed` for agy).
- A borrowed session id fails step 4 unless that session itself produced this prompt or answer. A host must still not relay another vendor's answer through that vendor's session.

## Claude (anthropic)

- Claude Code hosts: `call` refuses (host seat). Run an in-session subagent on `rounds/<round>/anthropic.prompt.md`, then `submit --file`. Interactive usage is exempt from headless metering.
- Another vendor hosts:
  - A live Claude Code session may answer with `submit --host-session` (above).
  - Invocation: `claude --safe-mode --strict-mcp-config --tools "" --permission-prompts none --no-session-persistence --model M --effort E --output-format json -p "Follow only the task supplied via standard input."`, with the prompt on stdin.
  - Reads `{type: "result", is_error, result, session_id}`.
- Readiness: as host, in-session READY. Otherwise the CLI must exist, and the seat is **UNKNOWN**, never READY.
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
- Readiness evidence, live first: `grok agent --no-leader stdio` (ACP, JSON-RPC lines) → `initialize` (protocolVersion 1, fs and terminal off) → `_x.ai/billing` (`x.ai/billing` on -32601). No prompt, no model turn; server notifications and requests are ignored, never answered; the process tree is killed afterwards (25 s cap). Reply: `config.creditUsagePercent`, `config.currentPeriod.end`, `onDemandCap`, `prepaidBalance`, `subscription_tier`.
  - Fallback only when the probe fails or `--no-probe`: last `billing: fetched credits config` line in `~/.grok/logs/unified.jsonl` (last 4 MB, same `ctx.config` fields). Grok writes that line only when one of its own sessions starts, so usage from elsewhere is invisible to it — 2026-10-03 the newest line said 78% while the account was at 100% and the call hit 402.
  - period end passed → READY.
  - percent ≥ threshold → ABSENT "HTTP 402 expected until <end KST>"; a non-zero on-demand cap or prepaid balance adds a billing warning. This holds for a stale line too.
  - a logged line older than 10 minutes below the threshold → UNKNOWN ("usage may have grown since"), never READY.
  - no line → UNKNOWN.
  - `evidence.live_probe` is `ok`, `failed: …` or `skipped (--no-probe)`; `evidence.stale` marks an old logged line.
- Failure: `API error (status 402 Payment Required): Grok Build usage balance exhausted` or a 429 / rate-limit line → absent.

## Gemini (google, Antigravity CLI `agy`)

- Invocation: `agy --print <prompt> --model M --mode plan --sandbox --output-format json --print-timeout <timeout-30>s` with `AGY_CLI_DISABLE_AUTO_UPDATE=1` and `NO_COLOR=1`. M carries the effort as its suffix (`gemini-3.1-pro-high`); meta records that suffix as `effort`.
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
- `catchup --orchestrator <current host>` lists PROVISIONAL debates whose absent vendor is back, with exact commands, then `record --amend`.
  - Plain `submit --file` is offered only when the current host is that vendor and the debate's stored orchestrator (`ready`, `commands`).
  - A vendor other than the stored orchestrator whose `call` seat is READY gets `prompt` + `call`.
  - Every other pending seat gets `host_session_commands` (`prompt`, then `submit --host-session`), including the stored host's own seat seen from another CLI (`readiness: HOST_SESSION`). A seat whose quota evidence is spent gets none.
  - The returning vendor answers ACCEPT or OBJECT.
  - Present r1 vendors plus catch-up ACCEPT vendors reaching 4 (no OBJECT, nothing unreadable, valid judge) promotes the debate to FINAL with `via: catch-up`.
  - An OBJECT sets `blocked`. A first line that is neither ACCEPT nor OBJECT is listed in `unresolved` and blocks FINAL.
- Judge: `judge-pick` walks a rotation seeded by the debate id.
  - It skips the orchestrator, the interject `--subject-vendor`, vendors that hit quota in this debate, shimmed seats, and UNKNOWN seats unless `--accept-unknown`.
  - None left → the orchestrator's vendor in a fresh session, marked `same-vendor`.
  - Only the vendor in `judge.json` answers the judge round: `submit --round judge` needs `judge.json` and that vendor, and takes `independence` from it (the orchestrator's vendor is always `same-vendor`). `call --round judge` refuses another vendor when `judge.json` exists. The interject `subject_vendor` is refused by both.
  - The judge prompt says one anonymized position may come from the judge's own vendor; meta records `judge_wrote_position` and `positions_count`.
- Interject cards go out only with both `deliver --orca-terminal HANDLE` and `--send`; otherwise `deliver` prints the orca command as a dry run. Control and bidi characters are stripped from the card and the argv text.

## Interject scan sources

`interject_scan.py scan` reads bounded tails only (no model call) and reports `agent` codex, claude, grok or agy. Roots: `--codex-root`, `--claude-root`, `--grok-root`, `--agy-root`, else the `AI_DEBATE_*` overrides above, else the CLI defaults.

- Grok: `<sessions>/<urlencoded cwd>/<session id>/updates.jsonl` plus `summary.json` (cwd, title, `current_model_id`, `reasoning_effort`). `user_message_chunk` opens a turn; `turn_completed` or a `stop`/`stop_failure`/`session_end` hook closes it. Agent activity without a user record opens one (background wake-up). Times come from `_meta.agentTimestampMs`; when the opening record is beyond the tail, `_meta.turnStartMs` of the open prompt gives the start. Quota (T5) is the latest billing line of `AI_DEBATE_GROK_LOG` or `~/.grok/logs/unified.jsonl` at 100% before its period end. `chat_history.jsonl` has no timestamps and is not needed.
- agy: `<brain>/<conversation>/.system_generated/logs/transcript.jsonl` steps. `USER_INPUT` opens a turn (text inside `<USER_REQUEST>`, which agy may cut off); a `DONE` `PLANNER_RESPONSE` without tool calls is the final answer; any later step (tool call, `RUNNING` result, `SYSTEM_MESSAGE`) keeps or reopens the turn. Workspace comes from `history.jsonl` next to `brain`. No local quota evidence, so no T5.
- Same stale rule (30 min without records gives `stale`), the same T1-T4 rules and the same redaction as Codex and Claude Code. T6 needs a Codex thread goal.

## Test hooks

- `AI_DEBATE_CMD_<VENDOR>` and `AI_DEBATE_CMD_ORCA`: JSON argv prefix; `[]` means absent.
- `AI_DEBATE_CODEX_SESSIONS`, `AI_DEBATE_GROK_LOG`, `AI_DEBATE_CLAUDE_BRIDGE`: evidence locations.
- `AI_DEBATE_CLAUDE_PROJECTS`, `AI_DEBATE_GROK_SESSIONS`, `AI_DEBATE_AGY_BRAIN` (with `AI_DEBATE_CODEX_SESSIONS`): host-session and interject scan roots.
- `AI_DEBATE_HOME`: state root.
- `AI_DEBATE_NOW` (ISO-8601) is honoured only when `AI_DEBATE_TEST=1`.
- Tests use fake CLIs only; no vendor is called. They drop the host markers of the CLI running them and set markers explicitly where a test needs them.
