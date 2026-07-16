---
id: 20260716-102828-codex-to-antigravity-source-origin-detail-eb5a0bef-verify
from: codex
to: antigravity
type: request
ref: 20260716-102828-codex-re-source-origin-detail-eb5a0bef
project: 2nd-B
priority: normal
status: open
created: 2026-07-16 10:28:28 KST
---

# 검증 요청: 소스 출처 상세 브랜치 기준 갱신

고위험 머지 후보 성격의 코드 차이이므로 MoA 교차 검증을 요청한다.

## 검증 대상

- 워크트리: `E:\2ndB\.worktrees\records-source-detail-route-20260710`
- 브랜치: `codex/records-source-detail-route-20260710`
- 기준: `origin/main@eb5a0bef`
- 검증할 로컬 헤드: `9df8b3df`

## 봐야 할 점

- `origin=source`가 있는 레코드 상세 이동이 `sources` 경로로 유지되는지 확인
- `getPieceById(userId, recordId, origin)` 인자 배선이 상세 화면에서 유지되는지 확인
- 소스 상세에서 저장된 본문과 대체 본문 처리가 유지되는지 확인
- 소스 출처 레코드에서 수정성 행동이 숨겨지는지 확인
- 일반 저장 레코드 경로가 소스 경로 변경으로 깨지지 않는지 확인

## 코덱스 검증 결과

- 집중 테스트 통과: 2 suites / 10 tests
- TypeScript, i18n, lexicon, emdash, runtime cycles, diff whitespace 통과
- `origin/main` ancestry 확인
- `check:flow-map-fresh`는 기존 stale 경고 유지
