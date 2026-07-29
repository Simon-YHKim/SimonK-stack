---
id: 20260728-210854-codex-re-index-domain-star-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-28 21:08:54 KST
---

# 홈 도메인 별 접근성 문구 정리

열린 codex 대상 주문은 없어서, BOARD 현재 포커스와 codex 레인에 맞춰 2nd-B UI/i18n anti-slop 작업 한 건만 수행했다.

- 2nd-B worktree: `E:\2ndB\.worktrees\codex-cycle-20260728-210738-index-domain-star`
- 브랜치: `codex/cycle-20260728-210738-index-domain-star`
- 기준: `origin/main 69b0c58f`
- 로컬 커밋: `4bec20c8` (`fix(i18n): rename index domain star a11y`)
- 변경 파일: `locales/en/index.json`, `locales/ko/index.json`, `locales/es/index.json`, `locales/pt/index.json`, `locales/id/index.json`, `src/lib/__tests__/worldview-naming.test.ts`

## 변경 요약

홈 화면에서 도메인 별 상세 진입에 쓰이는 `openPatternCore` 접근성 문구가 사용자에게 폐기된 `Pattern Core` 계층명을 노출하고 있었다. 데이터 키는 호환성을 위해 유지하고, EN/KO/ES/PT/ID 표시값만 현재 정본인 도메인 별 표현으로 정리했다. 같은 회귀가 다시 들어오지 않도록 `worldview-naming.test.ts`에 정적 가드를 추가했다.

## 검증

- JSON parse: pass
- `npm test -- --runTestsByPath src/lib/__tests__/worldview-naming.test.ts --runInBand`: pass
- `npm run check:i18n`: pass
- `npm run check:lexicon`: pass
- `npm run check:emdash`: pass
- `npm run type-check`: pass
- `git diff --check`: 기능 오류 없음. Windows 줄끝 경고만 확인.

## Section 35 self-panel

- 정본성: 홈의 7개 별은 hidden Pattern Core가 아니라 생활 도메인 별이라는 현재 모델에 맞췄다.
- 범위: locale 접근성 문구와 정적 테스트만 변경했다.
- 위험: 낮음. UI/i18n 라벨 정렬이며 스키마, 보안, 비용, 외부 사실, 네이티브 런타임을 건드리지 않았다.
- MoA: 고위험 산출물이 아니므로 별도 verify 요청 없음.

푸시, PR, 머지, 배포, 파괴적 작업, 비용 작업, 시크릿 처리, 브라우저 자동 열기는 하지 않았다.

## Links

- HTML report: `agents/codex/outbox/preview/20260728-210854-index-domain-star-a11y.html`
