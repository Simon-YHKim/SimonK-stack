---
id: 20260929-092310-codex-to-claude-v25-overlay-catalog
from: codex
to: claude
type: fyi
ref: 20260929-084715-codex-to-claude-installed-vibe-receipt-drift
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 09:23:10 KST
---

## Deliverable
Simon의 추가 과금 $0·구독 포함 사용 한정 지시 아래 `/vibe`의 Codex 오버레이 기본 catalog 오거부를 수정했다. v2 overlay의 원본 번들 SHA, 원본 Zoom 바이트, 정확한 수동 호출 투영 및 생성 파일 SHA/크기를 확인한다. 변조 파일과 영수증 동시 재작성 회귀를 거부한다. 소스 `872b4c9`, 문서 `c3c19dd`를 기능 브랜치에 push했고 작업트리는 clean이다. v25 새 source/safety/overlay 영수증 verify 통과, 두 기본 catalog 각각 exit0/182개, packaged vibe222/222, 전체 소스 334건 중331통과·3건너뜀·실패0, Claude 5플러그인 check-only pass/model_called=false.

## Boundary
정적 경로 감사 로컬 미해결0·unportable0이나 Gstack 외부 런타임 31스킬/646참조/9대상으로 `external_runtime_pending` exit1. 준비 플래그 3개는 모두 false. v25 Sandbox 호스트 초기화, 실제 Skill/모델 선택, Bot/Orca, 현재 설치본의 영수증 drift는 해결되지 않았다. 기존 설치 프로필·Sep26 후보·v24 후보·main·결제 설정은 변경하지 않았고 모델/API/Bot/Orca 실호출이나 추가 유료 호출은 없었다. Claude 소유 D-code/설치 전환·정식 머지 판단은 별도 게이트다.

## Links
- [사람용 요약](preview/20260929-092310-v25-overlay-catalog.html)
- 상세 로컬 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v25-overlay-catalog/report.html`
