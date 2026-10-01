# SimonK-stack 세션 인수인계

## Latest — 2026-10-01 / `/vibe` 구독 전용 실행 경로와 핸드오프

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
