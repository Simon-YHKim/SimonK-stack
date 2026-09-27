---
id: 20260927-131652-codex-to-claude-market-asset-candidate
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-27 13:16:52 KST
---

# SimonKMarket 누락 자산 복구와 v2 후보

## Deliverable

Simon 직접 승인으로 SimonKMarket 원본 `fix/market-missing-assets-260927`에서 누락 4자산을 구현했습니다. 파서·무결성 검사·K-factor SQL·단위경제성 템플릿과 해당 회귀·설명 수정은 `4b6d804`, `.gitattributes` 범위 수정은 `257c2cd`에 로컬 커밋했습니다. 원본 `main`과 설치본은 그대로입니다.

SimonK-stack `feat/skill-context-budget-260925`는 Market commit `257c2cd`를 정확히 핀했고 설치 문서를 `183791c`로 로컬 커밋했습니다. 안전 v2 후보 `candidate-safety-v2/` digest `8d7ea761ac6de6e3a54fbb7d198087cc91e1ed6f861057b924c7e54d1958cb1c`는 5 plugin·182 skill·720 file입니다. 같은 폴더의 `candidate/`는 v1 비교용이며 v2 후속 후보가 아닙니다.

## Acceptance

- Market quality gate 32/32, Node 회귀 9/9, plugin bundle 회귀 43/43 PASS. 후보 source/bundle byte verify PASS.
- 정적 경로 감사 미해결 11→7; AIHub1/Core6이 남아 `incomplete`입니다. PostgreSQL 실DB 실행은 하지 않았습니다.
- 격리 Codex 호스트에서 전역 스킬 중복/예산 영향: Core 후보61 중 프롬프트 가시27, `vibe`는 옛 전역 경로. 일괄 비활성화는 전역 전용 스킬을 잃으므로 하지 않았습니다.
- readiness 3 flag 모두 false. 사용자 프로필 설치, main merge, push, 모델/Bot/Orca 호출, 결제 설정 변경 없음. 추가 과금 $0.

## Links

- 원본: `E:/Coding Infra/SimonK-Plugins/SimonKMarket` (`fix/market-missing-assets-260927`, HEAD `257c2cd`).
- 배포 작업: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md` (`183791c`).
- 후보: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.10-market-assets-candidate/candidate-safety-v2/`.
- 사람용 보고: `agents/codex/outbox/preview/20260927-131652-market-asset-candidate.html`.
- 남은 게이트: Core helper closure §35 D-code, AIHub 1/Core 6 정적 경로, 선택적 Codex 전역 스킬 이전·호스트 재검증. 설치·main 머지·push는 별도 게이트.
