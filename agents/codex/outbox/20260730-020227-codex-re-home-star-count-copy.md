---
id: 20260730-020227-codex-re-home-star-count-copy
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-30 02:02:37 KST
---

# Codex cycle: home star count copy

이번 PROTOCOL 12/19/35.4 단일 사이클에서 새 Codex inbox 주문은 없었고, peer outbox의 Codex/all OPEN 후보도 stale 또는 이미 응답된 항목뿐이었다. 그래서 BOARD.md의 codex 레인인 UI/anti-slop 기준으로 2026-07-29 홈 밝기 결정 이후 남은 사용자 문구 불일치 하나를 처리했다.

2nd-B `origin/main` `353ca866`에서 별도 worktree `E:\2ndB\.worktrees\codex-cycle-20260730-015811-polish-scan`와 브랜치 `codex/cycle-20260730-015811-polish-scan`를 만들었다. `locales/en/home.json`, `locales/ko/home.json`, `locales/es/home.json`, `locales/pt/home.json`, `locales/id/home.json`의 홈/북극성 패널 카피를 조정해, 홈은 보이는 6개 도메인 별과 Museum portal을 안내하고 북극성은 7개 도메인 종합으로 설명하도록 분리했다.

2nd-B 로컬 커밋: `27ea451c` (`fix(i18n): align home star count copy`). push, PR, merge, 배포, 비용 발생, secrets 작업, 브라우저 자동 열기는 하지 않았다.

검증:

- `JSON.parse` for five edited locale files: PASS
- `npm run check:i18n`: PASS
- `npm run check:lexicon`: PASS
- `npm run check:emdash`: PASS
- `git diff --check`: PASS
- `npm run type-check`: PASS
- `npm run verify`: PASS, 기존 lint warning 57개와 테스트 console warning만 있음

Section 35 self-panel:

- 사용자 가치: 홈에 실제로 보이는 별 개수와 북극성 종합 설명을 분리해 최근 Simon 결정과 화면 안내를 맞춤.
- 범위: locale 5개 파일의 17줄 교체로 제한.
- 위험: schema, 보안, 네이티브, 수익화, 외부 사실 주장 없음. MoA 추가 검증 불필요.

## Links

- HTML report: `agents/codex/outbox/preview/20260730-020227-home-star-count-copy.html`
- 2nd-B worktree: `E:\2ndB\.worktrees\codex-cycle-20260730-015811-polish-scan`
- 2nd-B local commit: `27ea451c`
