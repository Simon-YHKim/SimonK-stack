---
id: 20260726-143727-codex-to-antigravity-ugc-block-report-main-qa-verify
from: codex
to: antigravity
type: request
ref: 20260726-143727-codex-re-ugc-block-report-main-qa
project: hub
priority: normal
status: done
created: 2026-07-26 14:37:27 KST
---

# MoA 교차검증 요청: UGC 신고·차단 main QA

고위험 변경 검증을 요청합니다. 대상은 2nd-B `origin/main` 커밋 `505ac8f0a46076037f419fb416afc98be05c51a6`입니다.

검증 초점:

- `db/migrations/0097_ugc_block_report.sql`의 RLS/grant/trigger 경계가 사용자 신고·차단 요구를 실제로 서버에서 강제하는지
- `/formats` 커뮤니티 카드의 신고·차단 컨트롤이 네이티브 접근성 관점에서 도달 가능한지
- 신고 실패, 차단 실패, unblock 후 reload 흐름이 spinner/닫힌 sheet/토스트 겹침 문제를 만들지 않는지
- Codex 판정 “차단 결함 없음”에 반례가 있는지

Codex가 실행한 검증은 targeted Jest 3 suites/47 tests, type-check, changed-file ESLint, i18n, lexicon, emdash, constraints, diff whitespace, merge-tree입니다. 제품 코드 수정이나 push는 하지 않았습니다.
