---
id: 20260729-192654-codex-re-deepspace-northstar-faq
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-29 19:26:54 KST
---

# 딥스페이스 도움말 북극성 명칭 정렬

새 Codex inbox 요청과 직전 사이클 이후 새 peer outbox OPEN 요청은 없었습니다. Codex 레인 자율 작업으로 `origin/main` 기반 worktree `E:\2ndB\.worktrees\codex-cycle-20260729-192309-northstar-residue-next`에서 딥스페이스 도움말 FAQ의 폐기 명칭 병기를 정리했습니다.

- 2nd-B 브랜치: `codex/cycle-20260729-192309-northstar-residue-next`
- 2nd-B 커밋: `676c796d` (`fix(i18n): align deep space north star faq`)
- 변경 파일: `locales/en/deepspace.json`, `locales/ko/deepspace.json`, `locales/es/deepspace.json`, `locales/pt/deepspace.json`, `locales/id/deepspace.json`
- 변경 내용: `North Star (Soul Core)` 계열 FAQ 질문을 각 locale의 North Star/북극성 단독 명칭으로 정렬
- 검증: JSON parse, 대상 잔여 검색, `git diff --check`, `npm run check:i18n`, `npm run check:lexicon`, `npm run check:emdash`, `npm run type-check`, `npm run verify` 통과
- §35 자체 패널: locale 문구 5줄 변경으로 저위험, cross-verify 요청 불필요
- 금지 동작: push, PR, merge, deploy, 비용/시크릿/파괴 작업 없음

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260729-192654-deepspace-northstar-faq.html`
