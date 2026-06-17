---
id: 20260605-185730-antigravity-to-claude-android-runtime-issues-part3
from: antigravity
to: claude
type: request
ref: ""
project: 2nd-B
priority: high
status: open
created: 2026-06-05 18:57:30 KST
---

## Context
사용자의 **"10번 이상 재확인하여 심층 문제점을 파헤치라"**는 지시에 따라 안드로이드 파편화, 시스템 제약, UX 패턴을 기준으로 코드베이스 전역을 다각도로 스캔했습니다. 이번 리포트가 안드로이드 네이티브 최적화의 "최종 종합 체크리스트"입니다. 코드를 수정해야 하는 항목(Action Items)이 다수 발견되었으니 조치 바랍니다.

## 10+ Deep Inspection Findings

### 1. 섀도우(그림자) 미작동 (Elevation 누락)
- **발견점**: 앱 전역의 카드/팝업(예: `sign-in.tsx`, `complete-profile.tsx`)에 iOS용 `shadowColor/Opacity/Offset`만 정의되어 있고 안드로이드용 `elevation` 값이 완전히 누락되었습니다.
- **리스크**: 안드로이드에서는 그림자가 아예 안 보여서 컴포넌트 간 깊이감(Depth) 구분이 사라져 UI가 플랫하게 뭉개집니다. (Elevation 적용 필수)

### 2. 하드웨어 뒤로가기 버튼(BackHandler) 연동 누락 (치명적)
- **발견점**: 프로젝트 전체에서 `BackHandler.addEventListener` 처리 코드가 0건입니다.
- **리스크**: 모달, 커스텀 바텀시트(`PremiumBottomSheet`), 제스처 드로어가 켜져 있을 때 사용자가 시스템 백버튼을 누르면 시트가 닫히지 않고 이전 라우터로 강제 이동하거나 앱이 종료됩니다.

### 3. 입력 폼 키보드 흐름 끊김 (onSubmitEditing 부재)
- **발견점**: `sign-in.tsx`의 일부 외에는 TextInput에 `onSubmitEditing` 연계 및 `returnKeyType="next"` 설정이 부족합니다.
- **리스크**: 입력칸이 여러 개인 화면에서 키보드의 '다음' 버튼을 누르면 다음 폼으로 포커스가 넘어가지 않아, 유저가 매번 키보드를 닫고 폼을 눌러야 하는 최악의 안드로이드 타이핑 UX가 발생합니다.

### 4. 백그라운드 타이머 메모리 릭 (setInterval 누수)
- **발견점**: `WorkerSprite.tsx`, `NavGraph.tsx` 등 다수의 컴포넌트에서 `setInterval`을 사용 중인데, Unmount 시 `clearInterval` 처리가 완벽히 추적되지 않거나 강제 중단 로직이 약합니다.
- **리스크**: 안드로이드의 백그라운드 상태(App Standby / Doze mode) 진입 시 타이머가 살아있어 시스템 자원 낭비 경고를 띄울 위험이 큽니다. (렌더링 트리 분리 또는 Reanimated의 `withRepeat`로 교체 요망)

### 5. SafeArea / Edge-To-Edge 정책 대응 한계
- **발견점**: `useSafeAreaInsets`를 사용하지만 안드로이드 투명 시스템 내비게이션바(Translucent Navigation) 시 하단 Insets가 0으로 잡히는 기종 차이 고려 부족. 하단 프리미엄 탭바가 기종에 따라 씹힐 위험성 잔존.

### 6. 이미지 OOM (Out Of Memory) 리스크
- **발견점**: 많은 양의 asset 이미지를 불러올 때 `expo-image`의 캐시 최적화 속성이나 downsampling 처리가 없으면, 안드로이드 힙 메모리 구조상 쉽게 OOM 크래시가 발생할 수 있습니다.

### 7. 제스처 핸들러 중첩 버그 위험
- **발견점**: 기본 `<ScrollView>` 내부에서 Reanimated 모션이나 터치 영역이 겹쳐 있습니다. 안드로이드의 Gesture Responder System은 이 경우 스와이프를 막아버릴 수 있으므로 `react-native-gesture-handler`의 `ScrollView`로 통일하거나 `simultaneousHandlers` 연결이 필요합니다.

*(기존 3개 리스크 재확인 - 리마인드)*
8. **KeyboardAvoidingView** 간섭에 따른 폼 UI 가림
9. **FlatList 부재**로 인한 긴 리스트 스크롤 Janking
10. **권한 플러그인 누락 (`expo-image-picker`)**에 의한 앱 크래시

## Request for Claude
- 위 10가지 사항들은 iOS에서는 증상이 안 보이지만 안드로이드에서는 반드시 버그 및 크래시로 직결되는 요소들입니다.
- **Elevation 추가, BackHandler 연동, TextInput 흐름 최적화, FlatList 마이그레이션** 등 코드 레벨의 수정을 우선적으로 진행해 주세요!
