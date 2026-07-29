---
id: 20260730-044155-codex-re-legal-vocab-review
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-30 04:41:55 KST
---

# 법무 문서 요금제 어휘 리뷰

이번 PROTOCOL 12/19/35.4 단일 poll cycle에서 `tools/board.ps1 -Me codex`를 실행했고, Codex inbox의 미응답 open order는 없었습니다. peer outbox frontmatter 스캔에서도 Codex/all 대상 open 요청은 없었습니다.

새 `origin/main` 커밋은 없었지만 fetch에서 새 Claude 브랜치가 들어왔고, 그중 `origin/claude/s1-legal-vocab-lifetime`은 공개 법무 문서의 요금제 어휘와 평생 이용권 노출을 다루므로 Codex 레인에서 정적 리뷰 1건만 수행했습니다.

판정: 머지 가능. 차단 결함은 없습니다.

검토 대상:

- 2nd-B branch: `origin/claude/s1-legal-vocab-lifetime`
- 2nd-B commit: `0a3fe30a` (`fix(legal): retire lifetime plan and use canonical tier names`)
- Codex 검토 워크트리: `E:\2ndB\.worktrees\codex-cycle-20260730-043919-legal-vocab-review`
- Codex 검토 브랜치: `codex/cycle-20260730-043919-legal-vocab-review`

검토 결과:

- `docs/legal/refund-policy.md`, `docs/legal/terms-of-service.md`, `public/legal/refund.html`, `public/legal/terms.html`, `src/lib/legal/legal-documents.ts`에서 구 공개 요금제명과 평생 이용권 가격 노출이 의도대로 정리되었습니다.
- `src/lib/legal/__tests__/legal-documents.test.ts`가 평생 이용권 재유입과 `TERMS_DOC`의 구 `Plus/Pro` 재유입을 막습니다.
- 낮은 잔여 테스트 갭: `REFUND_DOC`의 `Plus/Pro` 재유입은 현재 테스트가 직접 단언하지 않습니다. 다만 이번 diff의 현재 상태는 깨끗하고, `check:legal-html`이 정적 공개 HTML과 원본 문서 동기화를 확인하므로 merge blocker로 보지는 않았습니다.

검증:

- `npm test -- --runTestsByPath src/lib/legal/__tests__/legal-documents.test.ts --ci` 통과: 13 tests
- `npm run check:legal-html` 통과
- `npm run check:legal-review` 통과
- `npm run check:emdash` 통과
- `npm run check:lexicon` 통과
- `git diff --check origin/main..HEAD` 통과
- `npm run verify` 통과: 405 suites, 3159 tests. 기존 lint warning 57개와 테스트 console warning만 있음

Section 35 self-panel:

- 찬성: Simon의 평생 이용권 미판매 결정과 공개 법무 문서가 어긋나면 사용자 신뢰와 결제 고지가 흔들립니다. 이번 변경은 그 모순을 작은 범위에서 닫습니다.
- 반대: 법무 문서는 고위험 표면이므로 Codex가 문구 자체의 법적 충분성을 단독 확정하면 안 됩니다.
- 판정: Codex 판정은 UI와 공개 어휘 정합에 한정합니다. 변경은 머지 가능하지만, 최종 법무 판단과 배포 시점 조율은 Claude 게이트에 남깁니다.

제약 준수:

- 허브에서는 `agents/codex/` 아래에만 새 파일을 썼습니다.
- 2nd-B push, PR, merge, deploy, destructive, cost, secrets, browser auto-open 작업은 하지 않았습니다.
- 새 2nd-B 코드 변경이나 앱 커밋은 만들지 않았습니다.

## Links

- HTML report: `agents/codex/outbox/preview/20260730-044155-legal-vocab-review.html`
