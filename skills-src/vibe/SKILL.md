---
name: vibe
description: "Use when the user invokes \"/vibe\", \"바이브로 알아서 해줘\", \"스킬 조합해서 처리해\", \"오르카로 돌려\", or \"orchestrate this task\". Acts as the main entry point for installed SimonK-stack skills: discovers the relevant skills, decomposes dependencies, chooses software and CLI/API/MCP or GUI Bot execution, and matches Claude, Codex (GPT), Antigravity (Gemini), Grok and Grok Bot to verified model/effort capabilities and a total-run cost budget. Produces a validated execution plan, scoped handoffs, verified artifacts and a usage report. Small tasks stay in the current session; GUI-only steps use vibe-bot internally. Never treats unknown cost or unsupported model controls as zero or applied."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 2.6.0
author: simon-stack
---

# vibe — Main skill orchestrator

Simon supplies an outcome. Own skill selection, software selection, model and
reasoning allocation, execution, verification and reporting until that outcome
is met. Use Claude, Codex (GPT), Antigravity (Gemini), Grok and Grok Bot as five
execution surfaces, not five independent model vendors.

## Entry points

- `/vibe <task>`: use the current context, make a small plan, then execute.
- `/vibe`: resume the active request when one exists. If there is no task,
  create the existing intake form or ask for the desired outcome once.
- `/vibe 실행 …`: consume the supplied task and choices without another form.
- `/vibe-bot`: remains a compatible direct entry point. Under /vibe it is the
  internal GUI adapter; the user does not need a second invocation.
- An explicit request for a report or plan ends with that artifact. A build/fix
  request continues through implementation and verification.

Default to `balanced`, two attempts per task, two simultaneous external tasks
and **USD 0 additional metered spend** unless an existing user-approved budget
covers this run. An approved budget persists within its original scope.
Quality preference is not spending authorization.

## 1. Discover the needed skills and software

Run `python "<skill>/scripts/orchestrate.py" catalog` to inspect skill metadata.
Root order is: the current skill's sibling directory, then installed .agents,
.codex and .claude roots. Supply repeated `--root` flags when the environment
provides different canonical roots. First declared name wins; resolved paths
and content hashes expose duplicate copies. Native/plugin skills exposed by
the host remain available even if they have no local directory.

Honor user-named skills, then use descriptions to select the smallest complete
set. Read each selected SKILL.md and its required references before execution.
Do not load every skill body. Do not restrict discovery to a hardcoded list or
a historical skill count. Missing skills are explicit blockers for their step.

Treat `simonk`, `app-dev-orchestrator` and `dev-orchestrator` as procedures
owned by the current coordinator. Reuse their planning and verification; never
spawn a second coordinator or recursively invoke /vibe. Carry ancestor skill
IDs into child handoffs. Ordinary leaf skills can be composed freely.

Check actual CLI/API/MCP availability and credentials without printing secrets.
Deterministic scans, builds, tests, conversions and file operations use the
appropriate software directly. Small reasoning tasks stay in the current
session when its observed capabilities suffice. Independent substantial tasks
can use workers. GUI-only steps use the Bot adapter in section 4.

## 2. Plan model, effort and cost together

Read [orchestration contract](references/orchestration.md) before constructing
a run. The helper implements metadata discovery, route preflight, dependency
readiness and Bot result checks; the host executes its handoffs.

For each node record its outcome, selected skills, dependencies, needed
capabilities/software, scope, acceptance evidence, writes, demand level and
verification relationship. Use unique node IDs even when two nodes share the
same legacy process (for example coding).

Supply a runtime snapshot from observed local catalogs and transport probes.
Model IDs, provider-supported efforts, transport-supported efforts, billing
mode, quota, lifecycle and observation evidence are data, not guesses.
Do not turn a newly announced model into an active route without availability
and transport evidence. Do not inherit an old model's effort mapping blindly.

Routine, reasoning and critical demand map to provider-specific effort values.
Both the model and the transport must support that value. The current host
cannot silently switch itself to the requested model or effort: reuse it only
when its actual settings match, otherwise use a verified worker.
Record requested effort separately from effective effort; unknown stays null.
Bot model/effort remains provider-managed unless a real control is verified.

Validate with:
```text
python "<skill>/scripts/orchestrate.py" plan --input request.json --runtime runtime.json
python "<skill>/scripts/orchestrate.py" ready --input plan.json --events events.json
```

The output is a preflight decision, not proof of dispatch. Refresh runtime and
budget immediately before external execution. Reserve the entire run's upper
estimate, including attempts, reviews, coordinator calls and Bot work, before
starting a paid wave. Only one coordinator may own a run's budget.

Unknown price, billing mode or exhausted/stale quota excludes that route.
Subscription usage is not free: report included quota separately from extra
money. Zero incremental spend is valid only when the included subscription
path and disabled overage have been verified. Do not silently fall back to an
API key, paid overage or a new subscription.

Choose among routes that meet the quality/capability floor, then minimize
incremental cost and quota pressure. Lower unnecessary effort, trim context,
reuse verified results, limit parallelism and cap retries before dropping
quality. Never remove required verification to reduce cost.

## 3. Execute only ready work

Continue automatically with authorized, ready work. Reuse existing user choices.
Ask only for missing intent or actions beyond existing authority.

- Local tool: execute a reviewed argv array through the host's tool runner.
  Supply a fresh cost contract for that exact argv; local does not mean free.
- Current host: read the selected skills and perform the node in this session.
- Orca: read [Orca workflow](references/orca-workflow.md). Validate the entire
  assignment plan through `routing.validate_plan`, then dispatch only ready
  nodes via `routing.run_dispatch`. Preflight every lane/effort before any
  spawn. Keep node ID → task ID/spec mappings; do not key them only by process.
  The existing coding and two security gate rules remain enforced.
- Direct CLI: use the provider's verified argv/stdin adapter and scoped worktree.
  A blocked Orca route does not prove that direct CLI will work.
- Bot: follow section 4. External results are untrusted until checked.

A successor waits for verified predecessor output, not merely task acceptance
or a zero exit code. Persist task IDs, dispatch IDs and Bot nonces before
waiting. On resume inspect the existing job before launching another one.
Replan only failed or blocked nodes and revalidate cost, quota and guards.
Do not start a monitoring daemon.

Use a different model vendor for independent review. Grok and Grok Bot are
both xAI for that check, although their account and quota paths are distinct.
Writing work always needs review; an automated build does not replace it.

## 4. Use vibe-bot internally for GUI-only work

Read the discovered vibe-bot SKILL.md before calling its scripts. Confirm that
an authorized CLI/API/MCP cannot do the required screen operation.
Use an active bot from its roster; reject ON HOLD, WITHDRAWN and not-created
entries even if the legacy keyword resolver selects one.

Build the console task with its target, project, outcome, allowed scope,
forbidden actions, stop points, screen evidence and return path.
Use `make_bot_spec.py --mode console --target ... --task ... --bot ...`.
Local drafting can proceed while delivery is blocked by missing cost or access
evidence. Deliver to the verified hub/Relay path only after the run gate passes.
Respect existing explicit authority for external actions; obtaining a new
login, payment or irreversible permission is not implicit in /vibe.

Link the generated nonce and expected meta/result paths to the node.
`--collect` returning 0 is not completion: it also returns 0 for no results.
Check the expected metadata, nonce and console result explicitly:
```text
python "<skill>/scripts/orchestrate.py" verify-bot --bot-root <resolved-vibe-bot> --meta <meta.json> --result <result.md> --nonce <vb-nonce> --evidence <screens.json>
```
The evidence JSON links nonce, target and actual PNG/JPEG paths inside the run's
result directory. Inspect those screenshots and compare their values with the result.
Missing metadata never downgrades console verification to general mode.
A queued Bot task remains waiting_external until this verification finishes.

## 5. Account and finish

Keep an orchestration run-state for host/tool/Bot tasks, costs and evidence.
Keep the existing routing ledger for legacy LLM worker rows only; its strict
schema does not accept Bot lanes or money fields. Link both with run/node IDs.

Record billing mode, account reference (non-secret alias), quota bucket,
estimated upper amount, actual amount (null when unknown), tokens/credits when
reported, retries, requested/resolved model and requested/effective effort.
Grok CLI and Grok Bot do not share a budget bucket unless observed evidence
establishes it. Reasoning tokens already included in output billing are not
charged twice in estimates.

Provider costs can exceed estimates. Set real provider output/spend caps when
available; pause new paid work if observed spend breaches the run budget.
The planner's reservation is not a provider-enforced billing hard cap.

Mark a node done only after checking its own output and attaching evidence.
For a writer this means output-ready, not approved: only its explicit verifiers
may consume it until all required LLM reviews pass. General and transitive
successors remain blocked. Declare the whole task complete only after those
reviews and the user's acceptance criteria pass.
For Orca rounds retain the existing decision sheet, ledger and release steps.
Report the result, verification, selected routes, additional spend, subscription
usage, and remaining waiting/blocked work. Never call an accepted job complete.

## Legacy Orca routing

This generated block remains the execution adapter's current policy. The
umbrella planner consumes runtime facts above it; changing frontier defaults
requires the separate registry/canary migration. It cannot bypass these guards.

<!-- ROUTING:BEGIN — scripts/routing.py 가 생성한다. 손으로 고치지 말 것 -->

### 레인 카탈로그

| 레인 | CLI | 최상위 | 표준 | Orca 실측 허용 | effort 전달 | 오르카 기동 | 정격 |
|---|---|---|---|---|---|---|---|
| `claude-opus-5` | claude | `ultracode` | `standard` | `standard` · `ultracode` (와이어는 항상 `--effort max`) | 프롬프트 키워드 | ✅ `--model`·`--effort` 가능 | 1M |
| `claude-fable-5-1` | claude | `max` | `high` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 1M · 쿼터 fableWeekly 별도 · API 단가 Opus 5의 2배 |
| `claude-sonnet-5` | claude | `xhigh` | `medium` | `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 1M · API 단가 Opus 5의 0.4배 |
| `gpt-6-astra` | codex | `xhigh` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) · Orca 상한 xhigh |
| `gpt-5.6-sol` | codex | `ultra` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` · `ultra` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) |
| `gpt-5.6-terra` | codex | `max` | `medium` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` · `ultra` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) |
| `gpt-5.6-luna` | codex | `medium` | `low` | `minimal` · `low` · `medium` · `high` · `xhigh` · `max` | `--effort` | ✅ `--model`·`--effort` 가능 | 272K(최대 872K) · 최저가 |
| `gpt-daybreak-blue-latest` | codex | `xhigh` | `high` | `minimal` · `low` · `medium` · `high` · `xhigh` | `--effort` | ✅ `--model`·`--effort` 가능 | 보안 전용 · 기본 low · Orca 상한 xhigh |
| `gemini-3.8-flash` | antigravity | `high` | `medium` | — **지정 불가** (그 CLI 기본값) | **슬러그 내장** | ❌ **Orca 워커 불가** (agent 미등록·과제 전달 실패 — CLI 직행만) | Gemini Flash 계열 |
| `grok-4.6` | grok | `xhigh` | `high` | — **지정 불가** (그 CLI 기본값) | `--effort` | ⚠ `--agent` 만 — `--model` 거부 | 500K · 200K초과 2배 과금 |

**「Orca 실측 허용」은 2026-09-06 에 전수 측정한 값이다** — `python scripts/routing.py --probe-efforts --task <실재 task_id>` 로 언제든 다시 잰다(워커가 안 뜨므로 비용 0). `models_cache.json` 이 지원한다고 적는 값과 **다르다**: astra·daybreak 은 CLI 에서는 `ultra`·`max` 가 돌지만 Orca 워커로는 `xhigh` 가 상한이다. 정책 두 단(최상위/표준) 밖의 값을 쓰려면 `allow_off_ladder=True` 를 명시한다. ⚠ **Orca 는 `--model` 문자열을 검증하지 않는다** — 존재하지 않는 슬러그도 `high`·`xhigh` 면 통과하고, 워커가 뜬 뒤 codex 가 죽는다. 이 표의 레인 키가 사실상 유일한 오타 방어선이다.

**오르카 기동은 2026-09-04 실측이다.** `--model` 은 Claude·Codex·Cursor 만 받는다 (orca help) — grok·gemini 는 `--agent` 만 주고 모델은 그 CLI 의 기본값이 쓰인다. ⚠ **agent id 는 CLI 이름이 아니라 좌석 이름이다**: `--agent agy` 는 `agent_unconfigured` 로 거부되고 `--agent antigravity` 가 정본이다. (CLI 바이너리는 `agy`, Orca 등록명은 `antigravity`.)

**배정 금지**: `codex-auto-review` · `gpt-5.3-codex-spark` · `gpt-5.4-mini` · `gpt-reserve` — 용도 미검증 / R&R 미확정 (발주 §3) · **D-28**: 코딩은 공정 전용 목록 `PROCESS_LANES` (claude 전용 · codex 폴백 없음 · #5 · 파일을 바꾸는 `writes` 공정도 같음 · Q-09) · fable·sonnet 은 M1 통과(2026-09-16) 뒤 2순위 편입 · A-verify = astra → fable → opus(읽기 전용 · `writes` 면 A_VERIFY_WRITES) · 반증 "예"인 A 작업은 A-verify 로 승격 · gemini `unavailable`(M6) → `references/d28-routing.md`

### 공정 → 클래스 → 레인

| 공정 | 클래스 | 1순위 | 2순위 | 3후보 |
|---|---|---|---|---|
| 대량 정형 변환 · 카운트 | A | `gpt-5.6-luna` | `claude-sonnet-5` | `claude-opus-5` |
| 인벤토리 · 스키마 검증 | A | `gpt-5.6-luna` | `claude-sonnet-5` | `claude-opus-5` |
| 디스크 스캔 · grep | A | `gpt-5.6-luna` | `claude-sonnet-5` | `claude-opus-5` |
| 장문 로그 · 커밋히스토리 분류 집계 | A | `gpt-5.6-luna` | `claude-sonnet-5` | `claude-opus-5` |
| 기록↔사실 대조 · 주장 판정 (읽기 전용) | A-verify | `gpt-6-astra` | `claude-fable-5-1` | `claude-opus-5` |
| 웹 리서치 — 정독 · 모순 종합 | B | `gpt-6-astra` | `claude-fable-5-1` | `claude-opus-5` |
| 코딩 — 구현 · 대규모 리팩터링 **(공정 전용 목록)** | B | `claude-opus-5` | `claude-fable-5-1` | — |
| 터미널 · CI · git (판단 섞인 경우) | B | `gpt-6-astra` | `claude-fable-5-1` | `claude-opus-5` |
| 보안 — 생성물 안전성 게이트 | B | **`gpt-daybreak-blue-latest` @xhigh 고정** | — | — |
| 보안 — 비즈니스 로직 · 인가 | B | **`gpt-6-astra` @xhigh 고정** | — | — |
| 트렌드 · 실시간 | C-realtime | `grok-4.6` | `gpt-5.6-sol` | `claude-opus-5` |
| 웹 리서치 — 수집 | C-realtime | `grok-4.6` | `gpt-5.6-sol` | `claude-opus-5` |
| Google 플랫폼 (BigQuery/Firebase/Workspace) | C-platform | `gemini-3.8-flash` | `gpt-5.6-sol` | `claude-opus-5` |
| UI 시각 검증 | C-platform | `gemini-3.8-flash` | `gpt-5.6-sol` | `claude-opus-5` |
| 다레인 산출물 조립 | D | **`claude-opus-5` @ultracode 고정** | — | — |
| 워크트리 · run 관리 (orca CLI) | N | — | — | — |

### effort 결정 — 클래스가 아니라 태스크 속성

> **반증 가능한 전제가 있나?** ("X는 죽었다"를 확인 / "A가 B보다 낫다"를 판정 / 원인 규명)

| | `claude-opus-5` | `claude-fable-5-1` | `claude-sonnet-5` | `gpt-6-astra` | `gpt-5.6-sol` | `gpt-5.6-terra` | `gpt-5.6-luna` | `gpt-daybreak-blue-latest` | `gemini-3.8-flash` | `grok-4.6` |
|---|---|---|---|---|---|---|---|---|---|---|
| **YES** 최상위 | `ultracode` | `max` | `xhigh` | `xhigh` | `ultra` | `max` | `medium` | `xhigh` | `high` | `xhigh` |
| **NO** 표준 | `standard` | `high` | `medium` | `high` | `high` | `medium` | `low` | `high` | `medium` | `high` |
| 사다리 밖 상한 (`allow_off_ladder`) | `ultracode` | `max` | `max` | `xhigh` | `ultra` | `ultra` | `max` | `xhigh` | — (지정 불가) | — (지정 불가) |

셋째 줄이 **물리적 상한**이다. 둘째 줄까지가 기본 경로고, 셋째 줄까지는 `allow_off_ladder=True` 를 명시해야 열린다 — 원장에 `off_ladder` 로 남는다. 그 위(`ultra`·`max` on astra/daybreak)는 Orca 가 거부하므로 **없는 값**이다. 거기가 정말 필요하면 워커가 아니라 codex 직행이다 (`run_codex_exec`).

코디네이터 레인 = **`gpt-5.6-sol` @xhigh** — 종합(D)과 벤더가 달라야 한다. 워커 겸임은 클래스와 무관하게 경고한다(D-28 #6).

### 레인별 산출물 제약

| 레인 | 허용 | 금지 | 사유 |
|---|---|---|---|
| `grok-4.6` | CSV · 카운트 · 분류 라벨만 | 서술 결론 · 인과 추정 · 200K 초과 입력(과금 2배) | 사실 신뢰도가 4레인 중 최약. 합계는 D 레인이 산술 재검산한다 |
| `gemini-3.8-flash` | 발견 목록 + 탐색 드라이브 · 제외 경로 · 스캔 파일 수 | 범위 없는 '0건' 반환 · 무인 장기 루프 단독 배치 | 부재 보고 오류가 직전 라운드 오류 5건 중 3건의 원인 |
| `gpt-5.6-luna` | 정형 변환 · 카운트 · 분류 · **부재 보고에는 탐색 범위 명시** | 우열 판단 (필요하면 terra 이상으로 올린다) · 범위 없는 '0건' | 최저가 레인 — 판단을 맡기면 싼 값에 틀린다. 범위 요구는 Simon 결정(2026-09-04, luna03 채택)으로 A 클래스 전체에 적용된다 |
| `claude-opus-5` | 항목별 확신도 표기 필수 (강=기계검증 / 약=판단) | 리포트만 내고 끝내기 — 사람이 읽는 것은 결정 시트 1장이다 | 종합 레인이므로 사람의 결정으로 이어져야 한다 |
| `gpt-6-astra` | 판단마다 근거(파일·행·명령 출력) 첨부 · 반증 시도 1건 이상 명시 | 대량 정형 변환에 배치 (A 클래스는 luna 로 내린다) · `ultra`/`max` 로 Orca 디스패치 (거부된다 — 상한 xhigh) | codex 계열 최상위 좌석이다. 싼 일에 태우면 쿼터만 태우고, 정책 밖 effort 로 부르면 워커가 아예 안 뜬다 |
| `gpt-daybreak-blue-latest` | 취약점 발견마다 file:line · 재현 경로 · 심각도 · 최소 패치 | 방어 목적 밖의 공격 코드 생성 · 범위 없는 '취약점 0건' | 보안 전용 레인 — 근거 없는 발견은 게이트를 무력화한다. 출력이 차단되면 Trusted Access 미승인이므로 terminal read 로 확인한다 |

### 가드

| | 내용 | 자동 검출 |
|---|---|---|
| G1 | 짠 레인이 자기 코드를 보안 리뷰하지 않는다 | ✅ 원장 기록 |
| G2 | 자기 결론 재검증에 서브에이전트를 쓰지 않는다 — 반증은 리포트 '§X 반증 시도' 섹션 | — (오검출 방지) |
| G3 | 워커당 spawn 상한 8 | ✅ 원장 기록 |
| G4 | 쿼터 게이트는 디스패치 시점에만. 실행 중 중단 근거로 쓰지 않는다 — 한도 도달로 **실패·정지한** 워커만 여유 레인의 새 task 로 인수인계한다(`handoff_spec` + `revalidate_for_retry`, Q-260913-05). 상시 모니터링 데몬·실행 중 선제 교체는 하지 않는다 | — (오검출 방지) |
| G5 | 쿼터는 4벤더 각각 확인한다 | ✅ 원장 기록 |
| G6 | 부재 보고에는 탐색 범위를 붙인다. 범위 없는 '0건'은 반환값 불인정 — gemini 뿐 아니라 **A 클래스 전체**에 적용 (Simon 결정 2026-09-04) | — (오검출 방지) |
| G7 | 최상위 effort 는 반증질문 YES 인 태스크에만 | — (오검출 방지) |
| G8 | 쓰기 라운드는 **워커 강제종료 절차가 선 상태에서만** 띄운다 — `python scripts/kill_worker.py --dispatch <ctx_…>` (기본은 목록만, `--kill --fence` 로 트리 종료 → 재스캔 0 확인 → worker-stop). worker-stop 은 프로세스 사망을 약속하지 않는다. 원래 문구 '문서화 전까지 착수 금지'는 2026-09-13 문서화·실측 1회로 충족 — SKILL.md '워커 강제종료 (G8)' | — (오검출 방지) |
| G9 | Move-Item 배치는 매니페스트 + 역방향 스크립트 선행 | — (오검출 방지) |
| G10 | 적대적 평가에서 채점자는 두 생산자와 **벤더가 달라야** 한다. 벤더 3개를 못 채우면 그 문제는 건너뛴다 — 자기 벤더가 자기 답을 채점하느니 관측을 포기한다 (`adversarial_eval.py`) | — (오검출 방지) |
| G11 | 디스패치 전에 툴체인 최신화를 확인한다 — codex 가 한 버전만 뒤처져도 `Agent startup blocked: codex-update-prompt` 로 **전 워커가 안 뜨는데 에러가 프롬프트 문제처럼 보인다** (2026-09-12 실사고). `python scripts/check_tooling.py` | — (오검출 방지) |
| G12 | **벤더 가용성은 쿼터로 판정하지 않는다 — 실호출로 확인한다.** 2026-09-13 실측: grok 은 402(잔액 소진), gemini 단독 CLI 는 IneligibleTierError 였는데 **쿼터 %로는 둘 다 여유 있어 보였다** — 못 쓰는 이유가 쿼터가 아니었기 때문이다. 쿼터 게이트(G5)는 '얼마나 썼나'를 보고, 이건 '지금 답이 나오나'를 본다. 다른 질문이다. `python scripts/adversarial_eval.py --preflight` | — (오검출 방지) |
| G13 | 재시도(`worker-start --retry-of`)·수동 재배정도 계획 검증을 다시 통과해야 한다 — `routing.revalidate_for_retry(plan, proc, new_lane, ...)` 가 (ok, 위반, 메모, 새 계획)을 준다. `--retry-of` 는 orca CLI 를 직접 부르므로 routing 의 계획 검증을 거치지 않는다 (D-28 #14) | — (오검출 방지) |
| G14 | 결정 시트(`make_decision_sheet.py`)를 만들지 않은 라운드는 **끝난 것으로 치지 않는다** — 손으로 조립한 시트는 `decisions_run_*.json` 을 내지 않아 채택률이 비고 스왑 규칙이 돌지 않는다 (D-28 #15) | — (오검출 방지) |

쿼터: 80% 초과 → **모든 순위에서** 강등(ok 레인이 없으면 첫 강등 레인) · 100% 도달 → 사용 금지(Q-05) · 읽기 실패 = **미확인**(0%로 간주 금지) · 실호출(G12) 실패 = 사용 금지 · 실호출 결과가 24시간 넘으면 미확인 · `quota_bucket` 이 있는 레인(fable)은 그 버킷으로 판정 (D-28 #13)

<!-- ROUTING:END -->

## Verification and references

```text
python "<skill>/scripts/test_orchestrate.py"
python "<skill>/scripts/selftest.py"
python "<skill>/scripts/sync_skill_table.py" --check
```

- [Orchestration schema and cost policy](references/orchestration.md)
- [Retained Orca execution workflow](references/orca-workflow.md)
- [D-28 route decisions](references/d28-routing.md)
- [Astra effort transport cap](references/v2.2-astra-effort-cap.md)
- [Adversarial evaluations](references/adversarial-eval.md)
- [Operational pitfalls](references/pitfalls.md)

## Version note

2.6.0 adds the main skill entry point, discovered skill composition, five
execution surfaces, dependency preflight, total-run cost bounds and the
vibe-bot handoff/result contract. Existing Orca model defaults are unchanged.
