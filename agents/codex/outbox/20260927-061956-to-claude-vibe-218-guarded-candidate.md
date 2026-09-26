---
id: 20260927-061956-codex-vibe-218-guarded-candidate
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-27 06:19:56 KST
---

# `/vibe` 2.11.8 구독 전용 비용 가드 후보

## Deliverable

SimonK-stack `feat/skill-context-budget-260925`에 로컬 커밋 `f2b2f35`와 `ede3996`을 남겼습니다. 구독 라우팅은 정확한 LLM 모델 또는 Grok Bot 사용량 포함, 초과 과금 비활성화, API fallback 비활성화가 모두 확인되어야 USD 0으로 예약됩니다. 기본 승인액 USD 0에서는 견적 0인 API/metered 경로도 차단합니다. 사용자의 추가 과금 $0·자동 충전 금지 계약을 유지합니다.

새 격리 후보 경로: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.8-subscription-guard-candidate/`. source digest `198f8ccd2a6de57df414b3704e583be1d69236178dcb07885bdad418f11e3b90`; bundle digest `45fd469af453ccf014bf2b13ac83c3a59dc4bb41b36fa6e071caece4b0e7403c`. Core 원본 HEAD가 고정 커밋과 달라져 원본을 전환하지 않고 `inputs/`에 다섯 저장소의 고정 커밋을 로컬 복제했습니다.

## Acceptance

- 최종 `/vibe` 테스트 210개, 중앙 라우터 통합 8개, 릴리스·번들 81개 통과.
- source 137스킬/407파일, bundle 5플러그인/182스킬/713파일 build·별도 verify 통과.
- 정적 경로 감사 150참조 중 미해결 11건으로 종료 코드 1(기존과 동일). `runtime_closure_verified`, `host_compatibility_verified`, `installation_ready` 모두 false.
- 기존 원본·설치본·main·원격 push·모델/Bot/Orca 실호출·결제 설정 변경 없음. 추가 과금 $0.

## Links

- 설치·검증 범위: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`.
- 남은 결정: Core helper 패키징 §35 별도 심판/D-code, SimonKMarket 원본 4자산 별도 브랜치 승인. 둘 다 해결 전 설치/머지 게이트 유지.
