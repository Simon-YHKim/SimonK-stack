# Guarded Orca workflow

## Contents

- Scope and current limits
- Live Orca discovery
- Orca topic routing
- Intake
- Plan and prepare
- Dispatch and recovery
- Verification and cleanup
- Records and evaluation

## Scope and current limits

This workflow follows SKILL.md and the central orchestration contract.
The old model ladder is historical compatibility policy, not current account,
price, availability or transport evidence. Read the orchestration contract
linked from SKILL.md for exact request, runtime, certificate and Store schemas.

Default additional spend is USD 0. Grok generation remains held under the
user's explicit instruction until quota recovery and the required account/cost
evidence are established. A reset timestamp or cached ping is not recovery.
Do not change billing, credentials or subscriptions to make a plan executable.

Only the implemented guarded Orca adapter may start a supported worker.
It currently covers registered local Claude/Codex flag-effort lanes, not
prompt-keyword/ultracode, Antigravity, Grok, remote or direct CLI execution.
Unsupported work remains blocked; the current host may do separately authorized
work within its actual capabilities, without claiming a model/effort switch.
D-67 이전의 종합 고정 `claude-opus-5` @ultracode 는 prompt-keyword 라 이 경계를
넘지 못했다. 2.14.0 은 종합을 `claude-opus-5-5` @max(flag)로 옮겼지만, 아래 조건 전에는
여전히 실행 경로가 아니다. 다른 레인을 끼워 넣어 계획 전체가 실행 가능하다고 주장하지 말고
정책·어댑터 불일치를 보고한다.
D-67(2026-10-04)로 현행 세대 레인 `claude-opus-5-5`(low~max)와 `gpt-6.1-sol`
(minimal~xhigh)이 옛 레인 옆에 **등록**됐다. 읽기 전용 canary 는 2026-10-04 에 **통과**했다
(두 레인 모두 `launch.requested` == `launch.effective`, 세부는 `references/model-catalog-map.md`).
그래서 상태는 `pending-transport-and-certificate` 다. native send 보류와 Orca 런치
계정/과금 인증서 부재가 그대로이므로 이 두 레인을 동작하는 경로로 쓰거나 보고하지 않는다.
$0 게이트(모델 포함·초과과금 OFF·API 폴백 OFF), G5, 런치 인증서는 기존 flag 레인과 똑같이 걸린다.
2026-10-05 Simon 지시(2.15.5)로 A 클래스 레인 `gpt-6-luna`(minimal~xhigh)와 `claude-sonnet-5-5`
(low~max, 정책 사다리 medium/high)도 옛 레인 옆에 **등록**됐고, 읽기 전용 canary 를 2026-10-05 에
통과했다(D-91, run `run_0a369252175f`). 상태는 `pending-transport-and-certificate` 다. Orca 런치
계정/과금 인증서 전에는 동작하는 경로로 쓰거나 보고하지 않고, 같은 $0 게이트·G5·런치 인증서가 걸린다.
D-99(2026-10-12, 2.16.0)로 A 클래스에 `claude-haiku-5-5`(low~max, 정책 사다리 low/medium)가 Claude 쪽 첫
폴백으로 **등록**됐다: `gpt-6-luna` → `claude-haiku-5-5` → `claude-sonnet-5-5` → `claude-opus-5-5`. 읽기 전용
canary 는 통과했다(run `run_8f7a27febc38`, @low, 정답이 정해진 A 과제 3/3). 상태는
`pending-transport-and-certificate` 이고 같은 게이트가 걸린다. 큰 입력·10만 토큰 초과 입력은 미측정이다.
D-98(2026-10-12 오전, 2.16.0)은 보안 생성물 게이트의 고정 레인을 `gpt-6.1-sol` @xhigh 로 옮겼었다. 같은 날 오후
D-101 이 되돌렸다(아래).
**D-101(2026-10-12, 2.17.0)은 패키지의 기존 기본 정책이다.** 현재 세션의 명시적 선호가 우선하며, 아래 구현 제약과 충돌하면 정책 불일치로 보고한다. 위의 D-67·10-05·D-99·D-98 문단은 그 시점 기록이다.
- GPT 쪽에서 일을 받는 레인은 `gpt-6-astra` 하나이고 effort 는 xhigh 고정이다("gpt 쪽은 astra 말고는 쓰지마. gpt 를
  넣어야한다면 astra xhigh."). 다른 effort 는 `off_ladder` 로도 ORCA_DISPATCH_UNSUPPORTED 다.
- `gpt-6.1-sol`·`gpt-6-luna`·`gpt-5.6-sol`·`gpt-5.6-terra`·`gpt-5.6-luna` 는 철회됐다. 계획에 넣으면
  ORCA_LANE_WITHDRAWN 이다. 결함 때문이 아니라 소유자 지시다(`gpt-6-luna` 는 D-91, `gpt-6.1-sol` 은 D-67·D-98
  canary 를 통과했다). 레인 키는 원장 호환용으로 남는다.
- A 클래스: `claude-haiku-5-5` → `claude-sonnet-5-5` → `claude-opus-5-5`. 전부 claude 라 claude 가 한도에 닿으면
  A 작업은 멈춘다. C-realtime: `grok-4.6` → `claude-opus-5-5` → `gpt-6-astra`. C-platform: `gemini-3.8-flash` →
  `claude-opus-5-5` → `gpt-6-astra`. B·A-verify(`gpt-6-astra` → `claude-fable-5-1` → `claude-opus-5-5`)·D·코딩은 그대로다.
  codex 가 80% 를 넘으면 astra 자리는 Claude 레인으로 강등된다.
- 코디네이터는 `gpt-6-astra` @xhigh 다. astra 는 인가 게이트이자 B 1순위라 겸임 경고가 자주 뜬다(경고일 뿐이다).
- 보안 생성물 게이트의 고정 레인은 `gpt-daybreak-blue-latest` @xhigh 다. 제공사는 이 별칭을 여전히 폐기 표시하고
  중앙 계획기는 packaged registry 로 MODEL_NOT_ACTIVE 를 낸다. 그래서 그 경로로는 Daybreak 게이트가 준비되지 않고,
  D-102 폴백(아래)이 게이트를 맡는다.
  레인 표의 ORCA_LANE_DEPRECATED 는 이 고정 자리(고정 effort xhigh) 하나만 통과시키고, 다른 공정·코딩·재시도·
  다른 effort 는 그대로 막는다.
- Daybreak 게이트 워커를 띄우기 전에 코디네이터가 `~/.codex/models_cache.json` 에 별칭이 은퇴·upgrade 표시 없이 남아
  있는지 확인한다. 없으면 Daybreak 로 띄우지 않고, 그 후보를 `available: false` 로 넣어 계획을 다시 세운다.
  게이트 출력이 비거나 차단되면 통과가 아니라 실패다 — 같은 실행을 폴백에 넘기지 않는다.
- **D-102(2026-10-12, 2.18.0, Simon 판정)**: Daybreak 가 설 수 없을 때만 `gpt-6-astra` @xhigh 가 생성물 게이트를 맡는다.
  계획기는 게이트 단계에 제시된 Daybreak Orca 후보가 전부 가용성 사유(MODEL_NOT_ACTIVE·MODEL_UNAVAILABLE 등)로 거부됐을
  때만 단계에 `gate_fallback`(고정 레인·폴백 레인·사유)을 남기고, 그 기록이 있어야 레인 표가
  ORCA_FIXED_LANE_OVERRIDDEN·ORCA_G1_SEC_SAME_MODEL 을 내지 않는다. Daybreak 후보를 빼면 폴백은 열리지 않는다
  (항상 넣는다). 요청에 `gate_fallback` 을 실어 보내도 계획기가 버린다. `prepare_orca`·`execute_orca` 는 저장된 기록을
  다시 검사하고 어긋나면 ORCA_PLAN_GUARD 로 멈춘다(계획기 코드는 ORCA_GATE_FALLBACK_INVALID). G1 은 면제하지 않는다 — 코딩이 codex 면 폴백 상태에서도 위반이다.
  폴백 상태에서는 한 모델이 두 보안 질문에 모두 답한다(두 게이트가 독립된 검사가 아니다).
  Simon 이 먼저 말한 Opus 폴백은 채택하지 않았다(`references/security-artifact-gate.md`).
- 게이트 워커의 과제문에는 `references/security-artifact-gate.md` 의 루브릭과 출력 형식을 넣고, 빈 출력·차단·
  첫 줄 누락·모호한 판정은 통과가 아니라 실패로 읽는다. 게이트는 자기 벤더(codex)가 만든 산출물을 채점하지 않는다(G1).
- canary 를 돌린 것은 Daybreak 게이트(run `run_b08adccb4ec8`)와 폴백 게이트로서의 astra(run `run_3607f8833d7e`)다.
  둘 다 심은 샘플 1건이다. 코디네이터로서의 astra 와 A 클래스 순서 변경은 canary 가 없다.

gpt-6-sol, grok-4.7, grok-4.5 로의 Orca 발주는 여전히
ORCA_UNREGISTERED_PROCESS_OR_MODEL 이다(`references/model-catalog-map.md`).

운영 주의(D-67 canary 2026-10-04 관측, 판정 아님):
- Orca 워커는 전권 모드로 뜬다. Claude 는 `--dangerously-skip-permissions`, Codex 는
  `--dangerously-bypass-approvals-and-sandbox`(sandbox `danger-full-access`)다. "읽기 전용"은
  과제문으로만 지켜진다. A-verify 같은 읽기 전용 레인의 전제를 Orca 가 강제한다고 보지 않는다.
- Codex 워커는 Orca runtime home 설정의 `service_tier="priority"` 를 물려받는다(상태줄 `fast`).
  이 tier 의 사용량 배수는 확인하지 못했다. 쿼터·비용 판단에서 standard 와 같다고 가정하지 않는다.
- 실제 /vibe 과제문은 워커가 `worker_done` CLI 호출을 하도록 허용해야 한다. canary 처럼
  "도구 금지"이면 워커가 `worker_done` 을 보내지 않아 Task 가 `blocked` 로 남고
  Dispatch 는 정상 정산되지 않고 `failed` 로 세어진다.

Legacy live functions `run_dispatch`, `run_codex_exec`,
`validate_and_dispatch`, `probe_orca_efforts` and adversarial live
preflight/run are disabled. No force flag, dry argv, shell command or manual
terminal submission bypasses that boundary. The raw `run_orca` helper accepts
only its exact read-only allowlist; it is not the dispatch adapter.

## Live Orca discovery

Use this check at each /vibe invocation, after an Orca update, or when a command
or model appears unavailable. It is skill synchronization/discovery, not a
second dispatch adapter. Run once per invocation, not before every leaf task.

1. Read the installed `orca-cli` discovery stub. Select its executable once
   using `ORCA_CLI_COMMAND`, then the documented dev/platform rule; keep that
   executable for the run. On Linux outside Orca, do not confuse the GNOME
   screen reader with Orca IDE. If discovery is unavailable, report the missing
   guide and use explicit executable `--help` only for read-only discovery.
2. Read `skills get orca-cli --json` from that executable. Use the helper below
   to preview and, when needed, update existing skills through the official
   `skills update --all --json` command without force. It rechecks the plan
   afterward. Then discover the complete current `skills list --json` catalog;
   choose relevant topics by description and retrieve only their guides.
   The executable's guide is authoritative for CLI syntax and lifecycle, not
   a copied old command list. Unsupported discovery/update commands mean a
   reported compatibility gap; use read-only help, never guessed mutations.
3. Compare the observed worktree ID and canonical path with the user-approved
   repository/workspace. `--worktree current` can still point to an old folder
   copy. A cwd change or matching basename is not sufficient. Missing or
   mismatched context blocks dispatch to that workspace; do not silently use
   another registered folder.
4. Observe the selected provider's current model catalog using its supported
   metadata command. Separate listed model IDs, supported transport efforts,
   requested effort and actual effective effort. A generic `--effort xhigh`
   flag does not prove that a particular model honors xhigh. Model visibility
   does not prove subscription inclusion or remaining quota. No generation
   call is needed just to discover commands or catalog entries.
5. Record skill source/version, executable/version, workspace binding, current
   session preferences, capability evidence and remaining gates separately.
   For update checks, compare the loaded skill with the authorized source and
   installation receipt. A marketplace version is not the embedded skill's
   version. Report divergence; update through the authorized source/install
   workflow and recheck the bytes, never edit a receipt to conceal drift.

| Observation | Report and next action |
| --- | --- |
| Current guide supports workers/messages, vibe adapter lacks that path | Adapter gap; do not report that Orca cannot communicate |
| Model is listed, exact effort unverified | Model listed / effort unverified; no silent downgrade |
| Historical preference rejects this session's explicit choice | Session policy conflict; preserve the request and execution gates |
| Account, quota or subscription proof missing | Evidence gap; do not label a supported command unavailable |
| Worktree is missing or points at a copy | Workspace mismatch; resolve the approved workspace before dispatch |
| Source and installed skill differ | Installation drift; report both versions and verify the update |

### Automatic skill update

```text
python -B "<skill>/scripts/orca_skills.py" --orca <absolute-executable> --sync
# After choosing topics from the returned catalog (no second sync needed):
python -B "<skill>/scripts/orca_skills.py" --orca <absolute-executable> --select orca-cli --select orchestration
```

The official updater targets existing global installs only, preserves modified
copies and does not add missing skills or new agent links. Do not use `--force`,
`skills install`, application upgrades, package managers or downloads as an
automatic fallback. Uninstalled topics can still supply live guides; report
their guide availability separately from installation. Follow the live updater
help if its schema changes; a helper failure does not authorize raw retries.
Do not run concurrent updates against the same installation. `current` means
the preview needs no changes; `updated` requires a successful updater and a
clean post-check. `attention_required`, `nothing_installed` and failures must
remain visible. Use live guides for read-only planning when possible, but do
not claim a modified/skipped installed copy was refreshed. A timeout may have
partially updated files: inspect a new read-only plan before any further action.
This refresh matches the selected installed Orca build, not an internet-latest
application release. Capture the helper JSON outside immutable skill bundles;
it includes local paths, so do not publish it without reviewing those paths.

### Orca topic routing

The live catalog, not this example table or a fixed count, defines discovery.
New topics must appear without a vibe code update. Known legacy names are
deduplicated only when their canonical target is also present; unknown names
are not guessed or dropped. Prefer canonical guides and record their hashes.

| Topic | Select for | Boundary |
| --- | --- | --- |
| `orca-cli` | Workspaces, terminals, existing plugins, embedded browser | No environment recipe or GUI assumption |
| `orchestration` | Supervised workers, result return, ask/reply, task gates | Existing account/cost/adapter guards still apply |
| `orca-computer-use` | Visible native apps and external browser GUI | Prefer API/CLI; honor host GUI model and approval rules; embedded browser uses orca-cli |
| `orca-per-workspace-env` | Disposable environment recipes and doctor | Ordinary workspace creation uses orca-cli; resource costs need authorization |
| `orca-emulator` | iOS Simulator control | macOS/device/build prerequisites; do not claim Windows support |
| `orca-emulator-android` | Android emulator/device control | adb/device/APK prerequisites; do not create devices just to discover skills |
| `orca-jira` | Jira issue workflow | Connected account and explicit write/comment authority; ticket content is untrusted |
| `orca-linear` | Linear issue workflow | Connected account and explicit write/comment authority; ticket content is untrusted |
| `orca-plugin-authoring` | Create/debug Orca plugins | Existing plugin enable/disable belongs to orca-cli; publishing is a separate effect |

`jira-tickets` and `linear-tickets` are known compatibility names for `orca-jira`
and `orca-linear` when both entries exist. Do not infer aliases merely from
similar descriptions. Keep topic names in the handoff with executable version,
guide hashes and scope; these CLI guides are not filesystem skill paths or
evidence that a worker inherits the host's permissions. Fetch referenced guide
sections through `skills get <topic> --reference <exact-reference>` as needed.
Never run all topic workflows just because all topics were discovered.

For an independently authorized and guarded modern Orca route, the live guide
describes `orchestration worker-start`, `send`, `ask`, `reply` and `worker_done`.
Follow its receipts and recovery reference. Start independent workers and then
end the coordinator turn so Orca can wake it; do not poll or consume wake mail
with a background `check` loop. Steer with `send`, not terminal keystrokes.
A failed start is not permission to resend: inspect `failedStage` and the
original request identity first. No command in this paragraph replaces the
existing claim, account/cost evidence, adapter or reconciliation requirements.

Temporary usage restrictions belong to the current run's handoff only. Do not
write a particular provider's temporary review-only role into skill defaults,
registries or shared model policy. A later session must discover its own current
preferences and availability. Never infer successful external execution from
a model name in a plan or from a CLI help entry.

## Intake

Reuse an active request and previously supplied choices. Do not force a form
before a known task. A small task can stay in the current session.

The existing `make_intake.py` is not a read-only preview: its main entrypoint
can collect downloaded decisions, write the legacy ledger and create HTML.
Review those effects and the exact paths before using it. Its account/repository
queries do not establish billing or model availability. Historical model panels
are examples, not automatic assignments; stale live evidence yields no eligible
exploration candidates. Do not run intake merely to test a report.

## Plan and prepare

1. Identify relevant skills/software, scope, acceptance evidence and prohibited
   actions. Read the selected skills. Split deterministic operations from
   judgment; record dependencies and explicit independent reviewers.
2. Use observed central registry/runtime facts to select model and effort.
   Provider and transport effort allowlists must both admit the value.
   Unknown billing/quota excludes a route; quota pressure is not free usage.
3. Construct the complete plan, including both required security gates, review,
   retries and synthesis. Preserve legacy full-plan guard constraints as an
   additional filter. A new model ID cannot override those constraints.
4. Validate offline with explicit skill roots/exclusions. A blocked plan starts
   no nodes. Independent safe work needs its own valid scoped plan; do not
   silently drop blocked requirements and report the original task complete.

```text
python "<skill>/scripts/orchestrate.py" plan --root <explicit-skill-parent> --exclude-root <protected-path> --input request.json --runtime runtime.json
python "<skill>/scripts/orchestrate.py" ready --input plan.json --events events.json
```

Repeat root/exclusion flags for the actual scope. These commands do not create
native Runs/Tasks, reserve money or dispatch. A user asking only for a plan does
not authorize those side effects. Do not label arbitrary local commands free:
review their argv, dependencies, hooks and exact cost contract.

Before dispatch the plan needs a unique existing native Run/Task, exact Task
spec, workspace ID/path/instance, pinned Orca executable/runtime and a fresh
launch-account certificate. The adapter does not create these resources.
The central guarded native preparation lifecycle is not yet implemented.
If those prerequisites cannot be established through an independently reviewed,
authorized preparation path, report the gap and stop that node. Do not restore
the old raw run-create/task-create path to get around it.

The spec builder is an offline inspection aid:
```text
python "<skill>/scripts/execute_orca.py" spec --plan plan.json --node ID
```
Its output fixes the Task intent; it does not set the native Task spec.
Never accept an unrelated prompt or a Task with a previous Dispatch.

Do not run generation as a tooling probe. Version metadata alone does not
establish launch compatibility. A zero-CPU process is not proof that a worker
is stuck or safe to kill; a prompt or input field is not authority to submit it.
Updates and startup hooks can affect other sessions and require their own scope.

## Dispatch and recovery

Use the same canonical local Store DB and the existing immutable grant.
Register the complete plan to reserve all attempts and review costs atomically.
Never create another DB/grant to escape an exhausted allowance.
Do not manually claim a node before calling the adapter: claim and send belong
to that adapter invocation, and a committed no-send intent can remain unresolved.

For an already registered, eligible node with all preparation evidence:
```text
python "<skill>/scripts/execute_orca.py" dispatch --plan plan.json --node ID --db <shared-db> --certificate account-proof.json
python "<skill>/scripts/execute_orca.py" reconcile --plan plan.json --node ID --db <shared-db>
```

These are conditional execution commands, not offline validation commands.
The adapter repeats identity/freshness checks and calls Store.claim internally.
Only that fresh claim may send once. A saved dispatch_allowed flag, a dry
command or a successful planner result is not dispatch authority.

Persist the original dispatch identity. Reentry is lookup-only; timeout,
nonzero CLI exit, missing output or an unobserved turn do not prove non-acceptance.
Do not submit Enter, retry under a new Task/key, increase timeout and resend,
or use direct CLI as automatic recovery. Unknown acceptance or actual cost
keeps the reservation held until reconciliation. Retry requires terminal proof,
settlement, fresh preflight and the existing attempt/authorization limits.

Use exact resolved workspace identity; changing cwd does not establish where
an Orca worker will run. The adapter pins the executable rather than relying
on the legacy PATH runner. Read argv as data, never concatenate free text into
shell commands.

## Verification and cleanup

Accepted dispatch, turnStart, worker_done prose and exit zero are not completion.
Require matching native Task/Dispatch/workspace identity and terminal state;
record requested model/effort separately from resolved model/effective effort.
Applied launch settings are not proof of internal model reasoning or an invoice.

Inspect actual output, handle clipping and attach acceptance evidence. The
adapter's digest is not content review. A writer's result is output-ready only;
general/transitive successors wait for all explicit reviewers. The writer and
its independent reviewers must have different model vendors. Grok and Grok Bot
are both xAI; another same-host agent is not cross-vendor evidence.
Preserve artifact-safety and authorization/business-logic gates and their
separate-model constraints. Missing review routes block approval, not the rule.

For UI work use the repository's actual preview command and available approved
viewer, inspect pixels and accessibility evidence, and retain requested human
approval. Do not assume Expo, a port, a browser capability or screen visibility.
Only genuinely GUI-only operations belong to the separate vibe-bot adapter.

Actual cost settlement is distinct from output acceptance. Unknown actual_usd
stays null and retains its reservation. A subscription label, quota delta or
short answer is not a zero-cost receipt. Report provider overspend if observed.

Cleanup is not automatic. The adapter does not stop, abandon or release workers,
switch native Runs, delete worktrees or alter payment settings.
`kill_worker.py` is retired and cannot inspect or terminate processes. Every
legacy request, including the former dry path, fails with exit2 and
`LEGACY_WORKER_TERMINATION_DISABLED`; standalone help alone returns0. Do not use
an old installed copy or treat this diagnostic as proof of cleanup. Raw
worker-stop remains disabled, and the G8 safe-stop requirement is still unmet.

Official Orca 1.4.206 supervised stop can close an exact proven owned terminal;
unsupervised Dispatch fencing does not imply process exit. The future guarded
integration must bind authorization and a durable stop intent to the exact
Store/native target and verify the result. It is not provided by the retired
script. A timeout, low CPU, unreadable process or missing receipt authorizes no
OS kill, stop, retry or reservation release. Preserve dirty worktrees and obtain
applicable exact-target authorization before destructive action. No daemon.

## Records and evaluation

Keep central durable state for every node, reservation, observation, receipt
and verification. The legacy routing ledger only accepts its existing worker
schema; do not put Bot lanes, credentials, output bodies or new money fields
into it. Link records with run/node identities and read partial/CAS failures.
Do not commit other agents' records or silently consume files as a dry test.

For actual Orca decision rounds retain the decision-sheet/acceptance process.
A generated sheet is not a worker result, measured adoption or user approval.
Legacy aggregation can propose a change only from suitable measured rows;
it cannot activate routes or override current registry/account/cost gates.
Exploration must satisfy the same authorization, budget, availability and
verification requirements; no eligible alternative means no exploration.

The old direct-CLI adversarial runner is quarantined. See the evaluation
reference linked from SKILL.md for offline command effects and measurement
requirements. Schema/dry/fixture PASS is not per-skill live behavior evidence.

Report plan, dispatch, received result, verification and settlement separately.
Include blocked/skipped work, actual unknowns, remaining cleanup and evidence.
Do not mark five-surface integration, all-mode optimization or installed parity
complete from this source workflow. Historical troubleshooting remains in Git
history; old pitfalls/effort-cap instructions cannot override these boundaries.

## Verification commands

```text
python -B "<skill>/scripts/test_runtime_collect.py"
python -B "<skill>/scripts/test_run_state.py"
python -B "<skill>/scripts/test_execute_orca.py"
python -B "<skill>/scripts/test_model_registry.py"
python -B "<skill>/scripts/test_orchestrate.py"
python -B "<skill>/scripts/test_execute_codex_cli.py"
python -B "<skill>/scripts/selftest.py"
python -B "<skill>/scripts/sync_skill_table.py" --check
# Process-denied preparation fixtures, from the skill's scripts directory:
python -B -m unittest discover -s tests -p "test_prepare*.py"
# Secret detection equivalence/latency; denies child processes and networking:
python -B -I -S tests/test_ledger_scan.py
```

When testing an immutable bundle, also set `PYTHONDONTWRITEBYTECODE=1` for
child Python processes and reverify its receipt afterward. `-B` on the parent
command alone does not propagate to subprocesses. Plain Python invocation of
legacy CLI entrypoints now blocks bytecode before their first local import;
module imports by other callers still need the caller's own no-bytecode policy.
