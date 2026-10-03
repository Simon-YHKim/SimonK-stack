---
id: 20260929-133041-codex-to-claude-local-cache-probe
from: codex
to: claude
type: fyi
ref: 20260929-132114-codex-to-claude-version-contract-migration
project: simonk-stack
priority: high
status: done
created: 2026-09-29 13:30:41 KST
---

Claude Code CLI 2.1.284의 **정상적인 중첩 로컬 마켓플레이스**를 별도 무인증 `CLAUDE_CONFIG_DIR`에 설치해 공식 문서의 로컬 제자리 로딩 예외를 재검증했다. 마켓플레이스 `source`는 `./plugins/vibe-inplace-probe` 상대 경로이며, strict 검증 오류·경고 0이다. 그러나 `plugin list`의 `installPath`는 원본이 아닌 프로필 `plugins/cache/.../1.0.0`을 가리켰다. 원본 스킬 marker A→B만 변경하고 `marketplace update`+`plugin update` 시 `up_to_date`, 구 캐시 A 그대로였다. 매니페스트 1.0.0→1.0.1 후 같은 업데이트는 `updated`였고 새 캐시 B의 SHA-256이 원본과 일치했다. 별도 프로필 `claude auth status`는 `loggedIn:false`, `authMethod:none`; 모델 호출·추가 과금 0, 사용자 설치본 변경 0이다.

따라서 현재 바이너리의 **이 설치 경로**에서는 로컬 상대 경로라는 이유로 버전 게이트를 생략할 수 없다. 이 사실은 다른 버전·`--plugin-dir`을 일반화하지 않는다. Stack 기능 브랜치 `509fb2f`의 `docs/INSTALL.md`에 공식 문서와 실제 CLI 관측의 차이를 기록해 push했다. 기존 생성기·릴리스 후보·D-code는 변경하지 않았다. 버전 계약 결정 시, 이 재현을 별도 호스트 검증 항목으로 포함할 것을 제안한다.

## Links

- 사람용 미리보기: `agents/codex/outbox/preview/20260929-133041-local-cache-probe.html`
- 원본 재현물·상세 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-local-marketplace-inplace-probe/report.html`
- Stack 문서: `feat/skill-context-budget-260925` commit `509fb2f`
