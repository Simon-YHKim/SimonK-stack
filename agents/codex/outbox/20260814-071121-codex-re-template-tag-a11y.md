---
id: 20260814-071121-codex-re-template-tag-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-14 07:11:21 KST
---

## Deliverable

새 open request는 없어서 Codex 레인 자율 작업으로 2nd-B 템플릿 편집기의 태그 추가 버튼 접근성을 한 건 개선했습니다.

- worktree: `C:\2ndB\.worktrees\codex-qa-20260814-070829`
- branch: `codex/qa-cycle-20260814-070829`
- base: `origin/main 5ba0cdd905ec3e9e2d5aac0fceb17830c556ab09`
- local commit: `bebe377091823719cda8c12159841fc3403e0534`
- changed: `src/components/wiki/TemplateEditor.tsx`
- test: `src/lib/wiki/__tests__/template-editor-a11y.test.ts`

태그 입력이 비어 있거나 중복이거나 12개 상한에 도달한 경우 inline add 버튼이 실제 `disabled` 상태와 `accessibilityState.disabled`를 노출하도록 했습니다.

## Verification

- `npm test -- --runTestsByPath src/lib/wiki/__tests__/template-editor-a11y.test.ts --ci`
- `npx prettier --check src/components/wiki/TemplateEditor.tsx src/lib/wiki/__tests__/template-editor-a11y.test.ts`
- `npx eslint src/components/wiki/TemplateEditor.tsx src/lib/wiki/__tests__/template-editor-a11y.test.ts`
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:i18n-untranslated`
- `npm run check:lexicon`
- `npm run check:constraints`
- `npm run check:emdash`
- `npm run check:anti-anthro`
- `npm run check:mascot-voice`
- `npm run check:cycles`
- `git diff --check`
- changed diff sensitive-pattern scan

## Links

- HTML report: `agents/codex/outbox/preview/20260814-071121-template-tag-a11y.html`
