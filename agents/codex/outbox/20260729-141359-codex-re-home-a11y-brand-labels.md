---
id: 20260729-141359-codex-re-home-a11y-brand-labels
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-29 14:13:59 KST
---

## Context
Codex PROTOCOL 12/19/35.4 단일 poll cycle입니다. `tools/board.ps1 -Me codex` 기준 열린 Codex 요청은 없었고, peer outbox 스캔에서도 신규 actionable request는 없었습니다.

## Deliverable
최신 `origin/main` 기반 worktree `E:\2ndB\.worktrees\codex-cycle-20260729-141217-i18n-antislop`에서 홈 화면 접근성 라벨의 폐기 브랜드/세계관 용어를 정리했습니다.

- 브랜치: `codex/cycle-20260729-141217-i18n-antislop`
- 앱 커밋: `645be4ca` (`fix(i18n): align home accessibility brand labels`)
- 변경 파일: `locales/es/home.json`, `locales/pt/home.json`, `locales/id/home.json`
- 변경 요약: `Soul Core` 접근성 라벨을 각 로케일의 North Star 표현으로 맞추고, `Second Brain` 라벨을 `SecondB`로 정렬했습니다.

## Verification
- JSON 파싱: 통과
- 대상 파일 잔여 검색: `Soul Core`, `Second Brain` 없음
- `git diff --check`: 통과, Windows 줄끝 경고만 표시
- `npm run check:i18n`: 통과
- `npm run check:lexicon`: 통과
- `npm run check:emdash`: 통과
- `npm run type-check`: 통과

## Self-Panel
찬성: 홈 첫 화면의 접근성 음성이 현재 시각/세계관 명명과 달라지는 문제를 줄입니다.

반대: 전체 로케일 잔여를 계속 넓히면 반복 큐가 될 수 있어 이번 사이클은 같은 홈 a11y 블록으로 제한했습니다.

판정: 저위험 UI/i18n 수정입니다. MoA 고위험 검증 요청은 필요하지 않습니다. 2nd-B push, PR, merge, 배포, 파괴적 작업, 비용 작업, secrets 작업은 하지 않았습니다.

## Links
- HTML 보고서: `agents/codex/outbox/preview/20260729-141359-home-a11y-brand-labels.html`
