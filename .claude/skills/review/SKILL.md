---
name: review
description: Use when the user asks for a code review or feedback on code—triggers include "review this", "code review", "리뷰해줘", "check this code", "feedback on my code", "is this good". Produces a prioritized review with severity levels (blocker / major / minor / nit) and actionable fix suggestions.
version: 1.0.0
author: general-dev
---

# Code Review Skill

Provide actionable, prioritized feedback on code changes.

## Workflow

1. **Identify scope** — What is being reviewed?
   - Uncommitted changes: `git diff` (and `git diff --staged`)
   - Branch vs main: `git diff main...HEAD`
   - Specific files: read them in full
   - PR: fetch the diff via the GitHub MCP tools

2. **Read context** — Don't review in isolation:
   - Read the files being modified, not just the diff hunks
   - Check related tests and callers
   - Understand the intent before judging

3. **Review checklist** — Evaluate against:

   **Correctness**
   - Logic errors, off-by-one, null/undefined handling
   - Race conditions, concurrency issues
   - Error handling at boundaries

   **Security**
   - Input validation, injection risks (SQL, XSS, command)
   - Secrets in code, insecure defaults
   - Authentication/authorization checks

   **Maintainability**
   - Naming clarity
   - Function/file size and single responsibility
   - Dead code, duplicate code
   - Unnecessary complexity or premature abstraction

   **Testing**
   - Are tests included? Do they cover edge cases?
   - Are tests deterministic?

   **Performance** (only if it matters here)
   - N+1 queries, unnecessary loops, memory leaks

4. **Report format** — Group by severity:
   - 🔴 **Blocking** — must fix before merge
   - 🟡 **Should fix** — important but not blocking
   - 🟢 **Nit / suggestion** — optional polish

   For each issue: cite `file_path:line_number`, explain the problem, and propose a concrete fix.

## Pre-Merge Cleanup Scan

머지 직전 (PR 승인 전) 추가로 실행. legacy 코드와 누락된 정리를 찾아냄.

Trigger phrases: "merge 전 정리", "dead code check", "pre-merge cleanup", "legacy 정리", "unused imports"

자동화: `bash .claude/skills/review/scripts/pre-merge-scan.sh`

### 1. Dead code detection

- TS: `npx ts-unused-exports tsconfig.json`
- JS: `npx unimported`
- Python: `vulture src/` 또는 `pyflakes src/`
- 주석 처리된 코드 블록 > 3 lines → 삭제 (git history가 보존함)

### 2. Unused imports

- TS: `npx tsc --noUnusedLocals --noEmit` 또는 ESLint `no-unused-vars`
- Python: `autoflake --check --remove-all-unused-imports src/`
- Go: `goimports -l ./...`

### 3. Orphaned files

- 어디서도 import 되지 않는 source 파일
- source 파일이 삭제됐는데 남은 test 파일
- 제거된 feature의 config/migration 파일

검색: `grep -L "from.*<filename>" src/` 또는 `unimported`

### 4. 보고 형식

```markdown
## Pre-Merge Cleanup — N items

### Dead code (3)
- [ ] `src/legacy/old-api.ts` — 어디서도 import 안 됨, last edit 6개월 전
- [ ] `src/utils/format.ts:45-67` — 주석 처리된 함수, git history에 남아있음
- [ ] `src/feature/auth/_unused-helper.ts` — `_` prefix는 명시적 미사용 표시

### Unused imports (5)
- [ ] `src/page/dashboard.tsx:3` — `import { unused } from '@/lib'`
- [ ] ...

### Orphaned files (2)
- [ ] `src/feature/legacy-billing/` — 전체 디렉토리, 새 billing으로 교체됨
- [ ] `tests/old-checkout.test.ts` — source가 이미 삭제됨
```

각 항목은 file_path + 이유 + 권장 액션 명시.

## Principles

- Be specific. "This is confusing" is useless; "rename `x` to `userCount` because..." is actionable.
- Praise good patterns when you see them.
- Don't nitpick style if a formatter exists — let the tool handle it.
- Distinguish facts ("this throws on null") from opinions ("I prefer guard clauses").
- Pre-merge cleanup은 PR 머지 직전 강제 단계. dead code는 머지 후 추적이 더 어려워짐.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
