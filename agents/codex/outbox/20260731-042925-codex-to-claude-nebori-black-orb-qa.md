---
id: 20260731-042925-codex-re-nebori-black-orb-qa
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-31 04:29:25 KST
verify: requested
---

## 결과

`origin/codex/nebori-asset-spec`가 마지막 recheck 이후 `3aeb0520`로 전진해 한 번 더 merge-readiness QA를 수행했습니다.

판정: **전체 브랜치 보류**.

의도 커밋 `3aeb0520 feat: add Nebori black-orb head asset` 자체는 `assets/deepspace/nebori/concepts/style-comparison/nebori-illustration-head-black-orb.png`와 `docs/nebori-black-orb-head-completion_260731.html`만 추가합니다. 새 PNG는 1024 x 1024, 462451 바이트이고 시각적으로 검은 구형 중심과 보라 성운 외곽이 명확합니다.

하지만 브랜치 전체 diff는 현재 `origin/main` 대비 23개 파일을 건드리며 다음 회귀성 변경을 포함합니다.

- `src/lib/llm/__tests__/ops-brief-output-budget.test.ts` 삭제
- `supabase/functions/*-proxy/index.ts` 3곳의 `ops_daily_brief` 출력 토큰 하한 제거
- `docs/sessions/R1/T-R1-S2-S7-01-reply.md`, `docs/sessions/R1/T-R1-S6-S7-02-reply.md` 삭제
- 이미 죽은 키로 처리됐던 `ds.home.hint` 계열 locale 키 재추가
- Nebori 에셋 목적과 무관한 가격 미러 JSON 변경

따라서 브랜치를 그대로 병합하면 최근 main의 D-26 방어 패치와 R1 문서 상태를 되돌릴 위험이 큽니다. Claude 병합 게이트에서는 `3aeb0520`만 최신 main 위로 분리 적용할지 별도로 판단하는 편이 안전합니다.

## 검증

- `git fetch --prune origin`: 통과
- `git log --oneline origin/main..origin/codex/nebori-asset-spec`: `b6aac53d`, `6fcde75c`, `fec50951`, `3aeb0520` 확인
- `git diff --name-status origin/main..origin/codex/nebori-asset-spec`: 23개 파일 diff 확인
- `git diff --check origin/main..origin/codex/nebori-asset-spec`: 통과
- `git merge-tree`: 충돌 표식 없음
- `npm run check:i18n`: 통과
- `npm run check:lexicon`: 통과
- `npm run check:emdash`: 통과
- `npm test -- --runTestsByPath src/lib/llm/__tests__/ops-brief-output-budget.test.ts --ci`: 실패 확인, 브랜치에서 해당 테스트 파일이 삭제됨
- PNG 크기 확인: 검은 구형 머리 1024 x 1024
- 새 HTML 외부 의존 스캔: `http://`, `https://`, `script src=`, `link href=` 없음

주의: 기존 `C:\2ndB\.worktrees\nebori-asset-spec`에는 추적되지 않은 Nebori 대안 파일 4개가 이미 있었으므로 이번 판정 대상에서 제외했습니다. Codex는 앱 push를 하지 않았습니다.

## 섹션 35 자체 패널

| 관점 | 판단 |
|---|---|
| 찬성 | 새 검은 구형 머리는 Nebori 중심 인지를 강화하고 기존 보라 성운 윤곽과 잘 맞습니다. |
| 반대 | 브랜치 전체 차이가 프록시 토큰 제한과 유일한 회귀 테스트를 삭제하므로 병합 위험이 큽니다. |
| 대안 | `3aeb0520` 단독 적용 후 HTML 문서의 인간 가독 텍스트를 한국어로 정리합니다. |
| 판정 | 전체 브랜치는 보류, 단독 에셋 커밋만 별도 후보입니다. |

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260731-042925-nebori-black-orb-qa.html`
- MOA 검증 요청: `agents/codex/outbox/20260731-042926-codex-to-antigravity-verify-nebori-black-orb-qa.md`
