---
name: dev-orchestrator
description: "Use when the user asks to implement a feature, fix a bug, or refactor code—triggers \"기능 구현해줘\", \"버그 고쳐줘\", \"리팩토링 해줘\", \"implement this\", \"fix this\", \"add feature\". Produces a 7-step pipeline: diagnose → structure check (code-health-guard) → TDD test-first (simon-tdd Guard) → scenario testing (test-gen) → code health reactive scan → pre-merge cleanup (review) → conventional commit. Chains all recently added skills into one automatic flow for day-to-day coding. For NEW apps use app-dev-orchestrator, for security use security-orchestrator."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon-stack
---

# dev-orchestrator

일상 개발 작업 (기능 추가, 버그 수정, 리팩토링)의 전 과정을 자동으로 체인하는 통합 orchestrator.

`app-dev-orchestrator` = 새 앱 (21단계)
`security-orchestrator` = 보안 감사 (5단계)
**`dev-orchestrator` = 일상 개발 (7단계)**

## 발동 조건

사용자가 기존 프로젝트에서 코드 작업을 요청할 때:
- "이 기능 구현해줘", "버그 고쳐줘", "리팩토링 해줘"
- "implement this", "fix this bug", "add feature", "refactor"
- 명시적 호출: `dev-orchestrator`

**발동하지 않는 경우**:
- "새 앱 만들자" → `app-dev-orchestrator`
- "보안 점검" → `security-orchestrator`
- "디자인 만들어줘" → `simon-design-first`

## Workflow — 7단계

### 단계 1. 진단 (Diagnose)

코드를 바로 쓰지 않는다. 먼저 이해.

1. 사용자 요청을 분석: 기능 추가 / 버그 수정 / 리팩토링 중 어떤 유형?
2. 관련 코드 읽기 (`Read`, `Grep`)
3. 기존 테스트 확인 (`find . -name "*.test.*" -o -name "*.spec.*"`)
4. CLAUDE.md 의 검증 도구 확인 (서버 시작 명령, 테스트 명령 등)

산출물: 한 문단 요약 — "무엇을, 왜, 어디서"

### 단계 2. 구조 점검 (Structure Check) — `code-health-guard`

코드 작성 전 아키텍처 확인.

1. 새 파일이 필요하면: file placement decision tree로 위치 결정
2. 기존 코드면: import direction 확인 (상위 의존 없는지)
3. 함수 size > 40 lines? → 분리 후보 표시
4. 순환 의존 스캔 (있으면): `bash skills-src/code-health-guard/scripts/check-circular-deps.sh`

이 단계는 30초면 끝남. 스킵 유혹 금지.

### 단계 3. TDD — `simon-tdd` (Guard Mode)

RED → GREEN → REFACTOR 사이클. 테스트 먼저.

**버그 수정**: 실패하는 재현 테스트 먼저 작성
**기능 추가**: 요구사항을 테스트로 표현
**리팩토링**: 기존 테스트 통과 확인 후 구조 변경

Guard Mode: source 변경 시 대응 test 변경이 없으면 BLOCKER.
`bash skills-src/simon-tdd/scripts/tdd-guard-check.sh`

### 단계 4. 시나리오 확장 — `test-gen` (Scenario Planning)

복잡한 기능에서만 실행 (단순 변경은 skip).

기준: 변경이 2개 이상 state를 가지거나, 외부 API를 호출하거나, 권한 분기가 있을 때.

7개 카테고리 (Happy/Sad/Bad/Race/Boundary/Permission/State) 중 관련 카테고리만 적용.
상세: `skills-src/test-gen/references/scenario-matrix.md`

### 단계 5. 코드 품질 재점검 — `code-health-guard` (Reactive)

구현 완료 후 한 번 더 확인.

1. 순환 의존 발생 안 했는지
2. 큰 파일 만들어지지 않았는지
3. 중복 코드 생기지 않았는지
4. naming convention 위반 없는지

### 단계 6. Pre-Merge Cleanup — `review` (Pre-Merge)

커밋 전 정리.

1. unused imports 제거
2. 주석 처리된 코드 > 3줄 삭제
3. dead code 확인
4. `bash .claude/skills/review/scripts/pre-merge-scan.sh`

### 단계 7. 커밋 — `commit`

Conventional Commits 형식으로 원자적 커밋.

- 버그 수정: `fix(scope): description`
- 기능 추가: `feat(scope): description`
- 리팩토링: `refactor(scope): description`
- 테스트: `test(scope): description`

## 병렬 실행 — `agent-delegate`

단계 2 + 3 (구조 점검 + TDD)이 독립적이면 Fan-out으로 병렬 가능.
단계 4 (시나리오)가 크면 카테고리별로 Fan-out.

`agent-delegate` 원칙: file path만 전달, output contract 명시, round-trip 없이 완료.

## 축약 모드

단순 변경 (1 파일, 1 함수, 외부 의존 없음)일 때:
- 단계 2 → 5초 체크 (file placement만)
- 단계 4 → skip
- 단계 5 → skip
- 단계 6 → unused import만

복잡 변경 (multi-file, 외부 API, state machine)일 때:
- 전 단계 실행
- 단계 4의 시나리오 매트릭스 필수

## Anti-patterns

- ❌ 진단 없이 바로 코드 작성
- ❌ TDD 스킵 ("간단한 변경이니까")
- ❌ Guard Mode 우회 (`--no-verify`)
- ❌ Pre-merge cleanup 없이 커밋
- ❌ 복잡 변경에서 시나리오 확장 스킵
- ❌ 구조 점검 없이 새 파일 임의 위치에 생성

## Related skills

- `app-dev-orchestrator` — 새 앱 (이 skill은 기존 프로젝트)
- `security-orchestrator` — 보안 (이 skill은 개발 전반)
- `simon-design-first` — 디자인 작업은 여기서 분리
- `investigate` — 디버깅이 복잡할 때 (root cause 분석 전용)

## Skill 계층도

```
사용자 요청
  │
  ├─ "새 앱 만들자" → app-dev-orchestrator (21단계)
  ├─ "보안 점검" → security-orchestrator (5단계)
  ├─ "디자인 만들어줘" → simon-design-first
  └─ "기능 구현 / 버그 수정 / 리팩토링" → dev-orchestrator (7단계)
       │
       ├─ 1. 진단
       ├─ 2. code-health-guard (proactive)
       ├─ 3. simon-tdd (Guard Mode)
       ├─ 4. test-gen (Scenario Planning) — 복잡할 때만
       ├─ 5. code-health-guard (reactive)
       ├─ 6. review (Pre-Merge Cleanup)
       └─ 7. commit
```
