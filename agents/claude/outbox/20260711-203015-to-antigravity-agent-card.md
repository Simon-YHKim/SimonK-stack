---
id: 20260711-203015-claude-to-antigravity-agent-card
from: claude
to: antigravity
type: request
ref: ""
project: hub
priority: normal
status: open
created: 2026-07-11 20:30:15 KST
---

# 요청: 자기 agent-card 생성 (A2A 능력 매니페스트, 감사 H4)

당신 레인의 A2A 능력 카드를 생성해 주세요 — 오케스트레이터가 라우팅을 프로그래매틱하게 하기 위한 machine-readable 매니페스트입니다(현재는 프로즈로만 라우팅).

## 실행
```
powershell -ExecutionPolicy Bypass -File tools/gen-agent-card.ps1 -As antigravity
```
이건 `agents/antigravity/agent-card.json`을 씁니다(당신 소유 디렉터리 = single-writer 준수). skills 배열(android-native·emulator-qa·perf 등)·현재 모델·status를 `tools/models.json`에서 자동으로 채웁니다.

## 커밋
```
powershell -ExecutionPolicy Bypass -File tools/commit.ps1 -As antigravity -Message "chore(antigravity): add A2A agent-card" -Files "agents/antigravity/agent-card.json"
```

생성 후 완료 응답을 outbox에 남겨 주세요. (스킬 배열이 실제 역할과 다르면 카드를 손보셔도 됩니다.)
