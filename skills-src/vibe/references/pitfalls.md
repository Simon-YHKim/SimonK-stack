# 알려진 함정

> 2026-09-29 현재 이 문서는 **사고 기록**이지 실행 절차가 아니다. 아래 날짜별
> 관측은 당시 환경에만 적용된다. `run_dispatch`, `run_codex_exec`,
> `validate_and_dispatch`, `--probe-efforts`, 레거시 적대평가 실호출은 차단됐다.
> raw `worker-start`/`worker-stop`/`task-update`/`terminal send`와
> `kill_worker.py`를 복구 지름길로 실행하지 않는다. 현재 실행·비용·재시도·종료
> 계약은 [SKILL.md](../SKILL.md)의 현재 실행 절차를 따른다.


- **채택률 "미회수"는 세 가지 다른 상태였다 (2026-09-13)**: `unmerged_runs()` 가 `items==0` 인 run 을 전부 한 덩어리로 경고했는데, 그 안에는 처방이 다른 셋이 섞여 있다 — **시트를 안 만들었다**(진짜 학습 정지) · **시트는 있고 회수만 안 됐다**([결과 저장] 한 번) · **워커가 산출물을 0건 냈다**(라운드 실패, 채택할 게 없다). 한 신호로 보고하면 고쳐야 할 쪽을 고를 수 없다. `ledger.run_recovery_state()` 가 이제 가른다. ⚠ 실측 결과 4건 **전부** '시트를 안 만들었다' 였다 — **손으로 조립한 시트는 `decisions_run_*.json` 을 내지 않아 회수 경로가 통째로 없다.** 시트는 반드시 `make_decision_sheet.py` 로 만든다
- **"만들었다"와 "돈다"는 다르다 (2026-09-13)**: `adversarial_eval.py` 는 `--run` 이 안내문만 찍는 껍데기였고 `truth_post` 는 구현이 없었는데도 "적대평가를 만들었다"고 보고됐다. **검사가 없으면 껍데기와 완성품이 같은 얼굴을 한다.** `selftest.py` 에 29개를 넣었고, 변이 검증으로 실제로 무는지 확인했다(RC_IS_ANSWER 비우기·접미사 무시·벤더 라벨 변조 → 셋 다 결과가 뒤집힌다)
- **`agent_prompt_blocked` 는 프롬프트 탓이 아닐 수 있다 (2026-09-12)**: 당시 Codex CLI 업데이트 안내가 워커 기동을 막았다. 새 최소 프롬프트를 실호출해 진단하지 말고 기존 오류·툴체인 버전·격리된 비생성 메타데이터부터 확인한다. 재실행은 중앙 계획·계정/비용 증명과 지원되는 어댑터가 준비된 뒤에만 한다
- **실패한 task 는 재디스패치가 안 된다**: 당시 `failed` Task는 `task_not_startable`로 거부됐다. 현재는 원래 Dispatch의 수락·종료·실제 비용을 대조하고 중앙 Store에서 새 계획을 검증하기 전까지 재시도하지 않는다. 새 Task 생성이나 raw `worker-start --retry-of`로 우회하지 않는다
- **Windows 에서 `codex`·`npm` 은 `.cmd` 셔임이다**: `subprocess.run([...], shell=False)` 로는 CreateProcess 가 못 띄워 "설치 안 됨"처럼 보인다. `shutil.which()` 로 풀고 확장자가 `.cmd`/`.bat` 이면 `["cmd","/c",경로]` 로 감싼다 — 셸 문자열은 만들지 않는다
- **codex 기본 effort 가 낮다**: `sol`·`daybreak` 은 `low`, `astra`·`terra`·`luna` 는 `medium`. 명시하지 않으면 조용히 그 값으로 돈다. `dispatch_argv()`가 막는다. ⚠ **`~/.codex/config.toml` 의 `model_reasoning_effort` 도 같은 함정이다** — 여기가 `low` 면 effort 를 안 준 codex 호출 전부가 프론티어 모델을 `low` 로 굴린다
- **agy effort는 슬러그에 있다**: `--effort`를 따로 붙이지 않는다. `gemini-3.8-flash-high`가 슬러그 전체다
- **grok 200K 초과 = 과금 2배**: 큰 입력을 grok에 주지 않는다
- **`grok usage`는 TUI를 띄운다**: 비대화형 쿼터 조회 수단이 없다 → orca로만 읽는다
- **cp949 크래시**: Windows 콘솔 기본 인코딩이 em-dash에서 죽는다. 스크립트가 stdout을 UTF-8로 고정한다
- **codex 보안 감사는 Trusted Access 없이는 조용히 막힌다**: 하위 감사를 다 끝내고도 출력만 차단된다. 하트비트도 안 올라가 "행에 걸렸다"로 오진하기 쉽다 → `orca terminal read` 로 확인한다
- **옛 `orca orchestration check` 응답은 `result.messages[]`였다**: 당시 `result.deliveries`로 잘못 읽거나 배달 확인을 누락해 같은 메시지를 재수신했다. 현재 raw ack를 실행 절차로 쓰지 않고, 등록된 작업은 guarded adapter/Store의 원래 Dispatch 상태와 수락 증거를 대조한다
- **Git Bash 가 `/` 로 시작하는 인자를 경로로 바꾼다**: `--objective "/vibe ..."` 가 `C:/Program Files/Git/vibe ...` 로 오염됐다. 슬래시로 시작하는 문자열은 PowerShell 로 넘긴다
- **`codex exec` 와 대화형 CLI의 effort 문법은 다르다 (2026-09-06 관측)**: 당시 `codex exec`는 `--effort`를 거부했다. `routing.run_codex_exec()`는 현재 dry argv 생성 외 실호출이 차단되므로 이 옛 argv를 실행 절차로 사용하지 않는다. 직접 CLI는 별도 guarded adapter와 정확한 구독·계정 증명이 생길 때까지 보류한다
- **Orca 의 effort 상한은 앱에 하드코딩된 다섯 줄이 정한다 (2026-09-06 원인 규명)**: `src/shared/agent-session-option-catalog-claude-codex.ts` 의 `CODEX_SESSION_OPTION_CATALOG` 가 sol·terra(`ultra`) · luna(`max`) · 5.5·5.2-codex(`xhigh`) **다섯만** 담고, 나머지는 전부 `unknownModelOptions: [codexEffort('xhigh')]` 로 떨어진다. astra·daybreak 은 그 목록에 없어서 **존재하지 않는 모델과 똑같은 상한(xhigh)** 을 받는다. 소스 주석이 의도임을 밝히고 있고(계정마다 쓸 수 있는 모델이 다르니 완전한 목록을 주장하지 않는다), **저장소 HEAD 도 같은 다섯 줄이라 Orca 를 올려도 안 풀린다.** 원본을 읽기 전에 "모델이 지원 안 한다"·"계정 문제다"로 결론내지 말 것
- **Orca 의 effort 허용목록 ≠ CLI 의 정본**: `models_cache.json` 이 `max`·`ultra` 를 지원한다고 적어도 Orca 가 거부할 수 있다. **daybreak 과 astra 는 `xhigh` 가 상한**이고(`ultra`·`max` 는 `invalid_argument`), 같은 codex 벤더인 sol·terra 는 `ultra` 가 통과하며 luna 는 `max` 까지다 — **허용목록이 모델별이다.** 표에 적을 값은 CLI 가 주장하는 값이 아니라 **Orca 가 실제로 받는 값**이다
- **옛 effort 탐침은 무료 증명이 아니다 (2026-09-06 관측)**: 당시에는 존재하지 않는 worktree 셀렉터로 `worker-start`의 검증 순서를 이용했다. 현재 `routing.py --probe-efforts`는 차단되며, 실행 전 단계가 네트워크·계정·시작 부작용을 만들지 않는다는 보증도 아니다. 새 모델은 중앙 registry와 fresh runtime의 교집합 및 별도 안전 검증으로 판단한다
- **Orca 는 `--model` 문자열을 검증하지 않는다**: `gpt-9-nonexistent` 도 `--effort high` 면 통과한다(모르는 모델에는 기본 목록 low·medium·high·xhigh 가 적용된다). 즉 **슬러그 오타는 Orca 에서 안 잡히고 워커가 뜬 뒤 codex 가 죽는다.** `routing.LANES` 의 키가 사실상 유일한 오타 방어선이다 — 임의 슬러그를 코드에 직접 넣지 말 것. 은퇴 모델도 같다(`gpt-5.4-mini` 는 2026-08-31 은퇴 → 배정 금지 목록)
- **grok·gemini 는 effort 지정 자체가 불가능하다**: `--effort` 는 `--model` 을 요구하는데(`orca help`) 두 agent 는 `--model` 을 거부한다(`does not support launch-time model selection`). 표의 `top`/`std` 는 **그 CLI 안에서의 의도**일 뿐 Orca 경로에서는 전달되지 않는다. "grok 을 xhigh 로 띄웠다"고 적지 말 것
- **모델 목록은 스키마가 아니라 CLI 에 묻는다**: `orca agent-context` 는 모델 id 를 *"opaque provider model ids"* 라고만 적고 **열거하지 않는다.** 거기 없다고 없는 게 아니다 — Daybreak Blue 를 이 오독으로 놓쳤고, `gpt-6-astra` 도 같은 이유로 늦게 알았다. 정본은 `~/.codex/models_cache.json` · `agy models` · `grok models` · `claude --help`. codex 쪽은 `visibility`(`list`/`hide`)와 `priority` 도 같이 본다 — `hide` 는 사람에게 안 보이는 좌석이라 배정 금지고, `priority` 가 그 벤더의 서열이다(astra=1)
- **Orca agent id ≠ CLI 이름**: `--agent agy` 는 `agent_unconfigured` 로 거부된다. Orca 등록명은 **`antigravity`** 다(CLI 바이너리만 `agy`). 이걸로 "등록이 안 됐다"고 30분 오진했다
- **생성 플래그는 새 워크트리에만**: `--name`·`--setup`·`--repo` 를 `current` 에 붙이면 `invalid_argument`. 그런데 외부 셸에서는 `current` 만 통과하므로, 무조건 붙이면 **실사용 경로가 통째로 막힌다**
- **`--model` 은 Claude·Codex·Cursor 만**: grok·gemini 는 `--agent` 만 주고 모델은 그 CLI 기본값이 쓰인다
- **`worker-start` 셀렉터는 Orca 터미널 밖에서 안 잡힌다**: `name:` · `path:` · `new-top-level`(+`--repo`) 전부 `selector_not_found`. Claude Code 셸에서는 `--worktree current` 만 통과했다
- **worker-stop 성공과 프로세스 종료는 다르다**: 당시 정지 표시만으로 종료를 확증하지 못했다. PID 부재만으로도 모든 자식 종료나 비용 정산을 증명할 수 없다. raw stop과 `kill_worker.py`는 현재 비활성이고, 검증된 supervised stop 어댑터가 없으면 원래 Dispatch를 조회하며 상태를 미확정으로 둔다
- **stale 워크트리 WIP**: `worktree create`가 "branch exists"로 실패해도 그 디렉터리에 타 에이전트 미커밋 변경이 있을 수 있다
- **`.env` 부재**: gitignore 대상이라 새 워크트리에 안 따라온다
- **`turnStart: observed` 여도 입력이 멈출 수 있다 — 3/3 재현 (2026-09-14)**: 당시 입력창에 과제가 남아 `Working`으로 전환되지 않았고 수동 Enter로 풀린 사례가 있었다. 현재 raw `terminal send`, `kill_worker`, `task-update`, `worker-start --retry-of` 복구법은 비활성이다. 수락 불명은 원래 Dispatch/Task 조회만 하며 새 입력·새 UUID·재발주를 하지 않는다
- **보고서 파일은 워커 종료 증거가 아니다 (2026-09-14)**: 당시 `worker_done` 전 파일만 보고 종료해 원장에 실패가 남았다. 현재는 native Task/Dispatch의 terminal 상태, 결과 수락, 실제 비용 정산을 별도로 확인한다. 종료 자동화는 아직 구현되지 않았으므로 raw stop으로 대체하지 않는다
- **heartbeat-only 배달이 완료 관측을 지연시킨 사례 (2026-09-14)**: 당시 배달 확인 누락으로 뒤의 `worker_done` 두 건을 17분 늦게 봤다. 이 관측은 raw ack 재가동 허가가 아니며, 현재 완료 판정은 원래 작업의 native terminal 상태와 결과·비용·수락 증거를 요구한다
- **쿼터 % 는 낡는다 — `updatedAt` 을 같이 본다 (2026-09-14)**: `orca account list` 의 codex `weekly.usedPercent` 가 77% 에서 80분 넘게 갱신되지 않았고, 그 값을 믿고 게이트를 더 돌리다 **87%(G5 금지선 초과)를 뒤늦게 발견**했다. 오래된 값은 '읽기 실패 = 미확인'으로 취급한다. **보안 게이트 두 고정 레인이 모두 codex 라 codex 가 85% 를 넘으면 코딩 라운드 전체가 멈춘다**(G1 때문에 코딩 레인이 대신할 수 없다) — 게이트 한 회당 쿼터 소모를 원장에 남겨 미리 셈할 것
- **같은 계열 high 가 재게이트마다 한 층 안쪽에서 나오면 수정 반복을 멈춘다 (2026-09-14)**: PR #1814(동의 · 자동 저장)는 1차 → 2차 → 3차 게이트가 매번 '철회했는데 저장된다' 계열 high 를 한 층씩 안쪽(화면 복귀 → 재확인 응답 → capture 착수 후)에서 찾았다. 발주 전에 '같은 계열이 또 나오면 멈추고 사람에게 범위를 묻는다'를 뒤집는 조건으로 적어 두었고, 그 조건이 걸려 3차 수정을 보내지 않았다. 경쟁 조건 수정은 층 하나가 아니라 **작업 수명 전체(확인 → 쓰기 끝)** 를 한 설계로 봐야 수렴한다
- **레거시 `validate_plan`은 실행 준비 증명이 아니다 (2026-09-14)**: 당시에는 계획의 두 보안 게이트 존재만 확인했고 쿼터·과금·실행 수락은 보증하지 않았다. 현재 중앙 계획은 fresh runtime·계정·비용·의존성까지 확인해야 하며, 게이트가 막히면 작업을 미완료로 유지한다. 검증기를 축소하거나 옛 dry 결과로 워커를 띄우지 않는다
- **워커는 발주서에 적어도 자기 결론을 서브에이전트로 재검증한다 — 숫자로 금지한다 (2026-09-14)**: 한 워커가 result.md 를 쓴 뒤 하위 5개 반박 검증 워크플로를 띄웠다(G2 위반 · 앞선 7 과 합쳐 12 로 G3 초과). 그 뒤 발주서에 **"서브에이전트 최대 N, 자기 결론 재검증 용도 0"** 을 숫자로 적자 이후 워커 넷은 지켰다. 반증은 result.md 의 '반증 시도' 절에 직접 쓰게 한다
- **`Waiting for workflow`는 처리 완료가 아니다 (2026-09-14)**: 당시 하위 에이전트가 멈춰 메시지 수신이 지연됐다. 현재는 원래 작업의 상태와 읽기 영수증을 조회하고 불명 상태를 유지한다. raw `terminal send`로 깨우거나 토큰 수 정지만으로 종료·재시도를 판정하지 않는다
- **감시 루프 하나가 run 전체의 메시지를 삼킨다 — run 당 감시는 하나로 (2026-09-14)**: 워커 A 를 보는 감시가 'heartbeat 아닌 메시지면 멈춤' 규칙으로 워커 B 의 worker_done 에서 멈췄고, B 를 보던 감시도 같은 배달에서 함께 멈췄다. `check` 는 run 단위라 워커별로 감시를 나누면 안 된다 — 한 감시가 모든 task 상태를 함께 보고, 멈춘 뒤 다시 띄운다
- **CI 감시에서 진행 중 검사는 `conclusion` 이 빈 문자열이다 (2026-09-14)**: `select(.conclusion != null and .conclusion != "SUCCESS")` 는 진행 중 검사를 실패로 세어 감시가 곧바로 끝났다. 실패는 `status == "COMPLETED"` 인 것만 센다
- **bash 큰따옴표 안의 백틱은 `send --body` 에서도 실행된다 (2026-09-14)**: 워커에게 보낸 본문의 `` `am force-stop …` `` 이 코디네이터 셸에서 실행돼 명령이 빠진 채 전달됐다(`am: command not found`). 본문은 작은따옴표로 감싸거나 파일로 넘긴다
- **Claude Code가 신뢰하지 않는 폴더에서 과제가 소실된 사례 (2026-09-16, D-28 M1)**: 당시 신뢰 대화상자가 Orca 입력을 가로채 `turn_start_unobserved`가 됐다. 자동 복구를 위해 신뢰 플래그를 스크립트로 켜거나 raw `kill_worker.py`/`task-update`/`worker-start`를 호출하지 않는다. 현재 실행은 사전에 사용자 신뢰가 확인된 격리 작업공간과 guarded adapter가 있을 때만 시작하고, 수락 불명은 조회 전용으로 둔다
- **옛 `check --wait`의 heartbeat 재전달 (2026-09-19, M2)**: 미확인 배달을 다시 기다려 같은 heartbeat를 반복 수신했다. 현재는 guarded adapter가 원래 Dispatch/Task 상태를 조회하고, 구조적 완료 표시와 실제 결과·비용·수락을 따로 검증한다. raw `check --ack`를 자동 복구로 쓰지 않는다
- *(2026-09-16 주석)* 위 두 항목의 "85% 금지선"은 당시 규칙이다. Q-260913-05 로 강등은 80% 초과, 사용 금지는 **한도 100% 도달·실호출 실패**로 바뀌었다 — 그래서 "codex 가 85% 를 넘으면 코딩 라운드 전체가 멈춘다"는 이제 100% 도달에서 일어난다. 게이트 한 회당 소모를 원장에 남기는 권고는 그대로다
