# SimonK-stack 세션 인수인계

## Latest — 2026-10-01 / Claude·Codex CLI 계약 수정과 PR #78 인계

갱신 시각: 2026-10-01 15:41:53 KST. Simon이 컨텍스트 부담을 이유로 `/simon-handoff`를 요청했다. 문서 작성 중 별도 작업 흐름에서 코드 PR #78이 머지되어 아래 상태를 다시 반영했다.

### 어디까지 왔나
- `origin/main`: `669da9fe33c585cd685526637309b83d06b71612` (PR #78 머지). 이번 흐름에서 #76·#77·#78이 main에 머지됐다.
- [PR #78 — 직접 CLI의 허위 `ready` 차단](https://github.com/Simon-YHKim/SimonK-stack/pull/78)은 **머지됨**. 최종 HEAD `b8a26a76fa88ad5cccdde670f077f91c16ca4539`, merge SHA `669da9fe33c585cd685526637309b83d06b71612`, 6파일(플래너·테스트·계약 문서·Claude CLI 가짜 전송 테스트의 원격 CI 추가). PR 검사 4/4 성공. 다음 세션에서 최신 main 상태를 재조회한다.
- 로컬 전체 `/vibe` unittest 361/361, selftest 180/180, skill quality gate 141/141, `git diff --check` 통과. Git Bash의 TDD guard는 통과했으나 WSL 실행은 Windows worktree `.git` 경로를 해석하지 못해 실패했다. 모델·Bot 실호출은 없었다.
- 이 인수인계는 별도 `handoff/20261001-1539` 브랜치에서 문서만 작성한다. 기존 `fix/vibe-cli-node-contract-261001` 작업 트리는 깨끗했다. 공유 기본 체크아웃의 로컬 `main`은 원격과 크게 분기되고 다른 미커밋 파일 4개가 있어 이동·정리하지 않았다.

### 판단·안전 경계
- 독립 `ai-debate` 심판의 #78 판정은 **조건부 소스 전용 GO**였다. 별도 흐름에서 D-47과 소수의견을 허브에 로컬 기록하고 PR 본문에 연결한 뒤 머지했다. D-47 기록상 main의 quality·Windows path audit·validate·Cloudflare Pages·tag-release 5/5 성공, 태그/릴리스 차단 유지, 사용자 flat 설치 불변이다. 완전 CLI 5노드 양성 통합 계획·Store/전송 경로는 여전히 미검증이다.
- 허브 `E:/Coding Infra/AI Infra/Communication/`는 dirty/diverged 상태다. D44–D47은 로컬 기록이며 원격 반영으로 간주하지 않는다. 허브 전체를 무차별 stage/push하지 않는다.
- `distribution/main-source-only.hold`, SessionStart/Release 차단 및 marketplace `313c04b` pin은 현재 유지됐다. **소스 머지는 설치·릴리스·실호출 허가가 아니다.** 사용자 flat `/vibe` 설치는 마지막 확인 시 2.12.24이고, 최신 소스 변경을 설치하지 않았다.
- 사용자 정책: 추가 과금 **$0**, 구독 포함 usage만 사용, 자동충전·초과 과금·결제 설정 변경 금지. Grok CLI/Bot과 모든 모델의 실호출은 정확한 계정·구독 버킷·차단 상태를 검증하기 전에는 하지 않는다. Bot은 GUI-only, CLI/API/MCP로 가능한 작업은 `/vibe`가 직접 맡는다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | 완전 Claude/Codex 직접 CLI 5노드 debate의 양성 통합 계획·Store/전송 경로를 오프라인 테스트로 검증한다 | 중간 | D-47 소수의견의 첫 후속 |
| B | AGY·Grok CLI에 구독 전용 `claim → send once → lookup → verify` 어댑터를 오프라인 구현·검증한다 | 큼 | 별도 브랜치 |
| C | Claude/Codex 사용자 설치 후보의 자산 보존·호스트 명령·구독 청구를 별도 검증한 뒤 설치 게이트를 다시 판단한다 | 큼 | 소스 머지와 분리 |
| D | 허브 D44–D47 기록의 소유권과 dirty/diverged 이력을 안전하게 조정한다 | 중간 | 허브 전체 push 금지 |

### 핵심 파일과 검증
```text
skills-src/vibe/scripts/orchestrate.py               직접 CLI 후보의 구조 사전검사
skills-src/vibe/scripts/execute_cli.py                Claude CLI 전송 전 검사
skills-src/vibe/scripts/execute_codex_cli.py          Codex CLI 전송 전 검사
skills-src/vibe/scripts/test_orchestrate.py           플래너 회귀 테스트
.github/workflows/skills-ci.yml                       Claude CLI 가짜 전송 CI 추가
skills-src/vibe/references/orchestration.md            운영 계약
distribution/main-source-only.hold                    설치·릴리스 경계
E:/Coding Infra/AI Infra/Communication/DECISIONS.md  D-code (별도 저장소)
```
```powershell
python -B -m unittest discover -s skills-src/vibe/scripts -p test_*.py -q
python -B skills-src/vibe/scripts/selftest.py
python -B .github/skill-ci/run_ci.py
gh pr checks 78 --watch=false
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
gh pr view 78 --json number,state,headRefOid,baseRefOid,statusCheckRollup,body
```

---

## 2026-10-01 / `/vibe` 구독 전용 실행 경로와 핸드오프

### 어디까지 왔나
- 작업 시작 기준 `origin/main`: `357a42136b691951a3869169c86d5d5726b75f88` (PR #75 Orca 동시성 수정 머지). 최종 main SHA는 `git rev-parse origin/main`으로 다시 확인한다.
- 이번 세션 PR: [#76 — unsupported provider route 차단](https://github.com/Simon-YHKim/SimonK-stack/pull/76). 코드 커밋 `1733560d853ceeaf0ca2872ff152b661e7613a30`; 문서 추가 전 4/4 원격 검사가 통과했다. 이 문서 커밋 후 CI와 머지 상태를 다시 확인한다.
- `/vibe` 소스 2.12.38에서 AGY·Grok의 `cli`/`orca` 실행 어댑터가 없으면 합성된 런타임·과금 증거로도 `ready`가 되지 않는다. Antigravity는 구매 크레딧 폴백 차단과 정확한 계정·전송 경로별 쿼터 증거도 요구한다.
- 검증: `/vibe` 오프라인 unittest 351/351, `selftest.py` 180/180, skill validator 오류·경고 0, eval 26건 dry-run 입력 확인, `git diff --check` 통과. 실제 구독 청구·모델 품질·실제 Bot 전달의 증명은 아니다.
- 기존 Claude·Codex·`.agents` 사용자 flat `/vibe`는 마지막 관측에서 2.12.24였다. 이 변경은 소스 전용이며 사용자 설치를 수행하지 않았다.

### 활성 인프라·안전 경계
- `distribution/main-source-only.hold`, SessionStart의 source-only 보호, marketplace `313c04b` pin 및 GitHub Release hold를 유지한다. `main` Pages 자동 배포만 Simon이 이번 작업에 허용했다.
- 추가 API 과금 $0, 구독 포함 usage만 사용한다. 자동충전·초과 과금·결제 설정을 변경하지 않는다. 사용자 보고상 xAI 사용량이 소진되어 Grok CLI·Grok Bot 실호출을 하지 않았다.
- Grok Bot은 `/vibe` 내부 GUI-only Relay 어댑터이고 직접 `/vibe-bot` 호출과 호환된다. CLI/API/MCP로 가능한 작업을 Bot으로 보내지 않는다. 실제 활성 roster·Relay·비용/결과 증거 없이는 발송·완료 판정을 하지 않는다.
- 허브 `E:/Coding Infra/AI Infra/Communication/DECISIONS.md`의 D-44는 로컬 기록이다. 허브 저장소는 별도의 dirty/diverged 상태이므로 원격 반영으로 간주하지 않는다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | PR #76의 최종 main/CI·source-only hold·Pages·이 문서의 도달을 확인하고 다음 개발 브랜치를 정한다 | 작음 | 먼저 |
| B | Claude/Codex CLI의 planner `ready`와 실행 어댑터의 no-skill/node 제한을 일치시킨다. 현재 합성 `step(skills=["explain"])`는 planner를 통과하지만 실제 CLI adapter는 거부한다 | 중간 | 허위 준비 상태의 남은 사례 |
| C | AGY와 Grok CLI에 각각 구독 전용 `claim → send once → lookup → verify` 보호 어댑터를 기존 Store에 연결; 계정·모델·effort·쿼터·credit fallback을 전송 직전 재검증 | 큼 | 한도 복구와 무관하게 오프라인 구현 가능 |
| D | 사용량 복구 후 각 xAI 표면을 새로 관측하되, 정확 계정/버킷·구독 포함·초과 과금 차단이 증명될 때만 실호출; Bot과 CLI의 쿼터를 서로 대체하지 않음 | 중간 | 비용 증거가 없으면 계속 차단 |
| E | Claude/Codex 사용자 설치 후보의 자산 보존·Gstack 런타임·호스트 명령 선택·구독 청구를 별도 검증하고 설치 게이트 재판정 | 큼 | 소스 머지를 설치 준비로 오인 금지 |

### 결정 요약
- D-44 독립 토론 판정: 먼저 허위 `ready` 차단, 이후 AGY/Grok 보호 어댑터를 오프라인 구현. 새 중앙 registry 신설은 기존 planner/Store와 중복되어 보류. 소수 의견은 한도 복구 직후 사용성을 위해 어댑터를 선구현하자는 것과 장기적으로 명시적 준비 상태가 유리하다는 것이다.
- D-45 별도 심판은 #76의 코드·이 문서를 같은 최종 HEAD에서 소스 전용 머지하되, 새 CI/hold·기존 CLI planner/adapter 불일치의 인수 기록을 조건으로 했다. 소수 의견은 CLI의 노드별 실행 제한을 먼저 고치자는 것이다. 사용자 설치·실호출·결제 변경은 이 문서로 승인되지 않는다.

### 핵심 파일 위치
```text
skills-src/vibe/SKILL.md                         메인 스킬 계약·비용 경계
skills-src/vibe/scripts/orchestrate.py            실행 경로·과금·쿼터 planner
skills-src/vibe/scripts/test_orchestrate.py       허위 ready 회귀 테스트
skills-src/vibe/references/orchestration.md       런타임·어댑터 운영 계약
skills-src/vibe/scripts/execute_bot.py            GUI 전용 Bot Relay 어댑터
docs/INSTALL.md                                   후보·사용자 설치 게이트
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
gh pr view 76 --json state,headRefOid,baseRefOid,statusCheckRollup
```

`docs/HANDOFF.md`가 아직 `origin/main`에 없으면 PR [#76](https://github.com/Simon-YHKim/SimonK-stack/pull/76)의 본문·변경 파일 또는 아래 브랜치에서 읽는다.

```powershell
git fetch origin fix/vibe-provider-readiness-261001
git show origin/fix/vibe-provider-readiness-261001:docs/HANDOFF.md
```

---
