---
id: 20260927-065123-codex-vibe-21110-body-budget
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-27 06:51:23 KST
---

# `/vibe` 2.11.10 본문 예산 후보

## Deliverable

SimonK-stack 기능 브랜치 `feat/skill-context-budget-260925`의 로컬 커밋 `1d13d8e`에서 `/vibe` SKILL.md의 역사적 버전 기록을 제거했습니다. 실행 규칙·생성된 라우팅 표는 유지했고, 자세한 이력은 Git 및 `docs/INSTALL.md`에서 추적 가능합니다. `a8c3d87`에 한계와 후보 검증 기록을 남겼습니다. 스킬 검증기 기준 본문 416→362줄, 파일 32,900→28,707바이트이며 W007 경고가 source·패키지 모두 0건입니다.

새 후보: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.10-body-budget-candidate/`. source digest `ab7db4645c420f804684083672b108ec4e6e2d91449f33425a3cd267a415e6c0`; bundle digest `1a3963396749266759a1ee36b64d07fea5a5eb548d1a3b5cf3465db55ab89411`. 이전 2.11.9 후보의 고정 입력 `inputs/`가 깨끗하고 핀과 일치함을 확인한 뒤 재사용했습니다.

## Acceptance

- 스킬 검증 source/패키지 0오류·0경고, 라우팅 표 동기 PASS.
- `/vibe` 87, 모델 라우터 8, 준비 절차 90 테스트 PASS.
- source 137스킬/407파일, bundle 5플러그인/182스킬/713파일 build·별도 verify PASS.
- 정적 경로 감사 150참조 중 미해결 11건, 종료 코드 1; readiness 세 플래그 false.
- description 축약 경고, 실제 토큰 사용량, 자동 스킬 선택 정확도 개선은 측정하지 않았고 주장하지 않습니다. 실사용 설치·main/원격·결제 설정·모델/Bot/Orca 호출 없음, 추가 과금 $0.

## Links

- 설치 검증 기록: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`.
- 사람용 요약: `agents/codex/outbox/preview/20260927-065123-vibe-21110-body-budget.html`.
- 남은 게이트: Core helper 패키징 §35 심판/D-code, Market 원본 4자산 별도 브랜치 승인, 후보 경로 11건 검토.
