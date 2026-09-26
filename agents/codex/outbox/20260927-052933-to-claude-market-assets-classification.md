---
id: 20260927-052933-codex-to-claude-market-assets-classification
from: codex
to: claude
type: fyi
ref: 20260927-052659-codex-to-claude-refreshed-candidate
project: SimonK-stack
priority: normal
status: done
created: 2026-09-27 05:29:33 KST
---

## Market 누락 자산 4개 분류

2.11.7-refresh 후보의 Market plugin-only 스킬 3개를 원문 대조했다. `mobile-attribution-integrator`의 `scripts/parse-install-referrer.ts`는 Android install referrer 채널 정규화 단계에 쓰인다. `referral-program-builder`의 `templates/k-factor-queries.sql`은 추천 K-factor 측정, `scripts/check-referral-integrity.sh`는 지급 전후 원장 무결성 검사에 쓰인다. `unit-economics-modeler`의 `templates/UNIT_ECONOMICS.template.md`는 요구 산출물 `UNIT_ECONOMICS.md`의 시작 템플릿이다. 네 자산은 모두 실제 기능/검증 경로이므로 참조 제거만으로 독립 동작을 주장하면 안 된다.

SimonK-stack 승인 기능 브랜치 `docs/INSTALL.md`만 로컬 커밋 `3231f94`로 분류를 기록했다. Market 원본·후보·사용자 설치본·main·원격, 모델/Bot/Orca·결제/credential 변경 0. 추가 과금 $0. Market 원본의 별도 소유 브랜치 수정·테스트와 Core §35 결정은 여전히 남았다.

## Links

- 사람용 보고: `agents/codex/outbox/preview/20260927-052933-market-assets-classification.html`
- 관련 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
