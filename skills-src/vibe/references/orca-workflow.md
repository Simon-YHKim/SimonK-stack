# Orca execution workflow

## Contents

- [Intake](#모드-a--인테이크-폼-인자-없이-vibe)
- [Execution](#모드-bc--실행)
- [Observation and cleanup](#4-탐색-슬롯--라운드당-1개)
- [Ledger and guardrails](#집계--스왑-제안)

This is the retained Orca worker workflow. The umbrella SKILL.md determines
whether a worker is needed and gates total cost first. Intake is opt-in for a
known task. Only ready nodes may start; a submitted task is not a completed task.
Use the full-plan guards before each ready wave and preserve every G1–G14 rule.
The original model/effort table remains generated from routing.py until the
central registry migration passes its runtime gates.

## 모드 A — 인테이크 폼 (인자 없이 `/vibe`)

```bash
python "<skill>/scripts/make_intake.py"
```

출력 경로(`E:\Coding Infra\reports\vibe-intake.html`)를 브라우저로 열고 **거기서 멈춘다.**

폼이 실행될 때마다 하는 일:
1. **4벤더 쿼터**를 각각 읽는다 (`orca account list --json` 하나로 claude/codex/gemini/grok 전부 나온다)
2. 쿼터를 반영해 **클래스별 기본 레인을 미리 채운다** — 안 건드리면 그대로 간다
3. **다운로드 폴더의 `decisions_run_*.json`을 자동 회수**해 원장에 합치고 파일을 소비한다
4. 미회수 run이 3개 이상이면 **"학습 정지 상태"** 경고를 띄운다

폼을 연 뒤 한 줄만 말한다: *"폼에서 고르고 [복사] 눌러 붙여넣어 주세요."* **추측으로 먼저 시작하지 않는다.**

## 모드 B/C — 실행

### 0-A. 툴체인 최신화 — 쿼터보다 먼저 본다

```bash
python "<skill>/scripts/check_tooling.py"     # 뒤처졌으면 종료코드 1
```

**codex 가 한 버전만 뒤처져도 전 워커가 안 뜬다.** 그런데 에러가 프롬프트 문제처럼 보인다:

```
dispatch 실패 → lastError: agent_prompt_blocked          ← 내용 탓으로 오독하기 쉽다
최소 프롬프트로 갈라보면 → Agent startup blocked: codex-update-prompt
```

2026-09-12 에 이걸로 스펙을 두 번 다시 썼다. 원인은 codex-cli 0.153.4 / 최신 0.154.0 이었고,
올리니 세 워커가 그대로 떴다. **갈라보는 방법은 최소 프롬프트 한 줄을 같은 레인에 던지는 것**이다 —
그래도 막히면 내용이 아니라 툴이다.

이 스크립트는 **자동으로 설치하지 않는다.** 전역 npm 패키지는 같은 머신의 다른 세션에 영향을 준다.
올리기 전에 실행 중인 codex 프로세스를 보고, **CPU 0초로 멈춰 있으면 그것도 이 프롬프트에 걸린
워커다**(죽여도 된다). 일하는 중이면 기다린다.

`orca skills list` 스냅샷도 같이 대조해 추가·삭제·설명 변경을 알린다
(`state/orca-skills.json`). 변경이 보이면 그 스킬 문서를 다시 읽는다 — 오르카의 명령 정본은
이 문서가 아니라 `orca skills get <이름>` 이다.

### 0. 프리플라이트 — 건너뛰지 않는다

```python
import sys; sys.path.insert(0, "<skill>/scripts")
import routing
ok, status = routing.run_orca_json("status")
ok, acct  = routing.run_orca_json("account", "list")   # 4벤더 각각
```

- 어느 벤더 80% 초과 → **그 레인을 쓰는 태스크만** 다음 순위로 강등 (Q-260913-05: 60→80)
- 어느 벤더가 한도 100% 도달 또는 실호출 실패 → 그 레인 사용 금지(Q-05: 85→100). 후보가 없으면 **축소안을 제시**하고 승인받는다 · 한도에 걸려 실패·정지한 워커는 `handoff_spec` 으로 여유 레인에 인수인계(G4)
- 읽기 실패 → **"미확인"**으로 표시하고 1순위 유지. **0%로 간주하지 않는다**
- `claude.fableWeekly` 100%면 fable을 워커로 쓰지 않는다

### 1. 공정 분류 → 클래스 → 레인

과제를 공정으로 쪼개고 각 공정을 위 표의 클래스에 넣는다. **디스패치 결정과 학습 집계는 클래스 단위로만 한다.**

태스크마다 **반증질문**에 예/아니오를 정한다(폼 답이 있으면 그대로, 없으면 **아니오**):
> 반증 가능한 전제가 있나? — "X는 죽었다"를 확인 / "A가 B보다 낫다"를 판정 / 원인 규명

**착수 전 한 줄로 알린다**: 분류 결과 · 예상 워커 수 · 어느 태스크가 탐색 슬롯인지.

### 2. Run + 작업 DAG

```python
ok, run  = routing.run_orca_json("orchestration", "run-create",
                                 "--objective", objective)          # 인용 불필요
ok, task = routing.run_orca_json("orchestration", "task-create",
                                 "--run", run["run"]["id"],
                                 "--spec", spec)                    # 인용 불필요
```

`objective`·`spec` 은 사람이 쓴 자유 문자열이다. `run_orca_json()` 은 셸을 거치지 않으므로
`$(...)`·`;`·백틱이 확장되지 않는다. **셸 문자열로 조립해 실행하지 말 것.**

추가 조건에 **"먼저 계획만"**이 있으면 여기서 `task-list --brief --json`을 보여주고 **종료한다**(비용 0).

### 3. 워커 기동 — effort를 반드시 박는다

**전체 계획 검증 → 준비된 노드만 실행**한다. `routing.validate_plan()`에 보안
게이트를 포함한 전체 Orca 배정을 전달하고, `orchestrate.ready_steps()`가 연 노드만
`routing.run_dispatch()`로 실행한다. DAG 전체에 `validate_and_dispatch()`를 부르면
후속 단계가 조기 실행되므로 금지한다. 반대로 coding만 검증하면 필수 게이트가 빠진다.
필수 보안 게이트 · 4벤더 쿼터 · 금지 레인 · 고정 레인 규칙은 그대로 유지한다.

```python
import sys; sys.path.insert(0, "<skill>/scripts")
import routing, orchestrate

# plan/runtime/events는 최신 검증 스냅샷. task_of/spec_of의 키는 proc가 아닌 node ID.
nodes = [n for n in plan["steps"] if n["route"].get("transport") == "orca"]
assignments = [dict(proc=n["proc"], **{"class": n["class"]},
                    lane=n["route"]["model"], effort=n["route"]["requested_effort"],
                    writes=n.get("writes", False), off_ladder=n.get("off_ladder", False),
                    falsifiable=n.get("falsifiable", False)) for n in nodes]
ok, violations, notes = routing.validate_plan(
    assignments, quota_checked_vendors=runtime["quota_checked_vendors"],
    quota_states=runtime["quota_states"], spawn_counts=spawn_counts)
if not ok:
    raise SystemExit(f"계획 검증 실패: {violations} {notes}")

# 전체 배정의 argv/spec까지 dry-run. 이 루프에서는 워커를 띄우지 않는다.
for node, assignment in zip(nodes, assignments):
    routing.run_dispatch(assignment["lane"], assignment["effort"], task_of[node["id"]],
                         node["id"], worktree="current", spec=spec_of[node["id"]],
                         allow_off_ladder=assignment["off_ladder"], dry=True)
ready = set(orchestrate.ready_steps(plan, events))
for node, assignment in zip(nodes, assignments):
    if node["id"] not in ready:
        continue
    # 호스트: run_id/plan_digest/node ID와 running 이벤트를 먼저 영속화한다.
    rc, out, err, meta = routing.run_dispatch(
        assignment["lane"], assignment["effort"], task_of[node["id"]], node["id"],
        worktree="current", spec=spec_of[node["id"]],
        allow_off_ladder=assignment["off_ladder"])
    # 호스트: 응답/dispatch ID 저장. rc=0은 접수일 뿐 검증 완료가 아니다.
    if rc != 0:
        break  # 실패 비용을 남기고 다음 wave 전에 재계획한다.
```

낱개로 부를 때도 서명을 지킨다 — **`worktree` 는 필수**이고 반환은 **4개**다:

```python
rc, out, err, meta = routing.run_dispatch(
    "claude-opus-5", "ultracode", task_id, worker_name, "current", spec=spec)
# meta["spec"] 을 그대로 task-create --spec 으로 넣어야 ultracode 가 실제로 발동한다.
# spec 없이 최상위 claude 를 부르면 ValueError 로 막힌다 — meta 에만 남고
# 워커에는 전달되지 않아 조용히 표준 effort 로 도는 것을 방지한다.
```

⚠ **배열을 문자열로 다시 합치지 말 것 (감사 HIGH-6, 2026-09-04).**
argv 배열을 문자열로 이어 붙여 셸에 넘기면 안전성이 사라진다 — 워커 이름이
`safe; Write-Output X`면 배열에서는 한 인자지만, 이어 붙인 문자열을 셸이 읽으면
두 명령으로 갈라진다. `dispatch_argv()`는 **표시·검토용**이고 실행은
`run_dispatch()`가 `shell=False`로 한다. 확인만 하려면 `dry=True`가 argv 를 JSON 으로 돌려준다.

**orca 호출은 전부 `routing.run_orca()` / `run_orca_json()` 하나로 한다.**
timeout·returncode·stderr redaction 이 그 안에 있다. 자유 문자열은 그냥 인자로 넘기면 된다 —
셸을 거치지 않으므로 인용이 필요 없고, 인용으로 막으려 하지도 말아야 한다.

⚠ **"PowerShell 로 부르면 안전하다"는 생각은 틀렸다.** PowerShell 도 큰따옴표 안의
`$(...)`를 확장한다. Git Bash 는 거기에 더해 `/`로 시작하는 인자를 경로로 바꾼다
(`/vibe …` → `C:/Program Files/Git/vibe …` 로 실제 오염된 적이 있다).
**어느 셸이든 자유 문자열을 명령 문자열에 넣지 않는 것이 유일한 방어다.**

| 레인 | 나오는 형태 |
|---|---|
| codex | `--model <slug> --effort <값>` — **빼면 sol·astra·daybreak 이 조용히 기본값(low/medium)로 돈다** |
| grok · agy | `--agent` 만. **`--model` 을 주면 거부**되고, `--effort` 는 `--model` 을 요구하므로 **effort 지정 자체가 불가능**하다 — 그 CLI 의 기본값이 쓰인다 |
| claude | `--model claude-opus-5 --effort max` + **프롬프트 첫 줄에 `ultracode`** |

**정책 밖 effort 를 쓰려면 명시한다.** 기본 경로는 `top`/`std` 두 단이고, 그 밖의 값(예: 라운드가 가벼워서 `astra@medium` 으로 내리고 싶을 때)은 `allow_off_ladder=True` 를 붙여야 열린다. 원장에 `off_ladder` 로 남는다.

```python
plan = [{"proc": "research-deep", "lane": "gpt-6-astra", "class": "B",
         "effort": "medium", "off_ladder": True}]   # 의도한 하향임을 명시
```

`ultra`·`max` 를 astra·daybreak 에 주면 **계획 검증에서 `EFFORT_NOT_ALLOWED` 로 막힌다** — 한 건도 디스패치되지 않는다. Orca 가 안 받는 값이기 때문이고, 이건 정책이 아니라 물리적 사실이다.

워커 과제 서술에 반드시 넣는다: 검증 가능한 완료조건 · 건드리지 말 것 · **레인별 산출물 제약**(위 표) · 끝나면 `worker_done` 보고.

**배정 검증** — 디스패치 전에 돌린다:
```python
routing.check_guards(assignments, quota_checked_vendors, spawn_counts)   # G1·G3·G5·탐색오배정
routing.coordinator_conflict(assignments)   # 코디네이터 레인이 워커를 겸임(클래스 무관, D-28 #6) · 재시도 전엔 revalidate_for_retry()(G13)
```

✅ **D-260904-01 — 보안 검사 배정 (Simon 결정, 2026-09-04)**

판단이 가능한 벤더는 **claude·codex 둘뿐**인데 역할은 셋(구현·생성물검사·인가검사)이다. 셋을 모두 다른 벤더에 두는 배치는 **존재하지 않는다**(비둘기집). 그래서 우선순위가 낮은 제약을 양보했다.

| | 배정 | 벤더 |
|---|---|---|
| 코딩 (공정 전용 목록 `PROCESS_LANES`, D-28 #5) | `claude-opus-5` | claude |
| 생성물 안전성 게이트 | `gpt-daybreak-blue-latest` @xhigh | codex |
| 비즈로직·인가 게이트 | `gpt-6-astra` @xhigh  *(2026-09-06, 직전 `gpt-5.6-terra` @high)* | codex |

- **지킨 것** — 코딩 ≠ 두 게이트 모두. **자기채점 0.** G1을 HARD로 승격했고 `G1_BIZLOGIC` 임시 분기는 없앴다
- **양보한 것** — 두 게이트가 같은 codex 벤더가 되는 것(발주 §5 한 줄). 대신 **다른 모델**을 강제한다: `daybreak@xhigh` vs `astra@xhigh`. 같은 모델이 두 축을 겸하면 `G1_SEC_SAME_MODEL`로 잡는다
- ⚠ **2026-09-06 로 구분자가 바뀌었다.** 예전에는 "모델도 effort 상한도 다르다"였는데 astra 와 daybreak 은 **상한도 effort 도 둘 다 xhigh** 다(둘 다 Orca 의 `unknownModelOptions` 로 떨어지기 때문이다). 지금 두 게이트를 가르는 것은 **모델 성격**이다 — daybreak 은 `model_specialty="cyber"` 전용, astra 는 범용 프론티어. "상한이 달라서 안전하다"를 근거로 인용하지 말 것

> **2026-09-04 갱신 — 생성물 게이트를 `gpt-5.6-sol` → `gpt-daybreak-blue-latest` 로 옮겼다.**
> Simon 이 codex 모델 선택지에서 찾아냈다. 정본은 `~/.codex/models_cache.json`:
> display_name **"Daybreak Blue"**, *"Latest frontier agentic coding model for
> broad defensive cybersecurity work."* — **보안 전용 프론티어 모델**이다.
> sol 은 범용 워크호스("Reliable agentic workhorse")였으니, 보안 자리에 보안 모델을 놓는다. *(D-28 #16: 2026-09-13 models_cache 에서 sol 은 priority 1 "Latest frontier agentic coding model." 로 바뀌었다 — 이 문장은 09-04 기록이다)*
> 벤더는 여전히 codex 라 위 양보는 그대로고, 개선된 것은 **모델 적합성**뿐이다.
> 부수 효과로 sol 이 게이트에서 풀려 **코디네이터 겸임 충돌이 사라졌다.**
> ⚠ daybreak 도 **기본 effort 가 low** 다 — sol 과 같은 함정. effort 명시는 코드가 강제한다.

> **⚠ 전제 — codex 보안 게이트는 Trusted Access 승인이 있어야 작동한다 (2026-09-04 실측).**
> 승인이 없으면 codex는 감사를 **수행하고도 결과 출력만 차단**한다:
> `This content can't be shown / We take extra caution with cybersecurity requests`.
> 이건 **조용한 실패**다 — `worker_done`이 안 오고 산출 파일도 안 쓰이며 태스크가
> `dispatched`에 멈춘 것처럼 보인다. 진단은 `orca terminal read` 로 터미널 실물을 읽는 것뿐이다.
> 신청처는 `https://openai.com/daybreak/` (= Trusted Access). Simon 계정은 2026-09-04 승인 완료.
> **승인이 없는 계정·머신에서는 이 배정을 쓰지 말 것** — 게이트를 claude 로 돌리되
> 구현자와 벤더가 겹치지 않는지 반드시 확인한다.

> 지시는 "두 게이트가 같은 codex가 되면 생성물게이트를 claude로 맞바꿔라"였으나, 그렇게 하면 코딩과 생성물게이트가 모두 claude가 되어 **짠 쪽이 자기 산출물을 검사하는 HARD G1**이 된다. 옮기려던 문제보다 나쁘다. `selftest.py`의 "정본 기본 배정이 가드를 통과한다" 케이스가 이걸 잡는다 — 표를 고칠 때마다 여기서 걸린다.

### 3-2. codex 직행 — Orca 상한을 넘어야 할 때만

Orca 워커로는 astra·daybreak 에서 `xhigh` 가 끝이다. 그 위가 필요하면 codex CLI 를 직접 부른다.

```python
rc, out, err = routing.run_codex_exec(
    prompt,                       # stdin 으로 들어간다 — 인자로 넣지 않는다
    model="gpt-6-astra", effort="ultra",
    sandbox="read-only",          # 기본값. 격리가 없으니 쓰기는 워커로 보낸다
    cwd=worktree_path, timeout=1800)
```

**이건 워커가 아니다.** 차이를 알고 쓴다:

| | Orca 워커 | codex 직행 |
|---|---|---|
| 워크트리 격리 | 있다 | **없다** — 이 셸의 cwd 에서 돈다 |
| `worker_done` · 게이트 · `worker-release` | 있다 | **없다** — 동기 블로킹 호출 |
| 원장 dispatch 행 | 자동 | **직접 넣어야 한다** |
| 도달 가능한 effort | astra `xhigh` 까지 | `max` · `ultra` 까지 |

- 쓸 자리: 워커 하나를 통째로 띄울 값어치는 없는데 **최상단 추론이 필요한 단발 판정**
- **G1 은 그대로다** — 짠 쪽을 이 경로로 우회시켜 자기 산출물을 검사하게 하지 말 것
- 기본 `sandbox="read-only"` 를 올리기 전에 "워커로 보내면 되는 일 아닌가"를 먼저 본다

## 4. 탐색 슬롯 — 라운드당 1개

A 클래스 태스크 하나(없으면 B의 비고정 공정)를 **2순위 레인**으로 강제 배정하고 `explore:true`로 기록한다.
- 후보 중 **무작위**로 고른다 — 항상 첫 태스크를 고르면 난이도 편향이 생긴다
- **제외**: D · 보안 게이트 2종 · 코딩(공정 전용 목록 — 2순위 없음) · 되돌릴 수 없는 태스크 · 2순위가 Orca 로 안 뜨거나 실호출에 실패한 공정 — 후보는 `routing.explore_candidates()` 결과만 (D-28 #12)
- 추가 조건에 "탐색 슬롯 끄기"가 있으면 건너뛴다

### 5. 디자인 게이트 — 로컬호스트 컨펌

`화면 확인`이 "로컬호스트"면 디자인 워커 과제 서술 끝에 못박는다:
*"끝나면 `npx expo start --web --port <할당포트>`로 서버를 **띄운 채로 두고** worker_done을 보고할 것."*

```python
routing.run_orca_json("tab", "create", "--url", f"http://localhost:{port}")
routing.run_orca_json("screenshot", "--format", "png")        # 내가 먼저 픽셀 확인
routing.run_orca_json("orchestration", "gate-create", "--task", task_id,
                      "--question", f"localhost:{port} 컨펌?",
                      "--options", '["통과","재작업"]')
```

포트는 워크트리마다 `8090`부터. **명백히 깨진 화면은 올리지 않는다.** 대기 중에도 다른 단계는 계속 돌린다.

### 6. 수확 · 정리

```python
ok, res = routing.run_orca_json("orchestration", "check", "--run", run_id, "--wait",
                                "--types", "worker_done,escalation,question",
                                "--timeout-ms", 900000, timeout=960)
routing.run_orca_json("orchestration", "worker-release", "--dispatch", dispatch_id)
routing.run_orca_json("worktree", "set", "--worktree", "active",
                      "--comment", comment,                  # 자유 문자열
                      "--workspace-status", "in-progress")
```

`worker_done`은 **성공·실패 모두** release 대상. 타임아웃·유휴·질문은 release 사유가 **아니다**.

⚠ **G4** — 쿼터를 근거로 **실행 중인 워커를 중단시키지 않는다.** 직전 라운드에서 이 오판으로 최고 품질 워커를 죽였다(고아로 1h17m 더 살아 완성했다). 03:00에 쿼터 읽기가 0%로 실패한 실적도 있다.

### 6-2. 워커 강제종료 (G8) — 2026-09-13 문서화 · 실측

`worker-stop` 은 **Dispatch 를 fence 하고 터미널을 멈춘다**까지만 약속한다 — 프로세스가 죽었다는 약속이 아니다(help 원문). `worker-abandon` 은 프로세스에 손대지 않고, `worker-release` 는 끝난 워커의 터미널만 닫는다. `terminal show` 는 PID 를 주지 않는다(ptyId 만).

대신 **워커 셸과 에이전트가 전부 환경변수 `ORCA_TERMINAL_HANDLE=<handle>` 을 갖는다.** 구조는 `Orca.exe(터미널 호스트) → pwsh(터미널마다) → claude.exe · agy.exe · codex → 도구 하위 프로세스` 이고, 코디네이터 세션은 **다른 handle** 이다. 그래서 dispatch → handle → 환경변수로 정확히 그 워커 트리만 고른다. handle 은 `worker-list --json` 의 `agentTerminalHandle` 이다.

```bash
python "<skill>/scripts/kill_worker.py" --dispatch ctx_…               # 목록만 (기본)
python "<skill>/scripts/kill_worker.py" --dispatch ctx_… --kill --fence
#   terminate → 8초 대기 → kill → 재스캔. left_after 가 [] 이고 verified 가 true 여야 끝난 것이다
#   종료코드: 0 확인됨 · 1 잔존 · 2 handle 못 찾음 · 3 자기 자신/조상이 대상에 섞임(거부)
```

- 대상은 **handle 이 같은 프로세스 + 그 자손**이다. 워커가 띄운 에뮬레이터 · adb 도 환경변수를 물려받으므로 같이 내려간다
- 자기 터미널 handle 이거나 **이 스크립트의 조상 PID** 가 섞이면 아무것도 하지 않고 3 으로 끝난다 — 코디네이터가 자기 세션을 죽이는 사고를 막는다
- 실측(2026-09-13 21:16): 폴더 신뢰 프롬프트에 걸려 과제를 못 받은 agy 워커 → 대상 2개(agy.exe · pwsh.exe) terminate 로 전부 종료 · 재스캔 0 · worker-stop ok · 터미널 목록에서 사라짐. 코디네이터 트리는 건드리지 않았다
- 강제종료한 task 는 `failed` 가 되어 재디스패치가 안 된다 — 같은 spec 으로 **새 task** 를 만든다
- 쓰기 워커를 죽였으면 그 워크트리의 미커밋 변경을 **지우기 전에 본다**(`git --no-optional-locks status`). 워커 산출물을 버릴지는 사람이 정한다

⚠ **워커에 과제가 안 들어가는 증상 — 2026-09-13 에 다섯 번 봤다(agy 2 · claude 2 · codex 1).** 겉모습이 같다: 워커 TUI 는 떴는데 입력창이 비어 있고, `worker-show` 의 stage 가 `input_accepted` 또는 `turn_start_unobserved` 에 머문다. 그대로 두면 계속 논다.
- **claude 1건은 고쳐졌다.** 첫 `worker-start` 가 rc=1 로 끝났고(출력은 못 잡았다) task 가 `blocked` 가 됐는데 워커 터미널은 살아 있었다. `--worktree id:<repoId>::<경로>` + `--timeout-ms 300000` 으로 **새 task** 를 띄우자 응답에 `turnStart: observed` 가 오고 과제가 들어갔다. "기본 대기 시간 안에 에이전트 턴이 시작되지 않으면 CLI 가 먼저 끝나고 과제 입력이 사라진다"는 **추론**이다 — 재현 1회로 고쳐진 것만 확인했다
- **claude 2번째(22:16)는 `id:` + `--timeout-ms 300000` 을 처음부터 줬는데도 났다.** 방금 `git worktree add` 한 **새 워크트리의 첫 기동**이었다. `worker-start` 는 `cli_failed rc=1`(stderr 빈 값), `worker-show` 는 `start_unknown` · "input was written and submitted, but turn start could not be verified (up to 30s)", `terminal read` 의 `draft:` 에는 과제 전문이 있는데 **화면 입력창은 빈 `❯`** 였다. 복구: `kill_worker.py --kill --fence`(7프로세스 · 재스캔 0) → `task-update --status failed` → **같은 task 에 `worker-start --retry-of <죽인 dispatch>`** 를 같은 워크트리 · agent 로 다시 → `turnStart: observed`. 두 번째 기동은 그 폴더를 이미 한 번 연 뒤라 빨랐다는 것은 **추론**이다. 새 워크트리로 보낼 때는 첫 시도가 이렇게 날 수 있다고 보고, 응답의 `turnStart` 부터 본다
- **agy 2건은 원인 미확정이다.** 한 번은 처음 여는 폴더의 `Do you trust the contents of this project?`(`agentWait.reason = codex-trust-workspace`)에 막혔고, Enter 로 기본값을 주는 사이 과제가 사라졌다. 두 번째는 신뢰가 끝난 폴더에서도 입력창이 5분 넘게 비었다 — 위 claude 와 같은 타임아웃이었을 수 있는데 **agy 를 `--timeout-ms` 로 다시 띄워 보지는 않았다.** 손으로 과제를 보내면 dispatch 별 `--dispatch-capability` 토큰이 없어 `worker_done` 을 못 보낸다
- **codex 1건(astra, 22:32)은 `turnStart: observed` 가 거짓이었다.** 응답은 observed 였는데 50분 뒤 보니 `worker-show` 단계가 `input_accepted` · 하트비트 0 · codex 프로세스 CPU 15초였고, 화면 입력창에 `[Pasted Content 3026 chars][Pasted Content 4125 chars]` 가 **전송 안 된 채** 걸려 있었다. 복구: `orca terminal send --terminal <handle> --enter` 한 번 → 곧바로 `Working` 으로 바뀌었다. **dispatch 가 그대로라 `worker_done` 토큰도 산다**(죽이고 재발주하는 것보다 싸다). ⚠ `--wait-submit` 은 `--text` 없이 쓰면 `invalid_argument` 다 — Enter 만 보낼 때는 빼고, 확인은 화면(`terminal read --screen`)으로 한다
- → 디스패치 응답의 `turnStart` 가 `observed` 여도 **몇 분 뒤 한 번 더** 본다 — 하트비트가 없고 화면에 붙여넣은 과제가 남아 있으면 먼저 `terminal send --enter`, 입력창이 비어 있으면 아래 절차다. `observed` 가 아니면 `kill_worker.py --kill --fence` 로 내리고 **새 task** 를 `--timeout-ms` 를 늘려 띄운다. gemini 레인은 `--timeout-ms` 로 한 번 재확인하기 전까지 Orca 워커 배정을 피하고, 꼭 필요하면 CLI 직행(`agy --print`)이다 — D-28 #12 로 routing.py 에서 `dispatch: unavailable`(해제 조건 M6)

⚠ **`--worktree current` 는 cwd 가 아니라 코디네이터 터미널의 워크트리다 (2026-09-13).** Orca 터미널 안에서 도는 세션은 환경변수 `ORCA_WORKTREE_ID` 를 갖고 `worker-start --worktree current` 는 그걸 쓴다. 전용 워크트리로 `cd` 한 뒤 불렀는데도 워커는 **코디네이터 워크트리**에서 떴다 — `orca worktree current` 명령만 cwd 를 본다(둘이 다르다). 쓰기 워커를 다른 워크트리로 보내려면 `--worktree id:<repoId>::<절대경로>` 를 쓰고, `orca worktree show --worktree id:…` 로 먼저 풀리는지 본다. 옛 기록("Orca 터미널 밖 셸에서는 `current` 만 통과")과 결과가 다른 이유는 코디네이터가 Orca 터미널 안에 있느냐로 보인다(추론)

⚠ **코디네이터 터미널 하나는 run 하나에만 묶인다.** `run-create` 가 새 run 으로 **다시 묶는다.** 그 뒤 옛 run 에 `check` · `task-update` · `worker-release` 를 부르면 `consumer_fenced`(`bound to <새 run>, not <옛 run>`)로 거부된다 — `task-list` 같은 읽기는 된다. 두 라운드를 겹쳐 돌리면 결과는 `task-list` 의 `result`(worker_done 본문이 들어 있다)로 읽고, 옛 run 을 정리할 때만 `orchestration run-use` 로 다시 묶는다

### 7. 결정 시트 → 채택률

```bash
python "<skill>/scripts/make_decision_sheet.py" <items.json> [출력.html]
```

항목마다 **어느 레인이 냈는지** 배지로 표시된다. Simon이 체크하고 **[결과 저장]**을 누르면 `decisions_<run_id>.json`이 다운로드되고, **다음 `/vibe` 실행 때 자동으로 원장에 합쳐진다.** Simon이 외울 새 명령은 없다. **이 시트 없이는 라운드가 끝나지 않는다(G14 · D-28 #15)** — 손으로 조립한 시트는 회수 경로가 없다.

### 8. 원장 append — 마지막 단계

```python
import ledger

# ⚠ orca 응답 객체를 그대로 넘기지 말 것 — ID 문자열을 꺼내서 넣는다.
#   run["run"]["id"] 같은 dict 를 넘기면 strict schema 가 거부한다.
run_id = run_result["run"]["id"]            # "run_26ad3eb182a7"
recs = [ledger.new_record(
    run_id,                                  # str
    "security-artifact-gate",                # task = 공정 ID (비식별, 영숫자·_·-·. 64자)
    "B",                                     # class ∈ A / A-verify / B / C-realtime / C-platform / D / N
    "gpt-5.6-sol", "ultra",                  # lane·effort 는 routing 정본의 허용 쌍
    falsifiable=True, explore=False, status="done",
    sec=2100, retries=0, quota_delta={"codex": 1}, guard_violations=[])]
n, note = ledger.append_records(recs)        # 시크릿 스캔 → CAS 커밋
```

`note` 를 반드시 읽는다. `commit 완료(CAS)` 가 아니면 **커밋되지 않았거나 부분 성공**이다 —
`partial` 은 입력을 소비하지 않고 `.vibe-pending/journal.jsonl` 에 복구 정보를 남긴다.

- 워커 1개 = 1줄. 집계 키는 **(class, lane, effort)** — task로 집계하면 arm당 관측이 1이라 영원히 수렴하지 않는다
- **산출물 본문을 넣지 않는다.** 메트릭만
- `quota_delta`는 보조 신호다. 부정확하므로 스왑 판정의 주 근거로 쓰지 않는다
- **데몬·상시 폴링을 만들지 않는다** — 허브가 정확히 그 SPOF로 죽었다

### 9. 보고

§6 규격 HTML 1개. **실패·건너뛴 항목을 성공한 것보다 먼저.** 워커별 소모 · 만들어진 워크트리와 되돌리는 법 · 다음 1개.

---

## 집계 · 스왑 제안

```bash
python "<skill>/scripts/aggregate_ledger.py"        # 사람용 표
python "<skill>/scripts/aggregate_ledger.py" --json # 기계용
```

(class, lane, effort)별 채택률 · 중위 소요 · 실패율 · 재실행률. `explore:true` 관측은 **별도 컬럼**.

**스왑 제안 조건**: 같은 클래스에서 2순위 채택률이 1순위보다 **15%p 이상** 높고 **양쪽 관측이 각 5회 이상**.

- 제안은 **출력만** 한다. **표를 자동 수정하지 않는다**
- 승인은 Simon이 폼에서 누른다. **모델이 라우팅 표를 스스로 고치는 경로를 만들지 않는다**
- 관측이 부족하면 `관측 부족(n=N, 필요 5)`을 **명시 출력**한다. 침묵하지 않는다

## 가드레일

- **자동 머지 금지.** PR까지만
- **비용·파괴·시크릿**은 워커에게 위임하지 않는다
- 워커가 워커를 띄우려 하면 `nested_worker_depth_exceeded` — 우회하지 않는다
- 워커 산출물을 검증 없이 신뢰하지 않는다. **리뷰는 생략 가능한 단계가 아니다**
- 과제가 워커를 띄울 만큼 크지 않으면 `dev-orchestrator`로 넘기거나 인라인 처리한다
- **§7 가드를 학습 파라미터로 만들지 않는다** — 불변이다

## 주기 적대평가 — 영역별 최적 레인을 데이터로 정한다

라운드는 1순위만 태워 2순위 이하 관측이 안 쌓인다. 정답이 기계로 나오는 문항을 두 레인이 풀고 **벤더가 다른 제3 레인이 채점**한다(G10).
순서: `adversarial_eval.py --validate` → `--plan` → `--run --dry` → `--preflight`(G12 실호출) → `--run` → `--report`. 표는 자동으로 안 고친다 — 제안만.
규율 표 · 실행 경로(Orca 워커가 아니라 벤더 CLI 직행) · 문항 추가 규칙 → **`references/adversarial-eval.md`**

## 알려진 함정

Orca effort 상한 · 실패 task 재디스패치(`--retry-of`) · Windows `.cmd` 셔임 · codex 기본 effort · `check` 응답 모양 · Git Bash 경로 오염 등 20여 건 → **`references/pitfalls.md`**. 워커에 과제가 안 들어가는 증상과 G8 강제종료는 위 6-2 절에 있다.

## 관련 스킬

`dev-orchestrator`(단일 세션) · `simon-worktree`(격리 규칙) · `ai-debate`(결정 지점) · `simon-design-first`(디자인 방향) · `orca-cli`(오르카 명령 정본 — 버전 불일치 시 `orca skills get <이름>`이 우선)
