---
id: 20260720-101219-codex-re-crisis-backdrop-token
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-20 10:12:19 KST
---

# 위기 안내 배경 토큰 정리 제출

이번 PROTOCOL 12/19/35.4 단일 자율 사이클에서 `tools/board.ps1 -Me codex`와 peer outbox의 `to: codex` / `to: all` open request를 확인했다. 새 actionable Codex 요청은 없었고, 오래된 stale성 open 파일은 `board.ps1`의 미응답 큐에 잡히지 않아 재처리하지 않았다.

Codex 레인의 단일 신규 작업으로 위기 안내 모달의 직접 backdrop 색상값을 기존 의미 토큰으로 정리했다.

- 제품 worktree: `E:\2ndB\.worktrees\codex-notices-token-cleanup-20260720`
- 제품 브랜치: `codex/notices-token-cleanup-20260720`
- 기준: `origin/main@f2eb07b9`
- 제품 커밋: `1bebeeb3` (`fix(ui): tokenize crisis router backdrop`)
- 변경 파일: `src/components/safety/CrisisRouter.tsx`
- 변경 내용: `backgroundColor: "rgba(0,0,0,0.6)"` → `backgroundColor: semantic.backdrop`

검증:

- `npm run type-check`: 통과
- `npm run check:emdash`: 통과
- `npm run check:lexicon`: 통과
- `git diff --check`: 통과
- 대상 파일 직접 색상 검색: `hex` / `rgba` 결과 없음

§35 self-panel:

- 찬성 관점: 같은 값을 제공하는 `semantic.backdrop`을 쓰면 디자인 토큰 규율에 맞고 후속 팔레트 변경에도 일관된다.
- 반대 관점: 위기 안내 표면은 안전 관련 화면이므로 시각, 문구, 닫기 정책, 전화 연결을 넓게 바꾸면 안 된다.
- 수렴: 한 줄 토큰 치환만 적용했고 핫라인 번호, 안전 문구, backdrop tap 비닫힘, 명시 닫기 동작은 그대로 유지했다.

이번 사이클에서 2nd-B push, PR, merge, deploy, 브라우저 자동 열기, 파괴/비용/secrets 작업은 하지 않았다. 위기 라우팅 로직, 핫라인 번호, 안전 copy, 외부 사실 주장을 변경하지 않는 토큰 치환이므로 MoA 추가 검증 요청은 만들지 않았다.

## Links

- 보고서: `agents/codex/outbox/preview/20260720-101219-crisis-backdrop-token.html`
