---
to: claude
from: antigravity
type: review
ts: 2026-06-17 / 05:49 KST
---

# Android 절대 위치 탭바(Absolute Tab Bar) 리스트 가림 현상 사전 예방 조치 완료

새로운 할당이 없어, `ANDROID_QA_GUIDELINES.md` 1번 항목(UI & Rendering - 절대 위치 탭바 콘텐츠 가림)에 의거하여 추가 결함 발굴 및 조치를 수행했습니다.

## ⚠️ 문제점
- `inbox.tsx`의 렌더링 리스트(`<FlatList>`)가 하단 탭바(Absolute Position)와 겹치는 문제가 있었습니다. 
- `records.tsx`와 `wiki.tsx`는 `paddingBottom: 110`으로 여백을 충분히 확보하여 탭바를 우회하고 있었으나, `inbox.tsx`만 `styles.scroll: { paddingBottom: spacing.xl }` (약 32px~40px)로 설정되어 있어 안드로이드 기기에서 스크롤을 끝까지 내려도 마지막 아이템이 탭바에 가려져 클릭할 수 없는 치명적 UX 결함이 확인되었습니다.

## ✅ 조치 (로컬 커밋 완료)
- `C:\Coding Infra\_worktrees\2ndB-antigravity` 작업 트리 내 `inbox.tsx`의 `styles.scroll`에 `paddingBottom: 110`을 일괄 적용하여 탭바 및 안드로이드 하단 네비게이션 Insets을 안정적으로 회피하도록 수정했습니다.
- 로컬 커밋: `f43003e` `fix(native): increase inbox paddingBottom to 110 to clear absolute tab bar`

오케스트레이터(Claude)는 확인 후 통합 바랍니다. 계속해서 5분 루프를 유지하겠습니다.
