# Changelog

## 2.14.0 - 2026-10-04

- 허브 결정 D-67(토론 `dbt-261004-033902`, ADD_ALONGSIDE_KEEP_LEGACY, 4/4,
  심판 확신도 92)에 따라 현행 세대 Orca 레인 두 개를 옛 레인 옆에 추가했다.
  `claude-opus-5-5` 는 flag 레인(정책 high/max, Orca low~max)이고 `gpt-6.1-sol` 은
  flag 레인(정책 high/xhigh, Orca minimal~xhigh)이다. 근거는 Orca 1.4.218 번들의
  검증 코드(claude 미등록 id → low~max, codex 미등록 모델 → xhigh 상한)이며 모델 호출은 0회다.
- 이 두 레인은 **등록만 됐다.** registry `legacy_lane_migration` 상태는
  `pending-transport-and-canary` 이고, 읽기 전용 canary(`launch.requested` ↔
  `launch.effective`)와 Orca 런치 계정/과금 인증서 전까지 동작 레인이 아니다.
  native send 보류와 준비 브리지 미구현도 그대로다.
- 우선순위 목록(A·B·A-verify·C-realtime·C-platform·D)과 `PROCESS_LANES.coding` 의
  `claude-opus-5` 를 `claude-opus-5-5` 로 바꿨다. 옛 opus 레인은 prompt-keyword 라
  guarded Orca 로 실행되지 않아 코딩 1순위와 종합 고정이 실행 경로가 없었다.
- 종합 고정을 `(claude-opus-5, ultracode)` 에서 `(claude-opus-5-5, max)` 로 옮겼다.
  ultracode 는 프롬프트 키워드라 flag 레인이 받을 수 없고, max 는 opus-5-5 의 Orca
  상한이자 허브 핀이다. 코디네이터는 `gpt-6.1-sol` @xhigh 다(종합과 다른 벤더,
  D-28 #8 의 effort 유지, 6.1-sol 의 Orca 상한). C 클래스 2순위도 `gpt-6.1-sol` 이다.
- 옛 키는 지우지 않았다. `ledger.py` 가 `LANES` 에 없는 레인의 원장 행을 거부하므로
  `claude-opus-5`·`gpt-5.6-sol` 등은 원장 호환용으로 남고, `gpt-5.6-sol` 은 C 클래스
  목록 끝의 폴백이다. sol 후속은 `gpt-6.1-sol` 로 통일했다(registry 의 `gpt-6-sol` 표기 정리).
  레지스트리 version 은 2026-10-04.1 이 됐지만 제공사 사실과 `checked_at` 은 그대로다.
- `claude-sonnet-5-5`·`gpt-6-luna`·`gpt-6-sol`·`grok-4.7` 은 레인을 만들지 않았다.
  sonnet-5-5 는 effort 재보정이 필요하고, 6-luna 는 A 클래스 1순위를 바꾸는 별도 결정이며,
  grok 은 Orca 가 모델을 고정하지 못한다. 이들로의 Orca 발주는 여전히
  `ORCA_UNREGISTERED_PROCESS_OR_MODEL` 이다.
- 소수의견 방어 테스트를 추가했다. 모델 포함·초과과금 OFF 증거가 없으면 새 레인도 기존
  flag 레인과 같은 사유(`MODEL_INCLUSION_UNVERIFIED`·`OVERAGE_UNVERIFIED`)로 막히고,
  쿼터 증거가 없으면 `ORCA_G5` 로, 런치 인증서가 없으면 `TRANSPORT_ACCOUNT_UNVERIFIED`
  로 막힌다. `gpt-6.1-sol` @max·ultra 와 `claude-opus-5-5` @ultracode 는
  `ORCA_DISPATCH_UNSUPPORTED` 다. 오프라인 테스트만 실행했다.

## 2.13.1 - 2026-10-03

- Refresh the model registry before its seven-day window closed: all 28
  registry sources and the nine task-fit sources were re-read over HTTPS
  (HTTP 200), and model IDs/efforts were compared with the local Codex, Grok,
  agy and Claude CLI catalogs, without a model call. No provider fact changed:
  IDs, API efforts, context, prices, long-context tiers, retirement dates, the
  Daybreak alias target and the Claude Code notes all match.
- `checked_at` is the earliest evidence timestamp, the Grok models cache fetch
  at 2026-10-03 21:42:01 KST, so the facts stay fresh until
  2026-10-10 21:42:01 KST instead of becoming `REGISTRY_STALE` on
  2026-10-09 00:39:26 KST. The shadow task-fit policy is valid until
  2026-10-10 21:47:06 KST; its cited claims and ranks are unchanged.
- `gpt-6-sol` stays active: OpenAI's model page points to GPT-6.1 Sol as the
  newer Sol model, but its 2026-10-01 deprecation notice names `gpt-6-sol` as a
  replacement, not a deprecated model. `gemini-3.1-pro-preview` stays preview
  with no shutdown date.
- agy 1.2.16 now lists `claude-opus-5-5-*` and `claude-sonnet-5-5-*` (low,
  medium, high) instead of `claude-sonnet-4-6` and `claude-opus-4-6-thinking`.
  The map in `references/model-catalog-map.md` records them as unregistered,
  because the schema binds the antigravity surface to Google.
- Codex 0.160.0 and Claude Code 2.1.288 were observed; their model and effort
  lists are unchanged. Orca lanes are unchanged.

## 2.13.0 - 2026-10-03

- A run that writes code (a node with `writes`, `proc=coding`, a CODE_* task
  type or the `qa` skill) can no longer complete without a pinned QA binding:
  `run_state.py bind-qa` records the QA contract and target once
  (`QA_BINDING_IMMUTABLE`, absolute paths only, `QA_INTENT_CHANGED` when the
  spec digest moves), and `Store.complete` reruns the QA gate before it marks
  the run done (`QA_BINDING_REQUIRED` otherwise). There is no opt-out, so an
  already open coding run also needs `bind-qa`. `check-qa` runs the gate alone.
- `scripts/qa_acceptance.py` executes the qa skill's `qa_gate.py` only when its
  LF-normalized SHA-256 matches the pinned constant; changing `qa_gate.py`
  needs the same constant change here. The complete event payload carries the
  QA report; the database schema is unchanged.
- Pairs with qa 2.1.0 (contract hash, exact revision/environment and evidence
  file hashes, fail-closed on missing, skipped, failed or stale evidence).
  Installed on 2026-10-03 03:43 from `feat/qa-evidence-261003` before it
  reached main; landed on main through PR #96.

## 2.12.43 - 2026-10-02

- Refresh the model registry before its seven-day window closed: every
  official source was re-read over HTTPS and model IDs/efforts were compared
  with the local Codex, Grok, agy and Claude CLI catalogs, without a model call.
  `checked_at` is now the earliest observation, 2026-10-02 00:39:26 KST, so the
  facts stay fresh until 2026-10-09 00:39:26 KST instead of becoming
  `REGISTRY_STALE` on 2026-10-06 04:03 KST.
- Register `grok-4.5` as a legacy entry with low, medium and high only: xAI's
  reasoning guide says it treats `xhigh` as `high`. Label `claude-sonnet-5`
  legacy, as Anthropic does, while it stays active.
- Leave CLI-only names unregistered and map them in
  `references/model-catalog-map.md`: `grok-4.7-build-fast` (2x token rates,
  Cursor/Grok Build only), agy effort-suffixed Gemini names, and Haiku 4.5,
  which has no effort parameter. Requests for them still fail with
  `MODEL_NOT_REGISTERED`.
- Re-read the nine task-fit sources; claims and ranks are unchanged and the
  shadow policy is valid until 2026-10-09 00:42:30 KST.
- Orca lanes are unchanged. Orca dispatch to current-generation models is still
  rejected until a separate lane-migration decision. The advisory table now
  names GPT-6.1 Sol.
- Offline tests cover the refreshed windows, the new and legacy entries, the
  unregistered CLI names, the Grok 1.0.46 listing and the Orca rejection.
- Make the legacy label count in routing. `constrain_runtime` now copies the
  registry's `generation` onto the candidate and drops any runtime claim. The
  planner and the shadow task-fit score put `generation: legacy` after resource
  rank and the 80% quota guard, before quota percentage. Before this,
  candidate-ID order let `grok-4.5` beat an equally ranked `grok-4.7` on a host
  route. Plans without a legacy candidate keep the same routes and digests.
- CI now runs `test_model_registry.py`, where most of the refresh tests live.
- `references/model-catalog-map.md` no longer says every lane migration is
  pending (four are `keep-*`) or that a registered legacy model never routes.

## 2.12.42 - 2026-10-01

- Give each /vibe run its own Gstack state folder with telemetry, update checks
  and onboarding prompts off. `run_state.py gstack-env --run <id>` creates
  `gstack-runs/<sha256 prefix>` beside the run DB without creating the DB or
  touching the personal `~/.gstack`, and prints the env, an `export` line and a
  PowerShell line. Re-entry reads the config like `gstack-config get` (last
  `key:` line, LF-split lines only, quotes kept, exact `off`/`false`) and fails
  closed otherwise.
- Plans mark Gstack bin tool handoffs when any argv element names a
  `skills/gstack/bin/` script, and Gstack-skill host/Orca nodes. Inventory flags
  a skill `gstack: true` when its SKILL.md bytes (or a shadowed alternative's)
  reference `skills/gstack/bin/` or `~/.gstack`/`$HOME/.gstack`, which catches
  plugin-packaged Gstack skills; the flag stays out of `inventory_digest`.
- The brief names `<vibe skill folder>` instead of an absolute path, so Orca Task
  specs do not depend on the install path. `refresh` rejects a changed Task spec
  on a bound, unfinished Orca node with `TASK_SPEC_CHANGED`. Finalize drafted
  preparations before upgrading; cancel and re-plan registered runs whose Task
  spec changed.
- Isolation is instruction-level: nothing reads `gstack_isolation` at runtime,
  Orca is best-effort, and Gstack-derived skills and some bin scripts still use
  `~/.gstack`/`$HOME` directly (see the orchestration reference).
- Require a PROTOCOL §35 decision record to come from `/ai-debate` >= 0.2.0 with
  all four vendor seats; the five-node debate graph is an execution contract only.
- Offline tests only. No Gstack, model, Orca worker or Bot call was made, and
  `gstack-runs` folders are not cleaned up automatically.

## 2.12.18 - 2026-09-30

- Bind Grok CLI and Grok Bot quota evidence to their distinct surface,
  transport and account, and require a freshly observed state. A reset timestamp
  or the other xAI path's quota cannot reopen a held route. Offline tests cover
  wrong surface, transport, account, missing evidence and unobserved reset.
- Align the `model-router` image-generation contract and Bot fixture with the
  already enforced planner gates. This is source-only: no provider generation,
  Relay delivery, user installation or subscription billing proof is claimed.

## 2.12.8 - 2026-09-30

- Enforce the existing writing-review rule for typed `WRITING` outputs even
  when they do not edit files. Require an independent LLM reviewer in the same
  plan and hold downstream consumers until it passes on either host. Offline
  tests cover the previously ready unreviewed path and reviewed recovery;
  this does not establish live Claude/Codex behavior or permit paid calls.

## 2.12.5 - 2026-09-29

- Admit locally measured Antigravity CLI 1.2.13 for metadata-only `/usage`:
  `/help` and `/usage` both exited successfully with zero turns and zero tokens.
  Unknown versions still stop before the slash command; this does not verify
  account identity, subscription billing, model inclusion or generation.

## 2.12.4 - 2026-09-29

- Clarify that disabling auto-reload is not proof of disabled extra-credit
  consumption for Codex or Grok. Require account/transport-specific overage
  evidence for Claude, Codex, Antigravity, Grok and Grok Bot before treating
  subscription usage as zero additional spend. No payment setting is changed.

## 2.12.3 - 2026-09-29

- Bind default catalog discovery in a Codex compatibility overlay to both
  the original bundle and its exact manual-only `zoom-out` projection.
- Reject altered overlay bytes or forged projection receipts without falling
  back to a different skill root. This is offline discovery validation, not
  host installation or model-routing certification.

## 2.12.2 - 2026-09-28

- Fail closed when legacy plan quota checks are omitted; preserve quarantine of live preflight paths.

## 2.12.1 - 2026-09-28

- Recheck current GPT, Claude, Gemini and Grok provider facts on 2026-09-28
  and refresh the seven-day model-registry evidence window. Public model
  support still does not establish subscription access or permit API billing.
- Explicitly warn that non-interactive Claude Fable can charge usage credits
  without a consent prompt; keep exact-model inclusion and overage gates.

## 2.12.0 - 2026-09-28

- Block pinned Gstack design API-key setup, generation and checks under subscription-only USD 0; require transitive local-command cost evidence.

## 2.11.13 - 2026-09-27

- Make Play Console and other GUI requests discover the `/vibe` coordinator
  even without a slash invocation. Check authorized CLI/API/MCP first and name
  only the actual `vibe-bot` adapter for GUI-only steps.
- Add a natural-language GUI routing evaluation and a description regression
  after a tool-less Claude subscription probe invented a nonexistent specialist.
  This metadata change is not a measured improvement in live selection accuracy.
- Add the exact skill-name question as a second evaluation. A follow-up
  isolated probe with `Skill` available selected the real `/vibe` on both the
  old and revised metadata. The tool-less probe disabled automatic skill use;
  it cannot establish a regression or a metadata-driven improvement.

## 2.11.12 - 2026-09-27

- Admit only locally measured Antigravity CLI 1.2.12 for zero-turn, zero-token
  `/usage` metadata collection. Keep account, model and billing verification
  unavailable; the observed quota buckets do not authorize generation.
- Record the installed CLI's rejection of `agy models --output-format json`;
  do not infer executable model routes from the text-only listing.

## 2.8.0 - 2026-09-23

- Add durable local run/account reservations and dispatch intents in one SQLite
  transaction; keep the authorized grant immutable and default to USD 0.
- Prevent repeated claim sends and unsafe retries after uncertain acceptance;
  require original-job lookup, terminal proof, cost settlement and fresh plans.
- Separate execution success, acceptance/rejection and actual-cost evidence.
  Preserve unknown cost and observed overruns; never release them on timeout.
- Add crash, concurrent-process, local CLI lifecycle and sensitive-payload
  regression tests. Strict embedded JSON parsing rejects duplicate keys and
  non-finite values; exact nanoUSD conversion never rounds approval caps up.
- Document trusted-coordinator and single-local-DB boundaries. No provider
  generation adapter, live five-surface E2E, installation or main promotion is
  implied by these state tests.

## 2.7.0 - 2026-09-23

- Add a central model/effort registry with separate provider and transport facts;
  reject stale alias/access evidence again when work becomes ready.
- Collect explicit one-shot Codex, Claude, Grok and Antigravity CLI metadata.
  Preserve observed quota buckets, credit fields and opaque account references.
- Keep unknown billing, missing identity and unverified generation unavailable;
  do not equate subscription usage or metadata success with zero-cost execution.
- Bound probe I/O and lifetime; contain owned Windows process trees before
  launch and reject server-initiated actions or unknown Antigravity contracts.
- Add offline collector regression tests. Actual metadata observations are not
  five-surface task E2E, cost authorization or deployment-parity evidence.
- Leave legacy Orca defaults unchanged. Persistent execution/budget state,
  all-consumer migration and validated installation remain separate work.

## 2.6.0 - 2026-09-23

- Introduce the umbrella skill entry point, discovered skill composition,
  five execution surfaces, dependency preflight and total-run cost bounds.
- Integrate the vibe-bot handoff and result-verification contract.
