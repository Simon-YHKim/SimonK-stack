---
id: 20260806-232156-codex-re-plans-analytics-source
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-06 23:21:56 KST
---

# 플랜 진입 분석 보정

열린 Codex 요청이 없어 Codex 레인의 단일 자율 작업으로, 2nd-B 플랜 화면의 실제 유입 경로가 `plans_viewed` 분석 이벤트에서 `direct`로 뭉개지는 문제를 수정했습니다.

- 2nd-B 작업트리: `C:\2ndB\.worktrees\codex-qa-free-upgrade-copy-20260806-2330`
- 브랜치: `codex/qa-free-upgrade-copy-20260806-2330`
- 커밋: `821376fe fix: preserve plans analytics entry sources`
- 푸시: 하지 않음

변경 내용:
- `src/lib/analytics/index.ts`: `PlansViewedSource`와 `normalizePlansViewedSource` 추가
- `src/app/plans.tsx`: `params.from`을 중앙 정규화 함수로 처리
- `src/lib/analytics/__tests__/analytics.test.ts`: `ai_limit`, `advisor_lock`, `reasoning_limit`, `northstar_limit`, `persona_*`, unknown fallback 보존 테스트 추가

검증:
- `npm test -- --runTestsByPath src/lib/analytics/__tests__/analytics.test.ts --ci` 통과, 43개 테스트
- `npm run type-check` 통과
- `git diff --check` 통과
- 변경 diff 시크릿 패턴 검사 통과

제약 준수:
- 허브 쓰기는 `agents/codex/` 안에서만 수행
- 2nd-B push 없음
- 파괴적 작업, 비용 작업, 시크릿 작업 없음
- 이번 사이클의 실제 작업은 이 분석 보정 1건만 수행

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260806-232156-plans-analytics-source.html`
