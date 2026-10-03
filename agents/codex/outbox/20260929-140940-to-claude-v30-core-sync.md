---
id: 20260929-140940-codex-to-claude-v30-core-sync
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: done
created: 2026-09-29 14:09:40 KST
---

Simon 직접 지시의 추가 과금 $0 범위에서 Stack 기능 브랜치 `feat/skill-context-budget-260925`의 Core source-owned `json-canvas` 예시 참조 목차를 원본 Core `a07a1e9`와 동기화했다. Stack commit `5cec2c6`와 문서 commit `18b6034`를 push했고 worktree clean이다. v30 격리 후보 네 영수증(source, safety bundle, Codex overlay, general subset)을 독립 verify했다. v29b 대비 추가/삭제 파일 0, 바뀐 12개는 JSON Canvas 참조 1개·메타데이터 10개·영수증 1개다.

후보 5플러그인·182스킬·741파일, 182/182 스킬 validator 통과·비차단 경고 31(v28:34), Claude Code CLI 2.1.284 strict manifest 5/5, Codex manifest 5/5, 번들/오버레이/subset 회귀 55/55 통과했다. v29b의 전체 341건을 v30에서 재실행했다고 주장하지 않는다. JSON Canvas 소스 strict YAML·validator 오류/경고 0, 평가 2건 dry-run 형식 검사 통과다. 모델/Bot/API 실호출·추가 과금·사용자 설치·main 변경 없음. 세 readiness 플래그 false이며 실제 호스트 런타임/캐시 이관은 검증되지 않았다.

v30 safety bundle digest: `e312d41b12b7413bd334ceba695eec561e459958ccb63a0f42394b5c13f44681`. 플러그인별 버전 계약 D-code는 허브 `DECISIONS.md`에 아직 없어서 생성기 변경은 보류했다. 다음 게이트는 해당 결정·회귀, Gstack 전이 런타임, 실제 호스트 이관이다.

## Links

- 사람용 미리보기: `agents/codex/outbox/preview/20260929-140940-v30-core-sync.html`
- 전체 로컬 보고서: `E:/Coding Infra/Releases/SimonK-stack/20260929-v30-core-source-sync/report.html`
- Stack 설치 기록: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
