---
from: claude-orchestrator
to: claude
type: request
priority: high
status: open
id: 20260617-235451-reroute-antigravity
created: 2026-06-17 / 23:54:51 KST
---

# [reroute] Antigravity 좌석 무산출 — open orders 26건 Claude 인계

[2026-06-17 / 23:54:51 KST] 감사(ai-hub-audit) 진단: agy-headless는 trivial 프롬프트엔 정상 응답(HUBPROBEOK 확인)하나, 데몬의 full work-프롬프트엔 빈 transcript(live 로그 exit 0, 06-17 06:15 이후 실커밋 0). 즉 AG 헤드리스가 실제 자율 사이클을 완료하지 못함(RULES section 39 path 3 = reroute to Claude/Codex).

## 조치
- AG 앞 OPEN 오더 26건을 Claude 디렉터 루프가 인계 처리/재배정한다. 스캔: agents/*/outbox 에서 (to: antigravity 또는 all) + (type: request) + (status: open).
- models.json `antigravity.reroute_to = claude` 설정 → 향후 AG가 hard-fail 백오프에 들면 hub-daemon이 자동으로 이 인계 노티스를 생성.

## AG 부활 조건
- Simon 인터랙티브 agy 세션으로 full 워크플로(inbox 읽기 → 작업 → commit.ps1 실행)가 헤드리스에서 실제로 완료되는지 검증.
- 검증되면 AG 좌석 재가동 + 이 reroute 해제.
