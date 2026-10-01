# Model catalog map — CLI names, registry IDs and the 2026-10-02 refresh

## Contents

- CLI name map
- Registered legacy entries
- Lane migration pending
- Refresh record (2026-10-02)
- Repeating the refresh

`references/model-registry.json` stores provider API IDs only. CLI catalogs can
print a different name, carry an effort inside the name, or offer a CLI-only
serving tier. The names below are documentation, not registry IDs or aliases:
a runtime candidate that requests one fails closed with `MODEL_NOT_REGISTERED`.
The registry schema has no CLI-name alias table, so the IDs stay unchanged.

## CLI name map

agy prints no API ID; its rows are matched by display name, for example
"Gemini 3.8 Flash (High)". `runtime_collect.py` does not collect agy models and
no guarded agy execution adapter exists, so this map grants no route.

| Surface | CLI catalog name | Registry ID | Effort in name | Note |
| --- | --- | --- | --- | --- |
| `antigravity` | `gemini-3.8-flash-high` | `gemini-3.8-flash` | `high` | thinking level high |
| `antigravity` | `gemini-3.8-flash-medium` | `gemini-3.8-flash` | `medium` | API default level |
| `antigravity` | `gemini-3.8-flash-low` | `gemini-3.8-flash` | `low` | |
| `antigravity` | `gemini-3.1-pro-high` | `gemini-3.1-pro-preview` | `high` | preview, so `MODEL_NOT_ACTIVE` |
| `antigravity` | `gemini-3.1-pro-low` | `gemini-3.1-pro-preview` | `low` | agy lists no medium |
| `antigravity` | `gemini-3.7-flash-high` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.7-flash-medium` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.7-flash-low` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.6-flash-high` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.6-flash-medium` | `unregistered` | `-` | older Flash |
| `antigravity` | `gemini-3.6-flash-low` | `unregistered` | `-` | older Flash |
| `antigravity` | `claude-sonnet-4-6` | `unregistered` | `-` | Anthropic model on the Google surface; the schema binds antigravity to Google |
| `antigravity` | `claude-opus-4-6-thinking` | `unregistered` | `-` | same |
| `antigravity` | `gpt-oss-120b-medium` | `unregistered` | `-` | not a Google model |
| `grok` | `grok-4.7-build-fast` | `unregistered` | `-` | Grok 4.7 on faster serving at 2x standard token rates (1.5x long context), Cursor and Grok Build only, not on the public xAI API. Not for default routing |
| `claude` | `claude-haiku-4-5-20251001` | `unregistered` | `-` | Claude docs: default effort "Not supported", so it cannot satisfy the registry's explicit effort list; retirement not sooner than 2026-10-15 |
| `codex` | `gpt-5.5` | `unregistered` | `-` | listed by Codex 0.159.2 with efforts up to xhigh; previous generation |
| `codex` | `gpt-reserve` | `unregistered` | `-` | hidden in the Codex catalog |
| `codex` | `codex-auto-review` | `unregistered` | `-` | hidden in the Codex catalog |

## Registered legacy entries

- `grok-4.5` is a public xAI API model, so it is registered as `generation: legacy`
  with `low`, `medium`, `high`. Its model page lists `xhigh`, but the reasoning
  guide says grok-4.5 treats `xhigh` as `high`, and its release note and grok CLI
  1.0.46 list three levels; the conservative set wins.
- `claude-opus-5` and `claude-sonnet-5` are labelled Legacy on their Claude
  overview pages and Active in the deprecation table, so they keep
  `lifecycle: active` and carry `generation: legacy`, like `gpt-5.6-*` and `grok-4.6`.
- No registered model gains an Orca lane here, and the shadow task-fit policy
  names only current Claude/Codex models. A non-Orca route that passes its own
  gates can still pick a legacy model. `constrain_runtime` copies
  `generation: legacy` onto the candidate, and the planner scores it after
  resource rank and the 80% quota guard but before quota percentage. A legacy
  model therefore loses to an equally ranked current one, even when the current
  one has used more of its quota (below 80%).

## Lane migration pending

Orca lanes (`routing.LANES`, `PROCESS_LANES`, `CLASS_LANES`, `COORDINATOR`) are
unchanged in 2.12.43. Six `legacy_lane_migration` entries are `pending-*`; the
other four are `keep-*` and stay on their own model: `claude-fable-5-1`,
`gpt-6-astra`, `gpt-daybreak-blue-latest` and `gemini-3.8-flash`.
Changing a lane needs a separate decision with an Orca canary and `/ai-debate`.
Until then the planner rejects Orca dispatch to `claude-opus-5-5`,
`claude-sonnet-5-5`, `gpt-6.1-sol`, `gpt-6-sol`, `gpt-6-luna`, `grok-4.7` and
`grok-4.5` with `ORCA_UNREGISTERED_PROCESS_OR_MODEL`. Non-Orca guarded adapters
still apply their own account, billing and effort gates.

## Refresh record (2026-10-02)

All times are KST. No model, Bot or paid API call was made.

| Evidence | Observed | Result |
| --- | --- | --- |
| Codex `~/.codex/models_cache.json` | read 00:40; `fetched_at` 2026-10-01T15:39:26Z, client 0.159.2 | 11 slugs; priority 1 `gpt-6.1-sol`. Every registered slug lists low to max, plus harness-only `ultra` on 6.1-sol, 6-astra, 6-sol, 5.6-sol, 5.6-terra and Daybreak; none lists `none` |
| `grok --no-auto-update models` | 00:41, grok 1.0.46 | `grok-4.7` (default), `grok-4.7-build-fast`, `grok-4.6`, `grok-4.5` |
| `~/.grok/models_cache.json` | `fetched_at` 2026-10-01T15:40:44Z | 4.7, 4.7-build-fast and 4.6: low to xhigh, default high; 4.5: low to high; 256K and 500K windows |
| `agy models`, `AGY_CLI_DISABLE_AUTO_UPDATE=1` | 00:41 | the 14 names above; agy version not re-observed |
| `claude --version`, `claude --help` | 00:41 | 2.1.286; `--effort` low, medium, high, xhigh, max; no local model list |
| Registry sources, plus `cl_old_sonnet` and `x_grok45` | 00:42 to 00:46, HTTP 200 | IDs, API efforts, context, prices and long-context tiers, retirement dates and the Claude Code notes match. Updated: Gemini latest-model page date 2026-09-23 and the Sonnet 5 Legacy label |
| Task-fit policy sources (9) | 00:42 to 00:48 | cited claims unchanged; the openai.com Astra page refused a scripted user agent (403) and loaded with browser request headers |

The Daybreak alias page still lists `gpt-5.6-sol` as its target. Artificial
Analysis says GPT-6.1 Sol replaces GPT-6 Sol, but OpenAI shows no deprecation,
so `gpt-6-sol` stays active. Registry `checked_at` is the earliest observation
(2026-10-02 00:39:26), so its facts expire 2026-10-09 00:39:26; the task-fit
policy is valid until 2026-10-09 00:42:30.

## Repeating the refresh

1. Read the Codex models cache, run `grok --no-auto-update models` and
   `agy models` with auto-update off, and read `claude --help`. Do not send a prompt.
2. Re-read every registry and task-fit source over HTTPS; check IDs, efforts,
   prices, tiers and retirement dates against the JSON.
3. Set `checked_at` to the earliest observation actually made, never a later
   time, then run `test_model_registry.py`, `test_runtime_collect.py` and `test_orchestrate.py`.
