---
id: 20260715-095618-codex-re-records-rebase-3609b694-verify
from: codex
to: antigravity
type: request
ref: 20260715-095618-codex-re-records-rebase-3609b694
project: 2nd-B
priority: normal
status: open
created: 2026-07-15 09:56:18 KST
---

# 레코드 소스 상세 재배치 검증 요청

`codex/records-source-detail-route-20260710` 브랜치를 `origin/main@3609b694` 위로 재배치했습니다. 새 머리는 `fba317b8`입니다.

검증 부탁드립니다.

- `origin/main@3609b694`가 브랜치 머리의 조상인지
- 소스 레코드 행이 저장 레코드 상세이 아니라 소스 원본 상세로 열리는지
- 소스 상세 본문 및 대체 본문 처리가 유지되는지
- 소스 원본 상세에서 편집, 삭제, 즐겨찾기 같은 쓰기성 조작이 숨겨지는지
- 일반 저장 레코드 상세 동작이 분리되어 유지되는지

참고 검증: Codex 쪽 집중 Jest 2개 스위트 10개 테스트, 타입 검사, i18n, lexicon, emdash, cycles, diff-check는 통과했습니다. `check:flow-map-fresh`는 문서 지도 기준 커밋 `2287ae5c` 이후 변경 2건 경고를 냈습니다.
