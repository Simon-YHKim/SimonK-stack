---
id: 20260726-224048-codex-re-shell-nav-i18n
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-26 22:40:48 KST
---

# 셸 내비게이션 다국어 정리

열린 Codex 대상 요청이 없어 이번 사이클은 2nd-B UI anti-slop 레인 작업 하나를 수행했습니다.

- 2nd-B worktree: `E:\2ndB\.worktrees\codex-ui-audit-260726-2230`
- branch: `codex/ui-audit-260726-2230`
- base: `origin/main 6b02a9f9`
- commit: `43545a26`
- changed: `src/components/deepspace/shell/SbNavBar.tsx`

## Summary

`SbNavBar`의 하단 탭 라벨과 접근성 라벨에서 한국어 고정 문자열을 제거하고, 이미 존재하는 `home:ds.dock.*` 번역 키를 사용하도록 정리했습니다. 새 locale 키는 추가하지 않았습니다.

## Verification

- `npx eslint src/components/deepspace/shell/SbNavBar.tsx` pass
- `npm run check:i18n` pass
- `npm run type-check` pass
- `git diff --check` pass, CRLF warning only

## Section 35 Self-Panel

- 역할: Codex lane의 UI/i18n anti-slop 범위에 맞는 단일 파일 정리입니다.
- 제약: 2nd-B push, PR, merge, deploy, destructive, cost, secrets, browser-open action 없음.
- 판정: 기존 번역 키 재사용이라 회귀 범위가 작고, 이번 사이클의 단일 작업으로 적합합니다.

## Links

- [사이클 HTML 보고서](preview/20260726-224048-shell-nav-i18n.html)
