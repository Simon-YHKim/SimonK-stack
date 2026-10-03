# Model catalog map — CLI names, registry IDs and the 2026-10-03 refresh

## Contents

- CLI name map
- Registered legacy entries
- Lane migration pending
- Refresh record (2026-10-03)
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
| `antigravity` | `claude-opus-5-5-low` | `unregistered` | `-` | Anthropic model on the Google surface; the schema binds antigravity to Google |
| `antigravity` | `claude-opus-5-5-medium` | `unregistered` | `-` | same |
| `antigravity` | `claude-opus-5-5-high` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-low` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-medium` | `unregistered` | `-` | same |
| `antigravity` | `claude-sonnet-5-5-high` | `unregistered` | `-` | same |
| `antigravity` | `gpt-oss-120b-medium` | `unregistered` | `-` | not a Google model |
| `grok` | `grok-4.7-build-fast` | `unregistered` | `-` | Grok 4.7 on faster serving at 2x standard token rates (1.5x long context), Cursor and Grok Build only, not on the public xAI API. Not for default routing |
| `claude` | `claude-haiku-4-5-20251001` | `unregistered` | `-` | Claude docs: default effort "Not supported", so it cannot satisfy the registry's explicit effort list; retirement not sooner than 2026-10-15 |
| `codex` | `gpt-5.5` | `unregistered` | `-` | listed in the Codex models cache with efforts up to xhigh; previous generation |
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
- registry 에 등록됐다고 Orca 레인이 생기지는 않는다(D-67 로 추가된 두 레인은 아래 절).
  shadow task-fit 정책은 현행 Claude/Codex 모델만 든다. 자기 게이트를 통과한
  Orca 밖 경로는 legacy 모델을 고를 수 있다. `constrain_runtime` 이
  `generation: legacy` 를 후보에 복사하고, planner 는 그 값을 resource rank 와
  80% 쿼터 가드 다음, 쿼터 비율 앞에서 본다. 그래서 순위가 같으면 legacy 모델은
  현행 모델에 진다. 현행 모델이 쿼터를 더 썼어도(80% 미만) 마찬가지다.

## Lane migration pending

D-67(2026-10-04, 허브 토론 `dbt-261004-033902`, ADD_ALONGSIDE_KEEP_LEGACY)에 따라
2.14.0 은 Orca 레인 두 개를 옛 레인 **옆에** 추가했다. 근거는 Orca 1.4.218 번들의
검증 코드를 읽은 것이며 모델 호출·worker-start 는 0회다.

| 새 레인 | 전달 | Orca 1.4.218 이 받는 effort | 정책 std / top | registry 상태 |
| --- | --- | --- | --- | --- |
| `claude-opus-5-5` | `--effort` 플래그 | low~max (claude 카탈로그에 없는 정식 id) | high / max | `pending-transport-and-canary` |
| `gpt-6.1-sol` | `--effort` 플래그 | minimal~xhigh (codex 미등록 모델 폴백, max·ultra 거부) | high / xhigh | `pending-transport-and-canary` |

- 우선순위 목록·`PROCESS_LANES.coding`·종합 고정·코디네이터를 새 키로 옮겼다.
  종합은 `claude-opus-5-5` @max 다. ultracode 는 프롬프트 키워드라 flag 레인이 받지 못한다.
  코디네이터는 `gpt-6.1-sol` @xhigh 로, 종합(claude)과 벤더가 다르고 xhigh 는 6.1-sol 의 Orca 상한이다.
- 옛 키는 지우지 않는다. `ledger.py` 는 `LANES` 에 없는 레인의 원장 행을 거부하므로
  `claude-opus-5`·`gpt-5.6-sol` 등은 원장 호환용으로 남는다. `claude-opus-5` 는 우선순위 밖이고,
  `gpt-5.6-sol` 은 C 클래스 목록 끝의 폴백이다. sol 의 후속은 `gpt-6.1-sol` 로 통일했다
  (`gpt-5.6-terra` 의 평가 후보도 같다).
- **등록이지 동작이 아니다.** native send 보류, 준비 브리지 미구현, 계정/과금 인증서 부재는
  그대로다. 읽기 전용 canary 1회(`launch.requested` 와 `launch.effective` 대조)와 Orca 런치
  계정/과금 인증서가 생기기 전까지 두 레인은 `pending-transport-and-canary` 이고 준비된 경로로
  보지 않는다. 모델 포함·초과과금 OFF·API 폴백 OFF·G5·런치 인증서 게이트는 기존 flag 레인과
  똑같이 걸린다(`test_orchestrate.py`·`test_execute_orca.py` 의 D-67 테스트).
- `legacy_lane_migration` 12건 중 8건이 `pending-*` 다. 남은 이전 대상은
  `claude-sonnet-5` → `claude-sonnet-5-5`(effort 재보정 필요), `gpt-5.6-luna` → `gpt-6-luna`
  (A 클래스 1순위 변경이라 별도 결정), `grok-4.6` → `grok-4.7`(Orca 가 grok 모델을 고정하지 못한다)이다.
  `keep-*` 4건은 자기 모델 그대로다: `claude-fable-5-1`, `gpt-6-astra`,
  `gpt-daybreak-blue-latest`, `gemini-3.8-flash`.
- 그래서 planner 는 여전히 `claude-sonnet-5-5`, `gpt-6-sol`, `gpt-6-luna`, `grok-4.7`,
  `grok-4.5` 로의 Orca 발주를 `ORCA_UNREGISTERED_PROCESS_OR_MODEL` 로 막는다. 레인을 더
  바꾸려면 Orca canary 와 `/ai-debate` 를 거친 별도 결정이 필요하다. Orca 밖 guarded adapter 는
  자기 계정·과금·effort 게이트를 그대로 적용한다.

## Refresh record (2026-10-03)

All times are KST. No model, Bot or paid API call was made. The 2026-10-02
record is in the 2.12.43 changelog entry.

| Evidence | Observed | Result |
| --- | --- | --- |
| `codex --version`, `grok --version`, `agy --version`, `claude --version` | 21:46 | Codex 0.160.0 (was 0.159.2), grok 1.0.46, agy 1.2.16, Claude Code 2.1.288 (was 2.1.286) |
| Codex `~/.codex/models_cache.json` | read 21:46; `fetched_at` 2026-10-03T12:43:40Z, cache client 0.159.0 | unchanged: 11 slugs, priority 1 `gpt-6.1-sol`, every registered slug lists low to max (`ultra` on the same six), none lists `none` |
| `grok --no-auto-update models` | 21:46, grok 1.0.46 | unchanged: `grok-4.7` (default), `grok-4.7-build-fast`, `grok-4.6`, `grok-4.5` |
| `~/.grok/models_cache.json` | `fetched_at` 2026-10-03T12:42:01Z | unchanged: 4.7, 4.7-build-fast and 4.6 low to xhigh, 4.5 low to high, default high, 256K and 500K windows |
| `agy models`, `AGY_CLI_DISABLE_AUTO_UPDATE=1` | 21:46, agy 1.2.16 | 18 names. Removed: `claude-sonnet-4-6`, `claude-opus-4-6-thinking`. Added: `claude-opus-5-5-*` and `claude-sonnet-5-5-*` (low, medium, high), mapped above as unregistered. Gemini rows unchanged |
| `claude --help` | 21:46 | `--effort` still low, medium, high, xhigh, max; no local model list |
| 28 registry sources | 21:47, HTTP 200 (Google docs need a cookie-keeping client) | IDs, API efforts, context, prices, long-context tiers, retirement dates, the Daybreak target and the Claude Code notes match. No registry value changed |
| OpenAI and Google deprecation pages | 21:48 to 21:49 | `gpt-6-sol` is a recommended replacement in the 2026-10-01 OpenAI notice, not deprecated; `gemini-3.1-pro-preview` has no shutdown date |
| Task-fit policy sources (9) | 21:47, HTTP 200 | cited claims unchanged; the openai.com Astra page loaded with browser request headers |

Artificial Analysis's article list mentions a "Gemini 4 Argon" (2026-09-30).
No Google docs page, pricing row or agy catalog name for it was found, so it is
not registered. Registry `checked_at` is the earliest evidence timestamp, the
Grok models cache fetch at 2026-10-03 21:42:01, so its facts expire
2026-10-10 21:42:01; the task-fit policy is valid until 2026-10-10 21:47:06.

## Repeating the refresh

1. Read the Codex models cache, run `grok --no-auto-update models` and
   `agy models` with auto-update off, and read `claude --help`. Do not send a prompt.
2. Re-read every registry and task-fit source over HTTPS; check IDs, efforts,
   prices, tiers and retirement dates against the JSON.
3. Set `checked_at` to the earliest observation actually made, never a later
   time, then run `test_model_registry.py`, `test_runtime_collect.py` and `test_orchestrate.py`.
