# 알려진 함정

> SKILL.md 에서 옮겼다(2026-09-13) — SimonK-stack CI 의 본문 500줄 상한(E007) 때문이다. 내용은 그대로다.


- **채택률 "미회수"는 세 가지 다른 상태였다 (2026-09-13)**: `unmerged_runs()` 가 `items==0` 인 run 을 전부 한 덩어리로 경고했는데, 그 안에는 처방이 다른 셋이 섞여 있다 — **시트를 안 만들었다**(진짜 학습 정지) · **시트는 있고 회수만 안 됐다**([결과 저장] 한 번) · **워커가 산출물을 0건 냈다**(라운드 실패, 채택할 게 없다). 한 신호로 보고하면 고쳐야 할 쪽을 고를 수 없다. `ledger.run_recovery_state()` 가 이제 가른다. ⚠ 실측 결과 4건 **전부** '시트를 안 만들었다' 였다 — **손으로 조립한 시트는 `decisions_run_*.json` 을 내지 않아 회수 경로가 통째로 없다.** 시트는 반드시 `make_decision_sheet.py` 로 만든다
- **"만들었다"와 "돈다"는 다르다 (2026-09-13)**: `adversarial_eval.py` 는 `--run` 이 안내문만 찍는 껍데기였고 `truth_post` 는 구현이 없었는데도 "적대평가를 만들었다"고 보고됐다. **검사가 없으면 껍데기와 완성품이 같은 얼굴을 한다.** `selftest.py` 에 29개를 넣었고, 변이 검증으로 실제로 무는지 확인했다(RC_IS_ANSWER 비우기·접미사 무시·벤더 라벨 변조 → 셋 다 결과가 뒤집힌다)
- **`agent_prompt_blocked` 는 프롬프트 탓이 아닐 수 있다 (2026-09-12)**: codex CLI 가 업데이트 안내를 띄우면 워커 기동이 통째로 막히는데 에러가 이렇게 나온다. 최소 프롬프트("Print the cwd and stop")를 같은 레인에 던져 갈라라 — 그래도 막히면 `Agent startup blocked: codex-update-prompt` 로 문구가 바뀌며 정체가 드러난다. 프리플라이트 0-A 가 이걸 먼저 잡는다
- **실패한 task 는 재디스패치가 안 된다**: 한 번 `failed` 가 되면 `task_not_startable` 로 거부된다(`only a ready Task can start`). 프롬프트를 고쳐도 같은 task 로는 못 띄운다 — **새 task 를 만들거나 `worker-start --retry-of`** 를 쓴다. 이걸 몰라서 "스펙을 고쳤는데 또 막힌다"고 두 번 오진했다
- **Windows 에서 `codex`·`npm` 은 `.cmd` 셔임이다**: `subprocess.run([...], shell=False)` 로는 CreateProcess 가 못 띄워 "설치 안 됨"처럼 보인다. `shutil.which()` 로 풀고 확장자가 `.cmd`/`.bat` 이면 `["cmd","/c",경로]` 로 감싼다 — 셸 문자열은 만들지 않는다
- **codex 기본 effort 가 낮다**: `sol`·`daybreak` 은 `low`, `astra`·`terra`·`luna` 는 `medium`. 명시하지 않으면 조용히 그 값으로 돈다. `dispatch_argv()`가 막는다. ⚠ **`~/.codex/config.toml` 의 `model_reasoning_effort` 도 같은 함정이다** — 여기가 `low` 면 effort 를 안 준 codex 호출 전부가 프론티어 모델을 `low` 로 굴린다
- **agy effort는 슬러그에 있다**: `--effort`를 따로 붙이지 않는다. `gemini-3.8-flash-high`가 슬러그 전체다
- **grok 200K 초과 = 과금 2배**: 큰 입력을 grok에 주지 않는다
- **`grok usage`는 TUI를 띄운다**: 비대화형 쿼터 조회 수단이 없다 → orca로만 읽는다
- **cp949 크래시**: Windows 콘솔 기본 인코딩이 em-dash에서 죽는다. 스크립트가 stdout을 UTF-8로 고정한다
- **codex 보안 감사는 Trusted Access 없이는 조용히 막힌다**: 하위 감사를 다 끝내고도 출력만 차단된다. 하트비트도 안 올라가 "행에 걸렸다"로 오진하기 쉽다 → `orca terminal read` 로 확인한다
- **`orca orchestration check` 응답은 `result.messages[]`**: `result.deliveries` 가 아니다. ack 는 `result.deliveryId` 로 한다. ack 하지 않으면 **같은 메시지가 계속 재전송**되어 "진행이 멈췄다"로 보인다
- **Git Bash 가 `/` 로 시작하는 인자를 경로로 바꾼다**: `--objective "/vibe ..."` 가 `C:/Program Files/Git/vibe ...` 로 오염됐다. 슬래시로 시작하는 문자열은 PowerShell 로 넘긴다
- **`codex exec` 는 `--effort` 를 거부한다**: `-c model_reasoning_effort="ultra"` 를 쓴다. 대화형 `codex` 와 문법이 다르다. 프롬프트를 인자로만 주면 stdin 을 기다리며 행에 걸린다. 2026-09-06 실호출로 확인된 형태는 `codex exec -m <model> -c model_reasoning_effort="<값>" -` + stdin 이고, `routing.run_codex_exec()` 가 이 형태를 만든다
- **Orca 의 effort 상한은 앱에 하드코딩된 다섯 줄이 정한다 (2026-09-06 원인 규명)**: `src/shared/agent-session-option-catalog-claude-codex.ts` 의 `CODEX_SESSION_OPTION_CATALOG` 가 sol·terra(`ultra`) · luna(`max`) · 5.5·5.2-codex(`xhigh`) **다섯만** 담고, 나머지는 전부 `unknownModelOptions: [codexEffort('xhigh')]` 로 떨어진다. astra·daybreak 은 그 목록에 없어서 **존재하지 않는 모델과 똑같은 상한(xhigh)** 을 받는다. 소스 주석이 의도임을 밝히고 있고(계정마다 쓸 수 있는 모델이 다르니 완전한 목록을 주장하지 않는다), **저장소 HEAD 도 같은 다섯 줄이라 Orca 를 올려도 안 풀린다.** 원본을 읽기 전에 "모델이 지원 안 한다"·"계정 문제다"로 결론내지 말 것
- **Orca 의 effort 허용목록 ≠ CLI 의 정본**: `models_cache.json` 이 `max`·`ultra` 를 지원한다고 적어도 Orca 가 거부할 수 있다. **daybreak 과 astra 는 `xhigh` 가 상한**이고(`ultra`·`max` 는 `invalid_argument`), 같은 codex 벤더인 sol·terra 는 `ultra` 가 통과하며 luna 는 `max` 까지다 — **허용목록이 모델별이다.** 표에 적을 값은 CLI 가 주장하는 값이 아니라 **Orca 가 실제로 받는 값**이다
- **그 측정은 이제 공짜다 (2026-09-06)**: worker-start 의 검증 순서가 `consumer fence → task 존재 → effort → worktree 셀렉터 → 기동` 이다. 그래서 **존재하지 않는 worktree 이름**을 같이 주면, effort 가 거부되면 `does not support effort`, 통과하면 `selector_not_found` 로 갈리고 **어느 쪽이든 워커가 안 뜬다.** `python scripts/routing.py --probe-efforts --task <실재 task_id>` 가 이걸 전 레인에 돌린다. 새 모델이 보이면 표를 고치기 전에 이걸 먼저 돌릴 것
- **Orca 는 `--model` 문자열을 검증하지 않는다**: `gpt-9-nonexistent` 도 `--effort high` 면 통과한다(모르는 모델에는 기본 목록 low·medium·high·xhigh 가 적용된다). 즉 **슬러그 오타는 Orca 에서 안 잡히고 워커가 뜬 뒤 codex 가 죽는다.** `routing.LANES` 의 키가 사실상 유일한 오타 방어선이다 — 임의 슬러그를 코드에 직접 넣지 말 것. 은퇴 모델도 같다(`gpt-5.4-mini` 는 2026-08-31 은퇴 → 배정 금지 목록)
- **grok·gemini 는 effort 지정 자체가 불가능하다**: `--effort` 는 `--model` 을 요구하는데(`orca help`) 두 agent 는 `--model` 을 거부한다(`does not support launch-time model selection`). 표의 `top`/`std` 는 **그 CLI 안에서의 의도**일 뿐 Orca 경로에서는 전달되지 않는다. "grok 을 xhigh 로 띄웠다"고 적지 말 것
- **모델 목록은 스키마가 아니라 CLI 에 묻는다**: `orca agent-context` 는 모델 id 를 *"opaque provider model ids"* 라고만 적고 **열거하지 않는다.** 거기 없다고 없는 게 아니다 — Daybreak Blue 를 이 오독으로 놓쳤고, `gpt-6-astra` 도 같은 이유로 늦게 알았다. 정본은 `~/.codex/models_cache.json` · `agy models` · `grok models` · `claude --help`. codex 쪽은 `visibility`(`list`/`hide`)와 `priority` 도 같이 본다 — `hide` 는 사람에게 안 보이는 좌석이라 배정 금지고, `priority` 가 그 벤더의 서열이다(astra=1)
- **Orca agent id ≠ CLI 이름**: `--agent agy` 는 `agent_unconfigured` 로 거부된다. Orca 등록명은 **`antigravity`** 다(CLI 바이너리만 `agy`). 이걸로 "등록이 안 됐다"고 30분 오진했다
- **생성 플래그는 새 워크트리에만**: `--name`·`--setup`·`--repo` 를 `current` 에 붙이면 `invalid_argument`. 그런데 외부 셸에서는 `current` 만 통과하므로, 무조건 붙이면 **실사용 경로가 통째로 막힌다**
- **`--model` 은 Claude·Codex·Cursor 만**: grok·gemini 는 `--agent` 만 주고 모델은 그 CLI 기본값이 쓰인다
- **`worker-start` 셀렉터는 Orca 터미널 밖에서 안 잡힌다**: `name:` · `path:` · `new-top-level`(+`--repo`) 전부 `selector_not_found`. Claude Code 셸에서는 `--worktree current` 만 통과했다
- **worker-stop이 프로세스를 안 죽인다**: 정지 확증은 PID 실존으로만. 쿼터·cwd는 오신호
- **stale 워크트리 WIP**: `worktree create`가 "branch exists"로 실패해도 그 디렉터리에 타 에이전트 미커밋 변경이 있을 수 있다
- **`.env` 부재**: gitignore 대상이라 새 워크트리에 안 따라온다
