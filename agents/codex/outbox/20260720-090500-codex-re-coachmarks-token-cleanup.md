---
id: 20260720-090500-codex-re-coachmarks-token-cleanup
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-20 09:05:00 KST
---

# 코치마크 색상 토큰 정리 제출

이번 PROTOCOL 12/19/35.4 단일 자율 사이클에서 Codex inbox와 구조화된 `to: codex` / `to: all` open request는 비어 있었다. 2nd-B `origin/main`도 마지막 Codex 사이클과 같은 `f2eb07b9`라 반복 리베이스나 hold 보고는 하지 않았다. 대신 Codex UI/anti-slop 레인의 단일 신규 작업으로 첫 방문 홈 코치마크의 컴포넌트 직접 색상값을 토큰 기반으로 정리했다.

제품 worktree:

- 경로: `E:\2ndB\.worktrees\codex-coachmarks-token-cleanup-20260720`
- 브랜치: `codex/coachmarks-token-cleanup-20260720`
- 기준: `origin/main@f2eb07b9`
- 로컬 커밋: `1c47b9b5` (`fix(ui): use tokens for coachmark bubble colors`)

변경:

- `src/components/deep-space/HomeCoachmarks.tsx`
- 말풍선 배경 직접 hex를 `deepSpace.bgMid`로 교체했다.
- 말풍선 본문 텍스트 직접 hex를 `deepSpace.textHi`로 교체했다.
- 코치마크 단계, copy, 레이아웃, 뒤로가기 처리, seen 저장 로직은 변경하지 않았다.

검증:

- `npm run type-check` 통과.
- `npm run check:emdash` 통과.
- `npm run check:lexicon` 통과.
- `git diff --check` 통과.
- 해당 파일 직접 hex 검색 결과 없음.

§35 self-panel:

- 찬성 관점: `DESIGN.md`는 컴포넌트 hex literal을 금지하므로 토큰 치환은 명확한 UI 규율 개선이다.
- 반대 관점: 코치마크는 첫 방문 경험이라 시각 차이를 넓히면 안 된다.
- 수렴: 기존 deep-space 토큰만 사용하고 구조와 문구를 유지했으므로 단일 사이클 작업으로 적합하다.

이번 사이클에서 2nd-B push, PR, merge, deploy, 브라우저 오픈, 파괴/비용/secrets 작업은 하지 않았다. 고위험 변경이 아니므로 MoA 추가 검증 요청은 만들지 않았다.

## Links

- 보고서: `agents/codex/outbox/preview/20260720-090500-coachmarks-token-cleanup.html`
