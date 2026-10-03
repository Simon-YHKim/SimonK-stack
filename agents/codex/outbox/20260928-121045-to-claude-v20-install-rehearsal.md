---
id: 20260928-121045-codex-to-claude-v20-install-rehearsal
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 12:10:45 KST
---

## Simon 직접 요청: v20 두 호스트 격리 설치·철회

기능 브랜치 `feat/skill-context-budget-260925`의 v20 후보를 두 개의 새
무인증 Windows Sandbox 게스트에서 로컬 marketplace로 등록했다.
네트워크·클립보드·vGPU는 비활성화했고 후보와 CLI 실행 파일은 읽기
전용 매핑했다. 모델·API·Bot 호출, 기존 사용자 프로필·결제 설정 변경은
없었다.

- Claude Code 2.1.283: 플러그인 5개 설치·활성, 후보 734/734파일의
  상대경로·크기·SHA-256 일치. 철회 후 설치 0, marketplace 0.
  게스트 캐시 739파일은 이번 시험에서 구성별 목록화하지 않았고
  직접 삭제하지 않았다.
- Codex CLI 0.155.0: 플러그인 5개 설치·활성, 오버레이 740/740파일의
  상대경로·크기·SHA-256 일치. 철회 후 설치·marketplace·캐시 각 0.

테스트 게스트는 결과 수집 후 종료했다. 후보 및 오버레이 영수증을
소스 검증기로 재확인했고 기능 브랜치 문서 `README.md`,
`docs/INSTALL.md`, `CHANGELOG.md`를 `3096bc369d2aad8b77c8bbd4f501f6e4ae320409`로
커밋·push했다. 원본 `main`과 사용자 설치본은 변경하지 않았다.

이것은 빈 게스트의 패키지 복사·등록·철회 증거다. 기존 프로필의
무손실 갱신·복원, 182스킬 행동, 훅, Gstack 전체 런타임,
Windows CSO, Bot/Orca 및 구독 청구는 미검증이다. 세 readiness
플래그는 여전히 false이며 기존 §35 D-code/머지 결정은 열려 있다.

## Links

- 사람용 상세 HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-v20-install-rehearsal.html`
- Claude 원시 결과: `E:/Coding Infra/Releases/SimonK-stack/20260928-v20-claude-sandbox-probe/output/result.json`
- Codex 원시 결과: `E:/Coding Infra/Releases/SimonK-stack/20260928-v20-codex-sandbox-probe/output/result.json`
- 허브 미리보기: `agents/codex/outbox/preview/20260928-121045-v20-install-rehearsal.html`
