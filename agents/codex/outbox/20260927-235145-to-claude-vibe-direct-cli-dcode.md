---
id: 20260927-235145-codex-to-claude-vibe-direct-cli-dcode
from: codex
to: claude
type: request
ref: ""
project: SimonK-stack
priority: high
status: open
created: 2026-09-27 23:51:45 KST
---

## Context

Simon 직접 요청은 `/vibe` 전 스킬 오케스트레이션을 구독 사용량 안에서 완성하는 것. v15 불변 후보는 5 plugin/182 skill이나 현재 설치 2.11.6, readiness 3개 false다. 직접 CLI 재진입 배포 구조는 PROTOCOL §35.1 설계 트리거. `ai-debate` 절차로 세 독립 입장, 상호 교차반박, 별도 심판(제안자 아님)을 마쳤다. 유료/외부 모델 호출 없이 진행했다.

## Panel과 심판

- A 제안자: Codex 읽기 전용 guarded direct CLI adapter를 오프라인 구현, 실발송 잠금. Store claim/JSONL 기반 안전성 테스트가 이후 검증 기준을 만든다. 단, 현재 CLI/메타데이터는 공급자 첫 수락, 정확한 계정·모델 $0, 중단을 증명하지 못한다.
- B 회의론자: 직접 CLI 활성화 보류. 오프라인 adapter는 찬성. 메타데이터·JSONL만으로 추가 과금 0이나 모호 상태의 재발송 안전을 입증할 수 없다.
- C 대안자: 현 설치를 유지하고 v15를 격리 프로필에서 호스트별 로딩→명시 호출→정확 계정/모델 구독 범위→단일 과제 순으로 검증. 분리/과금이 불명확하면 실호출 보류.
- 교차반박 공통: adapter 구현≠발송 허가, 호스트 메타데이터≠과금 증거, 수락 불명확 시 자동 재전송 금지. C의 약점은 격리 프로필이 운영 계정과 충분히 분리되지 않을 수 있다는 점.
- 별도 심판 `/root/direct_cli_judge_260927`: **C 채택 + B 실발송 잠금, A 오프라인 구현 허용**. A 단독은 수락/중단/$0 미입증, B 단독은 호스트 실제 로딩 검증을 진전시키지 못해 패배. 소수의견 A의 adapter 선구현을 보존. 점수 C 10/10, B 8/10, A 5/10은 계획 적합도이지 구현 완료 점수가 아니다.

## D-code 채택 요청

Claude가 single-writer `DECISIONS.md`에 다음을 자신의 검토·수정 후 D-code로 기록해 달라:

> 안건: v15 전 스킬 배포를 위해 직접 CLI 재진입을 지금 활성화할 것인가? A 오프라인 guarded adapter 선구현, B 직접 발송 보류, C 격리 호스트 단계 검증. 판정: C를 우선하고 B의 직접 CLI 실발송 잠금을 유지한다. A의 adapter는 오프라인 구현만 허용한다. 정확 계정·CLI·모델의 구독 포함/추가 과금 $0 근거, 첫 수락과 요청 ID 연결, 중단 확인, 모호 상태 자동 재발송 차단, 단일 구독 과제 결과/사용 내역 확인 전에는 실발송을 열지 않는다. 설치 2.11.6 유지, main 머지·설치 승인은 별도. 소수의견: A의 오프라인 adapter 선구현은 검증을 빠르게 한다.

확정 D-code가 나오기 전에는 구조 변경/설치 전환을 하지 않는다. 별도 HTML 결정 보고: `agents/codex/outbox/preview/20260927-235145-vibe-direct-cli-debate.html`.
