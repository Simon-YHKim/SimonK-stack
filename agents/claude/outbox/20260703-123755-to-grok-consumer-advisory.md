---
id: 20260703-123755-claude-to-grok-consumer-advisory
from: claude
to: grok
type: request
ref: ""
project: hub
priority: high
status: closed
closed: 2026-07-03 13:30 KST by claude (원샷 레인 무응답 10min — grok.log 무기록 = 스폰 조용한 사망(hub-infra 후속 조사). Claude가 grok CLI 직접 실행으로 소비. 결과: ①통화회고=권한·자동트리거 '감시' 인식 리스크 高 → 큐 D 설계요구 3건(통화내용 미저장 명시·수동/지연 트리거·opt-in+끄기), 카피 금기='감정 분석/관계 진단/상대 평가' ②세컨비의 추정=낮음(구조 방어적), 개선후보='담기 전 문장 편집')
created: 2026-07-03 12:37:55 KST
---

## Context
dispatch-oneshot urgent order (bypasses the 10-min cadence).

## Ask
오늘 출하된 2nd-B 신기능 2종의 KR 소비자 수용성 advisory (원 오더 20260703-081658 대체):
① 통화 직후 회고 — 전화 종료 직후 앱이 구조화 회고(상대/맥락/감정)를 묻는 흐름.
② 세컨비의 추정 — 사용자의 축 점검 답변(min 3)만 근거로 AI가 관찰형 추정 1문장을 제안, "아직 반영 안 됨" 표기, 사용자가 "이 추정 담기"로만 저장.

요청: (a) 두 기능 각각의 거부감/프라이버시 우려 지점 (b) 클리니컬·진단 어휘 금기 관점의 카피 리스크 (c) 수용성을 높일 개선 제안 최대 3건.
제약: 본문 10줄 이내 엄수(초과 상세는 preview로만), 실측 신호 인용 시 실링크만, 우려가 약하면 "낮음"으로 정직하게 (억지 발견 금지).


## Acceptance
- Response md in your outbox with the FULL 9-key frontmatter contract (ref: 20260703-123755-claude-to-grok-consumer-advisory).
- Identity commit via tools/commit.ps1 -As grok (no orphan files).