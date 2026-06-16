---
name: simon-tdd
description: Enforces the RED → GREEN → REFACTOR cycle for new features, bug fixes, and regression tests, plus embeds the Boris Cherny verification-loop principle (Claude must be able to verify its own work via server/test/browser commands, not ask the user to check manually). Use this skill PROACTIVELY whenever the user says things like "이 기능 구현해줘", "이거 만들어줘", "버그 고쳐줘", "let's add X", "implement Y", "build a function that does Z", "fix this bug"—EVEN IF they don't mention testing. The skill produces a failing test first, then minimal implementation, then refactor, with an atomic commit per cycle.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Simon TDD

Superpowers `test-driven-development` 스킬의 핵심을 추출·강제하는 TDD 사이클. 사후 정당화 테스트 금지, 검증 루프 필수.

## When to use

- 새 기능 구현 시작 시 (기본값)
- 버그 리포트 → 재현 테스트 먼저
- `app-dev-orchestrator` 단계 13
- 사용자가 "기능 구현", "이거 만들어줘" 요청 시 TDD 로 진입

## Workflow — RED → GREEN → REFACTOR

### Pre-RED: 스펙 모호하면 `/grill-me` 먼저

RED 는 *구체적인 실패 테스트* 를 요구한다. 사용자가 준 스펙에 미해결 분기 (scope, edge cases, error handling) 가 남아 있으면 테스트도 모호해진다. 모호함 감지 시 `/grill-me` 로 1-Q-at-a-time 인터뷰 진행해서 결정 트리 닫고 RED 진입.

판단 기준: "이 테스트의 assertion 을 *지금* 한 줄로 쓸 수 있는가?" 답이 No 면 grill 먼저.

### RED: 실패하는 테스트 먼저

1. 요구사항을 **observable behavior** 로 표현 (구현 세부 아님)
2. 테스트 작성 → 실행 → **실패 확인** (스크린샷/로그로 증거 남김)
3. 실패 원인이 예상과 일치하는지 확인 (syntax error 로 실패 ≠ 유효한 RED)

```bash
npm test -- path/to/new.test.ts
# expect: FAIL with clear assertion mismatch
```

### GREEN: 통과시키는 최소 구현

1. 테스트를 통과시킬 **가장 작은** 코드 작성 (하드코딩도 OK — 이후 리팩토링)
2. 실행 → **성공 확인**
3. 다른 테스트가 깨지지 않는지 전체 스위트 확인

### REFACTOR: 구조 개선

1. 테스트 전부 통과 유지하며 구조 개선
2. 중복 제거, 네이밍 개선, 추출
3. 각 리팩토링마다 테스트 재실행

### 사이클 종료: Atomic Commit

```bash
git add -p  # 변경 검토
git commit -m "feat: <기능>"
# 또는 test-only 사이클이면
git commit -m "test: <테스트 설명>"
```

---

## 검증 도구 제공 원칙 (Boris Cherny)

TDD 와 함께 필수: Claude 가 "잘 됐나?" 를 **스스로 확인**할 수 있도록 도구를 명시적으로 제공.

### 최소 제공 정보

CLAUDE.md 또는 세션 시작 시 아래를 명시:

1. **서버 시작 방법**
   ```
   npm run dev  # http://localhost:3000
   ```
2. **테스트 실행 명령**
   ```
   npm test            # 전체
   npm test -- <pattern>   # 필터
   npm run test:e2e        # Playwright
   ```
3. **브라우저 URL 과 주요 경로**
   ```
   /           — 홈
   /login      — 로그인
   /dashboard  — 대시보드
   ```
4. **DB 접근법** (있을 경우)
   ```
   psql $DATABASE_URL
   supabase db reset  # 로컬 초기화
   ```
5. **린트·타입 체크**
   ```
   npm run lint && npm run typecheck
   ```

### 원칙

- **Claude 가 눈으로 확인할 수 없다면 = 검증 실패**
- 사용자가 수동 확인해야 하는 워크플로는 **자동화 기회**. Playwright / `/browse` / 헬스체크 엔드포인트 추가
- 실행 결과를 로그로 남길 것 (`2>&1 | tee /tmp/run.log`)

---

## Checklist

- [ ] 테스트 먼저, 구현 나중
- [ ] RED 단계에서 실패 로그 확인
- [ ] GREEN 단계에서 최소 코드로 통과
- [ ] REFACTOR 단계에서 구조 개선 + 테스트 재통과
- [ ] 원자적 커밋 (`feat:` 또는 `test:`)
- [ ] 검증 도구 (서버·테스트·브라우저·DB) 가 CLAUDE.md 에 명시됨
- [ ] 사이클당 최대 30분 — 초과하면 스코프 쪼개기

---

## Guard Mode — 구현 전 테스트 강제 (권고가 아닌 차단)

권고는 무시당하지만 차단은 행동을 바꾼다. source 변경에 대응 test 변경이 없으면 BLOCKER.

### 자동 검사

```bash
bash skills-src/simon-tdd/scripts/tdd-guard-check.sh
```

검사 로직:
1. `git diff --cached --name-only` 로 staged 파일 수집
2. source 파일 (`*.ts`, `*.tsx`, `*.js`, `*.jsx`, `*.py`)별로:
   - 대응 test 파일 존재 확인 (`*.test.*`, `*.spec.*`, `test_*.py`, `*_test.py`)
   - 동일 staging에 test 파일도 추가/변경됐는지 확인
3. 위반 시 exit 1 + 위반 파일 목록 출력

### Pre-commit hook 통합 (권장)

```bash
# .git/hooks/pre-commit 또는 husky
bash skills-src/simon-tdd/scripts/tdd-guard-check.sh || {
  echo "TDD Guard 위반: 테스트 없이 source 변경"
  exit 1
}
```

### 예외

- 문서·설정 파일 (`*.md`, `*.json`, `*.yml`, `*.yaml`) 자동 제외
- 명시적 우회: `git commit --no-verify` (사용자 책임. 실수 방지 위해 권장 안 함)

## Anti-patterns

- ❌ 테스트 없이 코드 먼저 작성
- ❌ 구현 이후 테스트 작성 (사후 정당화)
- ❌ RED 단계 skip — "이건 분명히 실패할 거야" 로 넘어감
- ❌ 테스트가 pass 되지 않은 상태로 커밋
- ❌ 테스트를 mocking 으로 떡칠해서 실제 로직 검증 안 됨
- ❌ 사용자에게 "브라우저 열어서 확인해주세요" (Claude 가 `/browse` 로 직접 확인해야)
- ❌ 한 커밋에 여러 기능 + 여러 리팩토링 섞기

## Related skills

- `simon-worktree` — 병렬 기능 개발
- `/qa` — E2E QA 자동화
- `/review` — PR 사전 리뷰
- `/browse` — 브라우저 자동 검증 (검증 루프)
- `/health` — 코드 품질 대시보드
- `investigate` — 버그 root cause (재현 테스트 먼저)

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
