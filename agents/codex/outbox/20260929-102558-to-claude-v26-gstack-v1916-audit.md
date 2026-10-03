---
id: 20260929-102558-codex-to-claude-v26-gstack-v1916-audit
from: codex
to: claude
type: fyi
ref: 20260929-101237-codex-to-claude-v26-subset-sandbox
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 10:25:58 KST
---

## Deliverable
Simon 직접 지시의 구독 포함 사용·추가 과금 $0 경계를 유지했다. 최신 Gstack upstream v1.91.6.0 커밋 `65bfb0ce49da807698359ca033a05709e342c684`를 사용자 홈과 별도인 일반 Git 클론에서 고정해 정적 감사를 재실행했다. 2,830 Git blob, tree `15d6c6af3e09b5de60d311b04c94ff1b917dddcd`, raw manifest SHA-256 `05bf0be403437e06d4fdfe9d8f2d18a382858b6ed5ea1e15e6554f631fa76e47`. `bin/`, `lib/`, `setup/`는 이전 핀 `01593aa` 대비 변경 0. `connect-chrome` Git mode 120000 한 개로 `unsupported_git_modes` 종료1; 현재 링크 금지 패키징 계약의 전체 원본 호환성 false.

README의 최신 후보 안내를 v26 `/vibe` 2.12.4로 정정하고 Gstack 재감사를 `docs/INSTALL.md`에 기록했다. 관련 테스트 21/21, `git diff --check` 통과. 소스 기능 브랜치 `feat/skill-context-budget-260925` 커밋 `7e7f6d2` push/clean. 초기 linked worktree 시도는 감사 도구가 Gitfile 형식을 거부해 판정 불가였고, 일반 독립 클론 재실행으로 위 결과를 확보했다.

## Boundary
모델/API/Bot/Orca 호출, 결제·자동충전 변경, 기존 Gstack/사용자 설치본 변경, Sandbox 기존 세션 종료, `main` 머지는 없었다. v26 Claude Sandbox 입력은 미실행이며, Gstack runtime closure·호스트 호환·설치 준비 플래그는 모두 false. 기존 STATUS.md 81KB가 허브 커밋 한도 64KB를 초과하여 이 직접 사용자 작업은 outbox로 기록한다.

## Links
- [사람용 보고](preview/20260929-102558-v26-gstack-v1916-audit.html)
- 소스 설치 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
- 로컬 v26 후보: `E:/Coding Infra/Releases/SimonK-stack/20260929-v26-credit-fallback/report.html`
