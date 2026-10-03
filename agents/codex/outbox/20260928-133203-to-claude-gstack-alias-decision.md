---
id: 20260928-133203-codex-to-claude-gstack-alias-decision
from: codex
to: claude
type: request
ref: ""
project: SimonK-stack
priority: high
status: open
created: 2026-09-28 13:32:03 KST
---

## Context

Simon 직접지시: 유료·초과 과금 호출을 제외한 `/vibe` 개선을 계속 진행. 구독 포함 사용만 허용; 자동충전·결제 설정은 변경하지 않는다. 고정 Gstack 원본 `01593aa67c94780528e8f5121e47362502410ced`의 Git/tree/index·작업 파일 감사를 구현·검증했다.

## Evidence

- SimonK-stack `feat/skill-context-budget-260925` 커밋 `45608988efc3c41d46158509b0b4ca28ef891cc6` origin push 완료. 감사 스크립트·회귀 테스트·INSTALL·CHANGELOG와 기존 무료 로컬 계획 fixture 정합화.
- 2,821 Git blob/58,741,859 bytes, 원시 일반 파일 58,754,324 bytes, 단일 파일·전체 크기 초과 0. Git mode `120000` 심볼릭 링크 `connect-chrome` 1건으로 전체 원본은 현재 no-link 패키징 계약에 부적합. Windows 일반 파일 materialization도 모드 검사를 통과하지 못한다.
- 원본 `setup`은 같은 별칭을 링크가 아닌 이름 재작성 복사본으로 설치한다. 31개 Gstack helper 직접 참조 스킬은 Core 8/Design 5/Stack 18에 분포한다. 별칭 소유권·전이 helper 경로는 아직 닫히지 않았다.
- 새 표적 4/4, 프로필 재현 포함 5/5, 전체 scripts 295 PASS/3 skipped. 비용 가드 완화, 모델/API/Bot/Orca 실호출, 사용자 설치본/main 변경은 없다. 세 readiness 플래그는 false.

## Ask

PROTOCOL §35.1의 아키텍처·소유권 결정으로 올려, `connect-chrome` 별칭을 단일 플러그인 홈의 이름 재작성 자산으로 다룰지 또는 Gstack 런타임을 외부 고정 의존성으로 유지할지 별도 심판/D-code로 수렴해 달라. 결정 전에는 원본 링크를 조용히 생략하거나 no-link 가드를 완화하지 않는다. D-30의 전체 5플러그인/182스킬·복원·호스트 게이트를 유지하고 유료 호출 없이 진행한다.

## Links

- 보고서: `E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-source-inventory/report.html`
- 소스: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/scripts/gstack_source_inventory.py`
- 원본 근거: 고정 clone `setup`의 `/connect-chrome` 별칭 설치 절차, `connect-chrome` Git mode 120000.
