---
id: 20260728-192126-codex-re-home-northstar-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-28 19:21:26 KST
---

# 홈 북극성 접근성 라벨 정리

열린 Codex 대상 주문은 없어서, BOARD 현재 포커스와 Codex 레인에 맞춰 2nd-B UI/i18n anti-slop 작업 한 건만 수행했다.

## 결과

- 2nd-B worktree: `E:\2ndB\.worktrees\codex-cycle-20260728-1919-antislop`
- 브랜치: `codex/cycle-20260728-1919-antislop`
- 기준: `origin/main` `69b0c58f`
- 로컬 커밋: `5d618d2c` (`fix(i18n): rename home north star a11y`)
- 변경 파일: `locales/en/home.json`, `locales/ko/home.json`, `locales/es/home.json`, `locales/pt/home.json`, `locales/id/home.json`

## 변경 요약

홈 별자리의 `soulCore.a11y` 접근성 라벨에서 사용자 노출 레거시 명칭 `Soul Core/소울 코어`를 캐논 표현 `North Star/북극성` 계열로 교체했다. 화면 로직, 라우팅, 스키마, 결제, 안전 분류, 외부 호출은 변경하지 않았다.

## 검증

- `node -e JSON.parse(...)` 통과
- `npm run check:i18n` 통과
- `npm run check:lexicon` 통과
- `npm run check:emdash` 통과
- `npm run type-check` 통과
- `git diff --check` 통과, Windows 줄끝 경고만 표시

## §35 self-panel

- 필요성: 홈 접근성 낭독에서 폐기된 `Soul Core/소울 코어` 명칭이 남아 캐논 북극성 모델과 충돌했다.
- 범위: locale JSON 5개 파일의 접근성 라벨만 수정했다.
- 위험: 낮음. 사용자 가시 텍스트 중 screen reader 라벨만 바뀌며 데이터/네이티브/보안/수익화 영향이 없다.
- 검증 요청: 고위험 산출물이 아니므로 MoA cross-verify 요청 없음.

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260728-192126-home-northstar-a11y.html`
