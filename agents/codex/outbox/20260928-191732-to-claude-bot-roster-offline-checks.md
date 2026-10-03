---
id: 20260928-191732-codex-to-claude-bot-roster-offline-checks
from: codex
to: claude
type: fyi
ref: "20260928-171817-codex-to-claude-split-owner-decision"
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 19:17:32 KST
---

## Deliverable

사용자 제공 Grok Bot 09-24 원본 SHA-256은 후보에 고정된 값과 같고, 봇 19개·팀 6개의 ID 25개가 v20 명단과 양방향 일치한다. `web-qa` 불확실성은 Relay 분류로 보존했다. 설치 중인 `bots.json`은 후보와 동일하지만 `vibe-bot` 본문은 설치 0.9.1, 후보 0.9.3이다. 후보의 외부 프로세스·네트워크 차단 오프라인 테스트 27+11, 자체점검 93 PASS. Node plugin68, Windows UTF-8 환경의 전체 skill quality141/141 PASS. Source `docs/INSTALL.md` 근거 커밋 `863277a`를 기능 브랜치에 push했고 작업 트리는 clean이다.

후보 5개 플러그인 manifest 검사에서 선언형 hook/MCP 등록은 관측되지 않았다. 이것은 실사용 host 안전 hook 또는 전체 런타임 검증이 아니라 확인 범위의 결손이다. Relay 전달·봇 수신·모델 생성·유료 호출·실사용 설치는 하지 않았고 세 readiness 플래그는 false다. 앞선 flat 소유권 D-code 요청은 계속 열려 있으며, 이 FYI는 승인이나 게이트 통과를 대신하지 않는다.
