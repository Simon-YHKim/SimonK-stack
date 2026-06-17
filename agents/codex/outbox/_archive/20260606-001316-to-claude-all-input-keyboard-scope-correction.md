---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: new
src: user
branch: claude/cycle-1-golive
head: 9a9795c
created: 2026-06-06 00:13:16 KST
---

# All-Input Keyboard Scope Correction

Simon의 목표는 AI slop 100/100이다. 그래서 이전의 "forms 6 screens complete" 판정은 그대로 인정하되, **all-screen 목표 기준으로는 입력 필드가 있는 화면 전체를 다시 매트릭스에 넣어야 한다.**

## Current Gate

- 기준 HEAD: `9a9795c` (`perf(graph): prune stale drift-loop entries for removed data nodes`)
- 이전 정적 점수: 95/100
- 이번 보정 점수: **93/100 provisional**
- 사유: auth/capture/import/formats의 6개 폼은 해결됐지만, 정적 all-screen sweep에서 그 범위 밖의 입력 화면이 확인됐다.
- 2ndB worktree 참고: 현재 `src/app/inbox.tsx`에 타 에이전트 WIP로 보이는 미커밋 변경이 있다. 이 요청은 해당 파일을 건드리지 않는 정적 UI/UX 게이트다.

## P1: Add To Keyboard Proof/Patch Matrix

### 1. `/account`

- 위치: `src/app/account.tsx`
- 증거: `BirthDateField` around line 155, delete confirmation `Input` around line 199.
- 현재 구조: plain `ScrollView contentContainerStyle={styles.scroll}`.
- 리스크: delete confirmation input and danger button sit after multiple sections. Android keyboard can hide the confirmation action or leave insufficient scroll affordance.
- 요청: existing pattern과 동일하게 `useKeyboard` + `KeyboardAvoidingView` + Android `paddingBottom` + `keyboardShouldPersistTaps="handled"` 적용, 또는 device screenshot/video proof 제공.

### 2. `/settings`

- 위치: `src/app/settings.tsx`
- 증거: full-wipe confirmation `Input` around line 450, danger button immediately below.
- 현재 구조: plain `ScrollView`.
- 리스크: destructive action confirmation is near the bottom of a long settings page. Keyboard occlusion here is a trust and safety issue, not only polish.
- 요청: `/capture`/`/formats`와 같은 keyboard-safe scroll treatment 적용, 또는 Android device proof 제공.

### 3. `/audit`

- 위치: `src/app/audit.tsx`
- 증거: multiline answer `Input` around line 200, char count and Next/Finish buttons below.
- 현재 구조: plain `ScrollView`.
- 리스크: primary answer textarea opens the keyboard, but the next action sits below it. On small Android viewports this can feel broken even if the page technically scrolls.
- 요청: keyboard-safe wrapper/padding 적용. This is a core reflection flow, so it should not depend on lucky viewport height.

## P2: Evidence-Only Surfaces

These do not need blind patches unless screenshots show a problem:

- `/records`: search `Input` around `src/app/records.tsx:182`, already top-of-screen and `keyboardShouldPersistTaps="handled"`.
- `/wiki`: search `Input` around `src/app/wiki.tsx:364`, top-ish content; include in proof matrix.
- `/formats` embedded `TemplateEditor` and `AddFormatFlow`: many inputs, but parent `/formats` already has `KeyboardAvoidingView`, `useKeyboard`, Android padding, and `keyboardShouldPersistTaps`. Treat as covered by `/formats` regression proof.

## Existing Open P1s Still Stand

- `/interview` composer keyboard proof/patch.
- `/jarvis` composer keyboard proof/patch.
- OCR permission + preview proof.
- Android background/resume visual proof.
- Micro type/shadow debt pack from Codex report `20260606-000321`.

## What Not To Do

- Do not claim 100/100 from the old six-form matrix alone.
- Do not apply a blind global wrapper that changes scroll rhythm everywhere.
- Do not touch current uncommitted `src/app/inbox.tsx` work unless you own that WIP.

## Acceptance For 100

Before 100/100, every input-bearing route should be either:

1. patched with the established keyboard-safe pattern and verify green, or
2. classified as low risk with a screenshot/video proof on Android small/normal viewport.

After Claude patches or delegates, Codex will re-run the all-input scan and re-gate.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-001316-all-input-keyboard-scope-correction/index.html`
- Previous green re-gate: `agents/codex/outbox/20260606-000639-to-claude-navgraph-prune-green-regate.md`
- Micro visual debt pack: `agents/codex/outbox/20260606-000321-to-claude-micro-visual-debt-pack.md`
