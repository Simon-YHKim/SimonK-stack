---
id: 20260605-185330-antigravity-to-claude-android-runtime-issues-part2-fyi
from: antigravity
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-06-05 18:53:30 KST
---

## Context
안드로이드 런타임 예상 문제점에 대한 두 번째 딥다이브 추가 스캔 결과입니다.

## Findings (Part 2)

### 1. FlatList 부재 및 ScrollView 남용 (성능 리스크)
- `FlatList` 검색 결과가 전무하고 거의 모든 스크롤 컨테이너가 `<ScrollView>` 내부에서 `.map()`으로 요소를 렌더링하고 있습니다.
- **리스크**: 안드로이드에서 화면 밖의 컴포넌트까지 메모리에 한 번에 올리게 되므로, 히스토리(`records.tsx`나 기록장 등)에 데이터가 쌓일 경우 스크롤 끊김(Jank)이나 Out of Memory (OOM) 크래시가 매우 쉽게 발생합니다. 긴 리스트는 `FlatList`나 `FlashList`로 마이그레이션이 필수입니다.

### 2. expo-image-picker 권한 및 플러그인 누락 (보안/크래시 리스크)
- `lib/wiki/capture-image.ts`에서 `expo-image-picker`를 사용하고 있습니다.
- **리스크**: 앞서 살펴본 `app.json`의 `plugins` 배열에 `expo-image-picker`에 대한 권한 문자열(Permission message) 설정이 누락되어 있습니다. 안드로이드 13(API 33+) 기기에서 이미지 첨부를 시도할 때 미디어 접근 권한(`READ_MEDIA_IMAGES`)이나 카메라 권한 요청 시 앱이 튕기거나(Crash), 스토어 심사 시 리젝 사유가 됩니다. `app.json`에 플러그인과 설명 메시지를 반드시 추가해야 합니다.

### 3. (안심) 다중 줄 TextInput 상단 정렬
- 안드로이드의 고질적 버그인 "multiline TextInput의 텍스트가 세로 중앙 정렬되는 현상"은 다행히 `textAlignVertical="top"`이 `audit.tsx`, `capture.tsx`, `components/premium/surfaces.tsx` 등에 일관되게 잘 적용되어 있어 안드로이드에서도 정상적으로 보일 것입니다.

## Recommendation
Claude, 성능 개선(FlatList 도입)과 권한 누락(app.json 수정)은 안드로이드 빌드 이전에 꼭 반영해 주시길 권장합니다!
