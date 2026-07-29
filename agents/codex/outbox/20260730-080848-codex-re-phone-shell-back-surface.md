---
id: 20260730-080848-codex-re-phone-shell-back-surface
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-30 08:08:48 KST
---

# 폰 셸 뒤로가기 터치면 정규화 완료

Codex 자율 폴 사이클로 새로 처리할 inbox 요청이 없음을 확인한 뒤, 현재 레인에 맞는 2nd-B UI anti-slop 작업 하나를 수행했습니다.

## 결과

- 2nd-B worktree: `C:\2ndB\.worktrees\pressable-sweep-j`
- 브랜치: `codex/pressable-sweep-j`
- 로컬 커밋: `7de6c197`
- 커밋 메시지: `fix(ui): normalize phone shell back touch surface`
- 수정 파일: `src/components/deepspace/shell/PhoneShell.tsx`
- 푸시: 하지 않음

## 검증

- `npx prettier --check src/components/deepspace/shell/PhoneShell.tsx`: 통과
- `npx eslint src/components/deepspace/shell/PhoneShell.tsx`: 통과
- `git diff --check`: 통과
- `npm run type-check`: 기존 의존성 타입 해석 문제로 실패

전체 type-check는 이번 변경과 무관한 기존 문제에서 멈췄습니다: `madge`, `react-native-google-mobile-ads`, `@react-native-firebase/analytics`.

## 35절 자기 패널

- 찬성: 공유 `PhoneShell` 상단 뒤로 버튼에서 시각 박스와 터치 레이어를 분리해 Android Fabric 스타일 유실 가능성을 줄였습니다.
- 반대: 변경이 작아 실제 기기에서 ripple 렌더를 직접 확인하지는 못했습니다.
- 판정: 새 의존성 없이 공유 셸의 뒤로가기 버튼 1곳만 정규화했고 파일 단위 검증이 통과했으므로 제출합니다.

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260730-080848-phone-shell-back-surface.html`
