---
id: 20260814-085450-codex-re-phone-shell-back-i18n
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-14 08:54:50 KST
---

# 폰 셸 뒤로가기 라벨 지역화

열린 codex 주문은 stale 또는 기처리 항목이라 재처리하지 않았고, 이번 한 주기는 2nd-B UI 접근성 레인에서 새 결함 하나를 처리했습니다.

- 기준: `origin/main 5ba0cdd905ec3e9e2d5aac0fceb17830c556ab09`
- worktree: `C:\2ndB\.worktrees\codex-qa-20260814-085213`
- branch: `codex/qa-cycle-20260814-085213`
- local app commit: `9382d9eb19c7cabbe3cd114f2ff985208191b7f1`
- 변경: `PhoneShell.tsx`의 하드코딩된 `accessibilityLabel="뒤로"`를 `common:navGraph.drilldown.back`으로 지역화하고 source-scan guard를 추가했습니다.
- 검증: targeted Jest, Prettier, ESLint, type-check, i18n, untranslated-i18n, lexicon, constraints, emdash, anti-anthro, mascot-voice, cycles, diff-check, sensitive-pattern scan 통과.
- push: 하지 않음.

## Links

- HTML report: `agents/codex/outbox/preview/20260814-085450-phone-shell-back-i18n.html`
