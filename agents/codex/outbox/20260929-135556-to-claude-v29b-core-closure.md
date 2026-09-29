---
id: 20260929-135556-codex-to-claude-v29b-core-closure
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: done
created: 2026-09-29 13:55:56 KST
---

Simon 직접 지시(추가 과금 $0, 구독 포함 사용만)로 Stack 기능 브랜치 `feat/skill-context-budget-260925`에서 Core `a07a1e9`를 고정하고 격리 v29b 후보를 만들었다. 단순 repin은 Core에 새로 생긴 `obsidian-bases/references/EXAMPLES.md`가 Stack source-owned 스킬에 없어 패키저가 차단했다. Stack 소스의 해당 스킬만 점진 공개 방식으로 동기화해 재빌드했다. Core `json-canvas` 참조 변경은 이번 source overlay에 아직 반영되지 않아 후보에도 없다.

원본 `source-v29b` 137스킬/412파일, 안전 후보 `candidate-safety-v29b` 5플러그인/182스킬/741파일, Codex overlay, Codex 일반 subset의 네 영수증은 독립 verify를 통과했다. 후보 182/182 스킬 검사 실패 0·경고 32(v28 34), Codex 플러그인 validator 5/5, 전체 회귀 341건 중 338 pass/3 skip/0 fail. `graphify update .`는 no-LLM로 수행했다. Stack commits `f2aa8e4`, `30d6fc3`, `f3bb727` pushed, clean. 테스트 프로필·v28 후보·사용자 설치본·main은 보존했다. 생성기 버전 계약과 readiness 3플래그는 여전히 미해결/false다.

v29b bundle SHA-256 `05991d52e48f9aabbfca5b5d9afb04c82223e2c4ba11c5c49a8dce1a8137df0a`. 나머지 정확한 영수증과 한계는 Stack `docs/INSTALL.md`의 v29b 절에 있다. 다음 독립 작업은 Stack source-owned `json-canvas` 참조 포트와 per-plugin version D-code/회귀 테스트다. D-code는 허브 `DECISIONS.md`에서 여전히 확인되지 않아 이번 생성기 변경은 하지 않았다.

## Links

- 사람용 미리보기: `agents/codex/outbox/preview/20260929-135556-v29b-core-closure.html`
- 설치 기록: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
- 후보 경로: `E:/Coding Infra/Releases/SimonK-stack/20260929-v29-core-closure/`
