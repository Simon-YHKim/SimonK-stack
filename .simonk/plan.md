---
sprint-id: 2026-05-23T15:30
user-task: "Graphify 식별·설치·실행 + planning-doc/wiki phase 계획 전부 점검 후 즉시 실행분 처리 + README 통합 패치"
ambiguity-score: 6.25/10 (direct proceed)
sub-tasks: 9
parallel-tasks: 5
sequential-tasks: 4
---

# Plan-to-Action Sprint

## Discovered actions (from planning-docs + wiki scan)

### Phase 3 (6/15~6/30) — 사전 준비 가능
- **A13 Graphify**: `uv tool install graphifyy` + `graphify . --wiki` on SimonKWiki/ → graphify-out/ 생성 → wiki/concepts/ wikilink 시각화
- **A11 Zotero MCP**: `zotero-mcp` 사전 조사 (사용자 계정 결정 후 통합)
- **A12 NotebookLM**: `notebooklm-py` 사전 조사 (사용자 계정 결정 후 통합)
- **A14 OpenHarness**: external/OpenHarness clone 있음 → 사전 셋업 가능
- **C05 obsidian-cli cron Lint**: obsidian-cli kepano 이미 vendored → cron 설정만
- **anthropics/skills Phase 3 추가**: external/anthropics-skills clone 있음 → 통합 검토

### Personal actions (simonK 범위 외 — 본인 영역)
- current-pivot.md `[ ]` 항목들 (커리어, 면접, 멘토링) → 사용자 본인
- 5y-vision 인터뷰 → 별도 세션
- Phase 4·5 자기인식 도구 (애착유형 등) → 본인 선택

### 미래 시기 (skip)
- 5/30 Phase 1 시동 → 이미 simonK 통합으로 선행
- Phase 6 Simon-ohmo (27Y Q1) → 1년 후

## Sub-tasks (이번 sprint)

| # | 작업 | 의존 | 병렬? |
|---|---|---|---|
| 1 | Graphify 설치 (uv → graphifyy) | none | seq (winget sibling) |
| 2 | Graphify SimonKWiki 실행 | 1 | seq |
| 3 | wiki/tools/graphify.md 사용법 문서 | none | par |
| 4 | README 통합 패치 (98 skills + simonk + kepano + SimonKWiki rename + 자동 업데이트 표 + Graphify) | none | par |
| 5 | planning-docs/ → wiki/projects/ action migration | none | par |
| 6 | Phase 3 사전 준비: zotero-mcp / notebooklm-py / openharness 사전 조사 | none | par |
| 7 | obsidian-cli cron Lint 자동화 (C05) | none | par |
| 8 | 검증: validate_skill.py + wiki 구조 lint + bash -n | 1-7 | seq |
| 9 | Commit + push 양쪽 repo + final report | 8 | seq |

## Auto-push 정책 (sprint 동안 적용)

- Full Auto: SimonK-stack + SimonKWiki 모두 자동 commit + push
- PR 생성·머지 X
- 파괴적 작업 X (감지 시 STOP)
- .env / credentials X
