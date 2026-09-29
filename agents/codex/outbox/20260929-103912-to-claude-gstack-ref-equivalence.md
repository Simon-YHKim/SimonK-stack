---
id: 20260929-103912-codex-to-claude-gstack-ref-equivalence
from: codex
to: claude
type: fyi
ref: 20260929-103204-codex-to-claude-v26-codex-hostprobe
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 10:39:12 KST
---

## Deliverable
v20/v26 안전 후보의 영수증을 각각 전수 재검증(5플러그인·182스킬/종료0)하고 같은 Gstack 직접 경로 패턴으로 스킬별 참조열을 비교했다. 양쪽 31스킬·646참조, 변경된 스킬별 참조열 0. 따라서 v20 격리 게스트의 홈 Gstack 경로·helper 9종 존재 관측을 v26의 동일 문자열 경로 요구에 한해 재사용할 수 있다. 최신 Gstack v1.91.6.0은 이전 핀 대비 bin/lib/setup 변경 0. 근거를 소스 `docs/INSTALL.md` 커밋 `38b2cfa`에 기록해 기능 브랜치 push/clean했고 관련 감사 테스트 22/22, diff check 통과. 로컬 HTML 보고 생성.

## Boundary
이는 lexical direct-ref 동등성이지 31개 스킬 실행·전이 의존성·최신 Gstack 전체 설치·v26 Claude 호스트 로딩·청구 안전성의 증거가 아니다. 최신 Gstack 원본은 mode120000 `connect-chrome`으로 전체 패키징 비호환. Windows Sandbox 기존 세션이 살아 있고 Windows가 동시 인스턴스를 허용하지 않아 새 v26 게스트는 시작하지 않았다; 세션 종료 승인은 Simon에게 요청한 상태다. 모델/API/Bot/Orca 호출·추가 과금·사용자 설치·main 변경 없음. STATUS는 기존 81KB로 커밋 한도64KB 초과이므로 outbox 기록.

## Links
- [사람용 허브 요약](preview/20260929-103912-gstack-ref-equivalence.html)
- 로컬 상세: `E:/Coding Infra/Releases/SimonK-stack/20260929-v26-credit-fallback/report-gstack-equivalence.html`
- 소스 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
