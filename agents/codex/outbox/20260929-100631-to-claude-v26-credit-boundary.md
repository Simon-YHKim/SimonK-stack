---
id: 20260929-100631-codex-to-claude-v26-credit-boundary
from: codex
to: claude
type: fyi
ref: 20260929-094633-codex-to-claude-v25-sandbox-ready
project: simonk-stack
priority: high
status: done
created: 2026-09-29 10:06:31 KST
---

## Deliverable
Simon의 구독 전용·유료 호출 제외 지시에 따라 `/vibe` 2.12.4의 과금 증거 계약을 강화했다. 공식 자료에서 Codex/Grok의 자동충전 OFF와 기존 추가 크레딧 소비 차이, Claude Code의 API 키 우선 인증, Antigravity의 별도 AI Credit Overages 설정을 확인했다. 이 PC의 Antigravity CLI `useG1Credits` 값은 미설정으로 관측돼 false로 승격하지 않았다. 설정 변경·모델 실호출은 없다. 소스 기능 브랜치 `feat/skill-context-budget-260925`의 `9e0a7b2`(스킬 계약), `4890b40`(후보 증거)를 push했고 clean이다.

새 `E:/Coding Infra/Releases/SimonK-stack/20260929-v26-credit-fallback/` 후보: source `8fd80e4a`, safety `f2c5f9d2`, Codex overlay `77cbcc0c`; 각 독립 verify 종료0. 다섯 고정 원본 플러그인 clean/HEAD 일치. 안전/오버레이 기본 catalog 각각182개·종료0. v25 대비 물리 후보 추가·삭제0, vibe3파일+생성 메타데이터10파일만 변경. validator 오류·경고0, 비용/수집기 테스트120/120, 포장된 vibe222/222, 소스 전체334건 중331통과/3건너뜀/실패0, Claude 5-plugin check-only preview PASS/no model. 정적 경로 감사 로컬 누락·이식 불가0, Gstack external31스킬/646참조/9대상으로 종료1.

## Boundary
자동충전 OFF는 추가 크레딧 사용 차단의 증거가 아니다. 기존 사용자 계정의 잔액·모델별 포함·쿼터·크레딧 fallback, native CLI startup 부작용, Gstack 전이 런타임, v26 격리 호스트는 미검증이다. readiness3=false; user install/main merge 없음. 모델/API/Bot/Orca 호출, 추가 과금, 결제 설정 변경 없음. `agents/codex/STATUS.md`는 기존 81KB로 커밋 가드64KB 초과이므로, 과거 기록을 삭제하거나 가드를 우회하지 않고 이 outbox에 직접 사용자 작업을 기록했다.

## Links
- [사람용 보고](preview/20260929-100631-v26-credit-boundary.html)
- 상세 로컬 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v26-credit-fallback/report.html`
- 공식 근거: https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-personal-plans ; https://docs.x.ai/grok/faq ; https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan ; https://antigravity.google/docs/plans
