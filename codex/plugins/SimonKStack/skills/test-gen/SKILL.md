---
name: test-gen
description: "Use when the user asks to write tests, add test coverage, or create a test scenario—triggers include \"테스트 작성\", \"write tests\", \"add test coverage\", \"test this function\", \"unit tests\", \"regression test\", \"시나리오 테스트\", \"E2E 시나리오\", \"edge case 뽑아줘\", \"exhaustive test cases\", \"integration test scenarios\", \"what could go wrong\". Produces meaningful deterministic tests covering golden path, edge cases, error paths, plus comprehensive scenario planning (Happy/Sad/Bad/Race/Boundary/Permission/State categories) for integration and E2E coverage."
version: 1.1.0
author: general-dev
---

# Test Generation Skill

Write tests that catch real bugs, not tests that exercise lines for coverage's sake.

## Workflow

1. **Discover the test framework**
   - Look for `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.
   - Find existing test files and **match their style** (naming, structure, helpers, fixtures)
   - Identify the runner command (`pytest`, `npm test`, `cargo test`, `go test`)

2. **Read the code under test**
   - Understand its public contract (inputs, outputs, side effects)
   - List the branches and edge cases
   - Note any external dependencies that need mocking

3. **Plan the test cases** — Cover:
   - **Happy path** — typical valid input
   - **Edge cases** — empty, null, zero, negative, max size, unicode
   - **Error paths** — invalid input, network failure, permission denied
   - **Boundary conditions** — off-by-one, just-below/just-above thresholds
   - **Regression** — if fixing a bug, write a test that fails before the fix

4. **Write the tests**
   - One assertion per concept (multiple `expect` calls are fine if they test the same behavior)
   - Use descriptive names: `test_returns_empty_list_when_user_has_no_orders`
   - Arrange-Act-Assert structure
   - No magic numbers — name your fixtures
   - Tests must be **deterministic** — no real time, no random, no network

5. **Run and verify**
   - All new tests pass
   - Existing tests still pass
   - Try mutating the code under test — do your tests catch the mutation?

## Principles

- **Test behavior, not implementation.** Refactoring shouldn't break tests.
- **One concept per test.** A failing test should point at one specific cause.
- **Fast and isolated.** No shared state between tests, no I/O unless necessary.
- **No flaky tests.** If you can't make it deterministic, don't write it.

## Scenario Planning Mode

복잡한 기능·통합·E2E 테스트가 필요할 때 단위 테스트 너머의 시나리오 매트릭스를 생성한다.

Trigger phrases: "시나리오 테스트", "E2E 시나리오", "edge case 뽑아줘", "exhaustive test cases"

상세 카테고리와 예시는 [references/scenario-matrix.md](references/scenario-matrix.md) 참조.

### 7개 시나리오 카테고리

| 카테고리 | 질문 | 예시 (결제 플로우) |
|---|---|---|
| **Happy** | 정상 흐름은? | 카드 결제 성공 |
| **Sad** | 의도된 실패는? | 잔액 부족 → 적절한 에러 표시 |
| **Bad** | 악의적 입력은? | 음수 금액, 0원, 최대값 초과 |
| **Race** | 동시 발생은? | 같은 카드 두 번 결제 (idempotency) |
| **Boundary** | 경계값은? | 결제 만료 직전 1초, 최대 카드 자릿수 |
| **Permission** | 권한 분기는? | 비로그인, 권한 없는 사용자 |
| **State** | 상태 전이는? | cart → checkout → payment → confirmation |

### 워크플로

1. 기능을 카테고리별로 brainstorm — 각 카테고리에서 최소 1개
2. 시나리오 매트릭스 작성 (입력 × 상태 × 권한)
3. 우선순위 매기기: Critical (Happy + 주요 Sad/Bad) > Important (Boundary + State) > Nice-to-have (희귀 Race)
4. 시나리오별로 단위/통합/E2E 중 적절한 레벨 선택
5. test 파일 생성 (시나리오 = describe block, 케이스 = it/test)

### Integration with simon-tdd

복잡한 기능에서는 simon-tdd의 RED 단계에서 이 모드 호출:
- 시나리오 매트릭스를 먼저 생성
- 각 시나리오를 RED → GREEN → REFACTOR 사이클로 순차 구현
- 한 사이클당 시나리오 1-2개

## Anti-patterns

- 🚫 Tests that mirror the implementation line-by-line
- 🚫 Mocking everything until the test no longer tests real behavior
- 🚫 `assert True` or tests with no assertions
- 🚫 Sleeping in tests to "wait for" async behavior — use proper sync primitives
- 🚫 Tests that only pass when run in a specific order

## Related skills

- `simon-tdd` — RED 단계에서 Scenario Planning Mode 호출 (시나리오 매트릭스 생성)
- `dev-orchestrator` — 단계 4 (시나리오 확장 — 복잡 기능에서만) 진입점
- `code-health-guard` — 시나리오 구현 후 reactive scan
- `app-dev-orchestrator` — 단계 13.5 에서 같이 호출 (Scenario Planning Mode + code-health-guard 병렬)

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
